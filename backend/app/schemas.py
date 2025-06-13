from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Document schemas
class DocumentBase(BaseModel):
    filename: str
    file_size: int

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    status: Optional[str] = None
    current_stage: Optional[str] = None
    progress: Optional[int] = None
    extracted_text: Optional[str] = None
    text_length: Optional[int] = None
    language: Optional[str] = None

class Document(DocumentBase):
    id: uuid.UUID
    upload_time: datetime
    status: str
    current_stage: Optional[str] = None
    progress: int
    extracted_text: Optional[str] = None
    text_length: Optional[int] = None
    language: Optional[str] = None
    
    class Config:
        from_attributes = True

# Prompt Template schemas
class PromptTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_text: str
    category: Optional[str] = None
    variables: Optional[List[Dict[str, Any]]] = None
    example_output: Optional[str] = None
    is_public: bool = True

class PromptTemplateCreate(PromptTemplateBase):
    pass

class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prompt_text: Optional[str] = None
    category: Optional[str] = None
    variables: Optional[List[Dict[str, Any]]] = None
    example_output: Optional[str] = None
    is_public: Optional[bool] = None

class PromptTemplate(PromptTemplateBase):
    id: uuid.UUID
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# AI Analysis schemas
class AIAnalysisBase(BaseModel):
    document_id: uuid.UUID
    prompt_template_id: Optional[uuid.UUID] = None
    final_prompt: str

class AIAnalysisCreate(AIAnalysisBase):
    pass

class AIAnalysisUpdate(BaseModel):
    gemini_response: Optional[str] = None
    response_metadata: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None

class AIAnalysis(AIAnalysisBase):
    id: uuid.UUID
    gemini_response: Optional[str] = None
    response_metadata: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# File upload schemas
class FileUploadResponse(BaseModel):
    file_id: uuid.UUID
    filename: str
    file_size: int
    status: str

# Progress update schemas
class ProgressUpdate(BaseModel):
    file_id: uuid.UUID
    stage: str
    progress: int
    status: str

# AI Analysis request schemas
class AnalyzeDocumentRequest(BaseModel):
    document_id: uuid.UUID
    prompt: str
    prompt_template_id: Optional[uuid.UUID] = None

class AnalyzeDocumentResponse(BaseModel):
    analysis_id: uuid.UUID
    response: str
    execution_time_ms: int
    tokens_used: Optional[int] = None 