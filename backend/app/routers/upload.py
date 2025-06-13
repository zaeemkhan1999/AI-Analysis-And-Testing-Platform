from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import List
import uuid
import asyncio
import logging
from pathlib import Path

from app.database import get_db
from app.models import Document
from app.schemas import Document as DocumentSchema, FileUploadResponse, ProgressUpdate
from app.services.file_service import file_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Store SSE connections
sse_connections = {}

def process_document_pipeline(file_id: uuid.UUID, file_path: str, db: Session):
    """Background task to process uploaded document"""
    try:
        logger.info(f"Starting document processing for {file_id}")
        
        # Stage 1: Text extraction
        update_progress(file_id, "Extracting text from document", 20, "processing", db)
        
        # Extract text based on file type
        extracted_text = file_service.extract_text(file_path)
        
        if not extracted_text:
            raise Exception("Could not extract text from document")
        
        # Stage 2: Text preparation
        update_progress(file_id, "Preparing for analysis", 60, "processing", db)
        
        # Detect language
        language = file_service.detect_language(extracted_text)
        text_length = len(extracted_text) if extracted_text else 0
        
        # Stage 3: Ready for AI analysis
        update_progress(file_id, "Ready for AI analysis", 100, "ready", db)
        
        # Update document with extracted text
        stmt = update(Document).where(Document.id == file_id).values(
            extracted_text=extracted_text,
            text_length=text_length,
            language=language,
            status="ready",
            current_stage="Ready for AI analysis",
            progress=100
        )
        db.execute(stmt)
        db.commit()
        
        logger.info(f"Document {file_id} processed successfully")
        
    except Exception as e:
        error_msg = str(e)
        # Truncate error message if too long
        if len(error_msg) > 400:
            error_msg = error_msg[:400] + "..."
        
        logger.error(f"Error processing document {file_id}: {error_msg}")
        update_progress(file_id, f"Error: {error_msg}", 0, "error", db)
        
        # Update document with error status
        stmt = update(Document).where(Document.id == file_id).values(
            status="error",
            current_stage=f"Error: {error_msg}"
        )
        db.execute(stmt)
        db.commit()

def update_progress(file_id: uuid.UUID, stage: str, progress: int, status: str, db: Session):
    """Update document progress and notify SSE clients"""
    # Update database
    stmt = update(Document).where(Document.id == file_id).values(
        current_stage=stage,
        progress=progress,
        status=status
    )
    db.execute(stmt)
    db.commit()
    
    # Notify SSE clients
    if str(file_id) in sse_connections:
        progress_update = ProgressUpdate(
            file_id=file_id,
            stage=stage,
            progress=progress,
            status=status
        )
        
        try:
            sse_connections[str(file_id)].put_nowait(f"data: {progress_update.json()}\n\n")
        except:
            # Remove dead connection
            del sse_connections[str(file_id)]

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a file and start processing pipeline"""
    
    # Validate file
    await file_service.validate_file(file)
    
    # Create document record
    file_id = uuid.uuid4()
    file_size = file.file.seek(0, 2)  # Get file size
    file.file.seek(0)  # Reset file pointer
    
    document = Document(
        id=file_id,
        filename=file.filename,
        file_size=file_size,
        status="uploaded",
        current_stage="File uploaded",
        progress=0
    )
    
    db.add(document)
    db.commit()
    
    # Save file to disk
    file_path = await file_service.save_file(file, file_id)
    
    # Start background processing
    background_tasks.add_task(process_document_pipeline, file_id, file_path, db)
    
    return FileUploadResponse(
        file_id=file_id,
        filename=file.filename,
        file_size=file_size,
        status="uploaded"
    )

@router.get("/progress/{file_id}")
async def stream_progress(file_id: str):
    """Server-Sent Events endpoint for real-time progress updates"""
    
    async def event_generator():
        queue = asyncio.Queue()
        sse_connections[file_id] = queue
        
        try:
            while True:
                # Wait for progress update
                data = await queue.get()
                yield data
                
                # Check if processing is complete
                if "ready" in data or "error" in data:
                    break
                    
        except asyncio.CancelledError:
            pass
        finally:
            # Clean up connection
            if file_id in sse_connections:
                del sse_connections[file_id]
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/documents", response_model=List[DocumentSchema])
def get_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of uploaded documents"""
    
    stmt = select(Document).offset(skip).limit(limit).order_by(Document.upload_time.desc())
    result = db.execute(stmt)
    documents = result.scalars().all()
    
    return documents

@router.get("/documents/{document_id}", response_model=DocumentSchema)
def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get specific document details"""
    
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    stmt = select(Document).where(Document.id == doc_uuid)
    result = db.execute(stmt)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document

@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete a document and its file"""
    
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    stmt = select(Document).where(Document.id == doc_uuid)
    result = db.execute(stmt)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from disk
    file_ext = Path(document.filename).suffix.lower()
    file_path = settings.upload_dir / f"{document_id}{file_ext}"
    file_service.delete_file(str(file_path))
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"} 