from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import List
import uuid
import time
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import get_db
from app.models import Document, PromptTemplate, AIAnalysis
from app.schemas import (
    PromptTemplate as PromptTemplateSchema,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    AIAnalysis as AIAnalysisSchema,
    AnalyzeDocumentRequest,
    AnalyzeDocumentResponse
)
from app.services.ai_service import ai_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@router.get("/prompt-templates", response_model=List[PromptTemplateSchema])
def get_prompt_templates(
    category: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of prompt templates"""
    
    stmt = select(PromptTemplate).where(PromptTemplate.is_public == True)
    
    if category:
        stmt = stmt.where(PromptTemplate.category == category)
    
    stmt = stmt.offset(skip).limit(limit).order_by(PromptTemplate.created_at.desc())
    
    result = db.execute(stmt)
    templates = result.scalars().all()
    
    return templates

@router.post("/prompt-templates", response_model=PromptTemplateSchema)
def create_prompt_template(
    template: PromptTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new prompt template"""
    
    db_template = PromptTemplate(
        name=template.name,
        description=template.description,
        prompt_text=template.prompt_text,
        category=template.category,
        variables=template.variables,
        example_output=template.example_output,
        is_public=template.is_public
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template

@router.get("/prompt-templates/{template_id}", response_model=PromptTemplateSchema)
def get_prompt_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get specific prompt template"""
    
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    stmt = select(PromptTemplate).where(PromptTemplate.id == template_uuid)
    result = db.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    return template

@router.put("/prompt-templates/{template_id}", response_model=PromptTemplateSchema)
def update_prompt_template(
    template_id: str,
    template_update: PromptTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a prompt template"""
    
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    stmt = select(PromptTemplate).where(PromptTemplate.id == template_uuid)
    result = db.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    # Update fields that are provided
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return template

@router.delete("/prompt-templates/{template_id}")
def delete_prompt_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Delete a prompt template"""
    
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    stmt = select(PromptTemplate).where(PromptTemplate.id == template_uuid)
    result = db.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    db.delete(template)
    db.commit()
    
    return {"message": "Prompt template deleted successfully"}

@router.post("/analyze", response_model=AnalyzeDocumentResponse)
# @limiter.limit(f"{settings.rate_limit_requests}/minute")  # Temporarily disabled
def analyze_document(
    request_data: AnalyzeDocumentRequest,
    db: Session = Depends(get_db)
):
    """Analyze a document with given prompt"""
    
    # Get document
    stmt = select(Document).where(Document.id == request_data.document_id)
    result = db.execute(stmt)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != "ready":
        raise HTTPException(
            status_code=400, 
            detail=f"Document is not ready for analysis. Current status: {document.status}"
        )
    
    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="Document has no extracted text")
    
    # Get prompt template if provided
    prompt_template = None
    if request_data.prompt_template_id:
        stmt = select(PromptTemplate).where(PromptTemplate.id == request_data.prompt_template_id)
        result = db.execute(stmt)
        prompt_template = result.scalar_one_or_none()
        
        if not prompt_template:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        # Update usage count
        prompt_template.usage_count += 1
        db.commit()
    
    # Create AI analysis record
    analysis = AIAnalysis(
        document_id=request_data.document_id,
        prompt_template_id=request_data.prompt_template_id,
        final_prompt=request_data.prompt
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    try:
        # For now, return a simple response since AI service needs to be implemented
        # This will allow testing the analysis endpoint
        
        start_time = time.time()
        execution_time = int((time.time() - start_time) * 1000)
        
        # Simple mock response for testing
        mock_response = f"Analysis of document '{document.filename}' with prompt: '{request_data.prompt}'\n\nDocument content preview: {document.extracted_text[:200]}..."
        
        # Update analysis record with results
        analysis.gemini_response = mock_response
        analysis.execution_time_ms = execution_time
        analysis.response_metadata = {
            "model": "mock-model",
            "tokens_used": len(document.extracted_text.split()),
            "chunks_processed": 1
        }
        
        db.commit()
        
        return AnalyzeDocumentResponse(
            analysis_id=analysis.id,
            response=mock_response,
            execution_time_ms=execution_time,
            tokens_used=len(document.extracted_text.split())
        )
        
    except Exception as e:
        # Update analysis record with error
        analysis.error_message = str(e)
        db.commit()
        
        logger.error(f"Analysis failed for document {request_data.document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/analyses", response_model=List[AIAnalysisSchema])
def get_analyses(
    document_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of AI analyses"""
    
    stmt = select(AIAnalysis)
    
    if document_id:
        try:
            doc_uuid = uuid.UUID(document_id)
            stmt = stmt.where(AIAnalysis.document_id == doc_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document ID format")
    
    stmt = stmt.offset(skip).limit(limit).order_by(AIAnalysis.created_at.desc())
    
    result = db.execute(stmt)
    analyses = result.scalars().all()
    
    return analyses

@router.get("/analyses/{analysis_id}", response_model=AIAnalysisSchema)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """Get specific AI analysis"""
    
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format")
    
    stmt = select(AIAnalysis).where(AIAnalysis.id == analysis_uuid)
    result = db.execute(stmt)
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis

@router.post("/init-default-templates")
def initialize_default_templates(db: Session = Depends(get_db)):
    """Initialize default prompt templates"""
    
    # Check if templates already exist
    stmt = select(PromptTemplate).limit(1)
    result = db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        return {"message": "Default templates already exist"}
    
    # Create default templates
    default_templates = ai_service.get_default_prompts()
    
    for template_data in default_templates:
        template = PromptTemplate(
            name=template_data["name"],
            description=template_data["description"],
            prompt_text=template_data["prompt_text"],
            category=template_data["category"],
            variables=template_data["variables"],
            example_output=template_data["example_output"],
            is_public=True
        )
        db.add(template)
    
    db.commit()
    
    return {"message": f"Created {len(default_templates)} default templates"}

# Rate limit exception handler is already registered in main.py 