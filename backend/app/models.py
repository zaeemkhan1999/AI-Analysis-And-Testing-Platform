from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default='uploaded')
    current_stage = Column(String(500))
    progress = Column(Integer, default=0)
    extracted_text = Column(Text)
    text_length = Column(Integer)
    language = Column(String(10))
    
    # Relationship with AI analyses
    analyses = relationship("AIAnalysis", back_populates="document")

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    prompt_text = Column(Text, nullable=False)
    category = Column(String(50))  # 'summary', 'analysis', 'extraction', 'custom'
    variables = Column(JSON)  # [{name: 'document_content', required: true}]
    example_output = Column(Text)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_public = Column(Boolean, default=True)
    
    # Relationship with AI analyses
    analyses = relationship("AIAnalysis", back_populates="prompt_template")

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    prompt_template_id = Column(UUID(as_uuid=True), ForeignKey("prompt_templates.id"))
    final_prompt = Column(Text, nullable=False)  # Actual prompt sent to Gemini
    gemini_response = Column(Text)
    response_metadata = Column(JSON)  # tokens used, model, temperature
    execution_time_ms = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="analyses")
    prompt_template = relationship("PromptTemplate", back_populates="analyses") 