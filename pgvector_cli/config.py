"""Configuration management for pgvector CLI."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings."""
    
    def __init__(self):
        self.database_url: str = os.getenv(
            "DATABASE_URL", 
            "postgresql://lihongwen@localhost:5432/postgres"
        )
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        
        # Embedding service configuration
        self.dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
        self.dashscope_base_url: str = os.getenv(
            "DASHSCOPE_BASE_URL", 
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

def get_settings() -> Settings:
    """Get application settings."""
    return Settings()