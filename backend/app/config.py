import os
from pydantic_settings import BaseSettings
from typing import List
from pydantic import Field

class Settings(BaseSettings):
    model_config = {
        "env_file": ".env", 
        "env_prefix": ""
    }
    
    # Database
    database_url: str = Field(default="postgresql://user:password@localhost:5432/docanalyzer", env="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Gemini API
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    
    # File upload
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    allowed_extensions: List[str] = [".pdf", ".txt"]
    upload_dir: str = "uploads"
    
    # Rate limiting
    rate_limit_requests: int = 10
    rate_limit_window: int = 60  # seconds
    
    # CORS - Store as string, convert to list when needed
    allowed_origins_str: str = Field(default="http://localhost:3000,http://127.0.0.1:3000", env="ALLOWED_ORIGINS")
    
    # Security
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    @property
    def allowed_origins(self) -> List[str]:
        """Convert comma-separated origins string to list"""
        return [origin.strip() for origin in self.allowed_origins_str.split(",") if origin.strip()]

settings = Settings() 