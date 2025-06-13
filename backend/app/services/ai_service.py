import google.generativeai as genai
import time
import asyncio
import hashlib
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.config import settings
import logging
import redis
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        if not settings.gemini_api_key:
            logger.warning("Gemini API key not provided")
            self.model = None
        else:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        
        # Redis for caching
        try:
            self.redis_client = redis.from_url(settings.redis_url)
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, prompt: str, document_text: str) -> str:
        """Generate cache key for prompt + document combination"""
        content = f"{prompt}:{document_text}"
        return f"gemini_cache:{hashlib.md5(content.encode()).hexdigest()}"
    
    async def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response from Redis"""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    async def _cache_response(self, cache_key: str, response_data: Dict[str, Any], ttl: int = 3600):
        """Cache response in Redis"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(response_data)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _call_gemini_api(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini API with retry logic"""
        if not self.model:
            raise HTTPException(
                status_code=503,
                detail="Gemini API not configured. Please set GEMINI_API_KEY environment variable."
            )
        
        start_time = time.time()
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            if not response or not response.text:
                raise HTTPException(
                    status_code=500,
                    detail="Empty response from Gemini API"
                )
            
            return {
                "response": response.text,
                "execution_time_ms": execution_time,
                "model": "gemini-pro",
                "tokens_used": len(prompt.split()) + len(response.text.split()),  # Rough estimate
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                raise HTTPException(
                    status_code=429,
                    detail="API rate limit exceeded. Please try again later."
                )
            elif "api key" in str(e).lower():
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"AI service error: {str(e)}"
                )
    
    async def analyze_document(
        self, 
        prompt: str, 
        document_text: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Analyze document with given prompt"""
        
        # Generate full prompt
        full_prompt = f"{prompt}\n\nDocument:\n{document_text}"
        
        # Check cache first
        if use_cache:
            cache_key = self._generate_cache_key(prompt, document_text)
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                logger.info("Returning cached response")
                return cached_response
        
        # Call Gemini API
        response_data = await self._call_gemini_api(full_prompt)
        
        # Cache the response
        if use_cache:
            await self._cache_response(cache_key, response_data)
        
        return response_data
    
    async def chunk_document(self, text: str, max_tokens: int = 4000) -> list[str]:
        """Chunk document for large texts that exceed token limits"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            # Rough token estimation (1 token ≈ 0.75 words)
            word_tokens = len(word) / 0.75
            
            if current_length + word_tokens > max_tokens and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_tokens
            else:
                current_chunk.append(word)
                current_length += word_tokens
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    async def analyze_document_chunked(
        self, 
        prompt: str, 
        document_text: str
    ) -> Dict[str, Any]:
        """Analyze large documents by chunking"""
        
        # Check if document needs chunking
        estimated_tokens = len(document_text.split()) * 1.33  # Rough estimation
        
        if estimated_tokens <= 4000:
            return await self.analyze_document(prompt, document_text)
        
        # Chunk the document
        chunks = await self.chunk_document(document_text)
        
        # Analyze each chunk
        chunk_results = []
        total_execution_time = 0
        
        for i, chunk in enumerate(chunks):
            chunk_prompt = f"{prompt}\n\nThis is part {i+1} of {len(chunks)} of the document. Please analyze this section:\n\n{chunk}"
            result = await self.analyze_document(chunk_prompt, "", use_cache=False)
            chunk_results.append(result["response"])
            total_execution_time += result["execution_time_ms"]
        
        # Combine results
        combined_prompt = f"Please synthesize the following {len(chunks)} analysis results into a cohesive summary:\n\n"
        for i, result in enumerate(chunk_results):
            combined_prompt += f"Part {i+1}: {result}\n\n"
        
        final_result = await self._call_gemini_api(combined_prompt)
        final_result["execution_time_ms"] += total_execution_time
        final_result["chunks_processed"] = len(chunks)
        
        return final_result
    
    def get_default_prompts(self) -> list[Dict[str, Any]]:
        """Get default prompt templates"""
        return [
            {
                "name": "Executive Summary",
                "category": "summary",
                "description": "Generate a concise executive summary",
                "prompt_text": "Provide a concise executive summary of the following document in 3-5 bullet points: {document_content}",
                "variables": [{"name": "document_content", "required": True}],
                "example_output": "• Key finding 1\n• Key finding 2\n• Key finding 3"
            },
            {
                "name": "Key Insights",
                "category": "analysis",
                "description": "Extract the most important insights",
                "prompt_text": "Analyze this document and extract the 5 most important insights: {document_content}",
                "variables": [{"name": "document_content", "required": True}],
                "example_output": "1. Insight 1\n2. Insight 2\n3. Insight 3\n4. Insight 4\n5. Insight 5"
            },
            {
                "name": "Action Items",
                "category": "extraction",
                "description": "List all action items and tasks",
                "prompt_text": "List all action items, tasks, or next steps mentioned in this document: {document_content}",
                "variables": [{"name": "document_content", "required": True}],
                "example_output": "• Action item 1\n• Action item 2\n• Action item 3"
            },
            {
                "name": "Financial Figures",
                "category": "extraction",
                "description": "Extract financial data and numbers",
                "prompt_text": "Extract all financial figures, amounts, and percentages from this document: {document_content}",
                "variables": [{"name": "document_content", "required": True}],
                "example_output": "$1,000,000 - Revenue\n25% - Growth rate\n$500,000 - Profit"
            },
            {
                "name": "Sentiment Analysis",
                "category": "analysis",
                "description": "Analyze the sentiment and tone",
                "prompt_text": "Analyze the sentiment and overall tone of this document. Is it positive, negative, or neutral? Explain your reasoning: {document_content}",
                "variables": [{"name": "document_content", "required": True}],
                "example_output": "Sentiment: Positive\nReasoning: The document contains optimistic language..."
            }
        ]

ai_service = AIService() 