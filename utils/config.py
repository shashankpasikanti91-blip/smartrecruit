"""
Configuration Management
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration"""
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Google Drive
    GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "")
    
    # n8n
    N8N_BASE_URL: str = os.getenv("N8N_BASE_URL", "http://localhost:5678")
    N8N_API_KEY: str = os.getenv("N8N_API_KEY", "")
    N8N_SCREENING_WORKFLOW_ID: str = os.getenv("N8N_SCREENING_WORKFLOW_ID", "")
    N8N_MESSAGING_WORKFLOW_ID: str = os.getenv("N8N_MESSAGING_WORKFLOW_ID", "")
    N8N_JD_PROCESSING_WORKFLOW_ID: str = os.getenv("N8N_JD_PROCESSING_WORKFLOW_ID", "")
    
    # Control Panel
    CONTROL_PANEL_PATH: str = os.getenv("CONTROL_PANEL_PATH", "🎯 Recruitment Control Panel copy (1).json")
    FULL_RECRUITMENT_PATH: str = os.getenv("FULL_RECRUITMENT_PATH", "Full Recruitment.json")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "recruitment_ai.log")
    
    # Database
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    def validate(self) -> bool:
        """Validate required configuration"""
        required = [
            "OPENAI_API_KEY",
            "SUPABASE_URL",
            "SUPABASE_KEY"
        ]
        
        missing = [key for key in required if not getattr(self, key)]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if not key.startswith("_")
        }


# Global config instance
config = Config()
