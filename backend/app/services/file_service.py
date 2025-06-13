import os
import aiofiles
import PyPDF2
import pdfplumber
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.config import settings
import uuid
import asyncio
from pathlib import Path

class FileService:
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def validate_file(self, file: UploadFile) -> bool:
        """Validate file type and size"""
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
            )
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size // (1024*1024)}MB"
            )
        
        return True
    
    async def save_file(self, file: UploadFile, file_id: uuid.UUID) -> str:
        """Save uploaded file to disk"""
        file_ext = Path(file.filename).suffix.lower()
        file_path = self.upload_dir / f"{file_id}{file_ext}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return str(file_path)
    
    def extract_text(self, file_path: str) -> Optional[str]:
        """Extract text from PDF or TXT file (sync version)"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.txt':
                return self._extract_text_from_txt_sync(file_path)
            elif file_ext == '.pdf':
                return self._extract_text_from_pdf_sync(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
                
        except Exception as e:
            raise Exception(f"Failed to extract text: {str(e)}")
    
    def _extract_text_from_txt_sync(self, file_path: str) -> str:
        """Extract text from TXT file (sync version)"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    
    def _extract_text_from_pdf_sync(self, file_path: str) -> str:
        """Extract text from PDF file using pdfplumber (sync version)"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            # Fallback to PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                return text
            except Exception as e2:
                raise Exception(f"Failed with both pdfplumber and PyPDF2: {str(e)}, {str(e2)}")
    
    def detect_language(self, text: str) -> str:
        """Simple language detection (sync version)"""
        # Basic language detection - can be enhanced
        if not text:
            return "unknown"
        
        # Simple heuristic - can be replaced with proper language detection
        english_words = ["the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        words = text.lower().split()[:100]  # Check first 100 words
        
        english_count = sum(1 for word in words if word in english_words)
        if english_count / len(words) > 0.1:  # If more than 10% are common English words
            return "en"
        
        return "unknown"
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from disk (sync version)"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    # Keep async versions for compatibility
    async def extract_text_from_file(self, file_path: str) -> Optional[str]:
        """Extract text from PDF or TXT file"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.txt':
                return await self._extract_text_from_txt(file_path)
            elif file_ext == '.pdf':
                return await self._extract_text_from_pdf(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")
    
    async def _extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return content
    
    async def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file using pdfplumber"""
        def extract_pdf_sync():
            text = ""
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text
            except Exception as e:
                # Fallback to PyPDF2
                try:
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        text = ""
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                    return text
                except Exception as e2:
                    raise Exception(f"Failed with both pdfplumber and PyPDF2: {str(e)}, {str(e2)}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, extract_pdf_sync)
        return text
    
    async def detect_language_async(self, text: str) -> str:
        """Simple language detection (async version)"""
        # Basic language detection - can be enhanced
        if not text:
            return "unknown"
        
        # Simple heuristic - can be replaced with proper language detection
        english_words = ["the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        words = text.lower().split()[:100]  # Check first 100 words
        
        english_count = sum(1 for word in words if word in english_words)
        if english_count / len(words) > 0.1:  # If more than 10% are common English words
            return "en"
        
        return "unknown"
    
    async def delete_file_async(self, file_path: str) -> bool:
        """Delete file from disk (async version)"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

file_service = FileService() 