"""Configuration management for pgvector CLI."""

import os

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

        # DashScope embedding service configuration (阿里云)
        self.dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
        self.dashscope_base_url: str = os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # Cleanup configuration
        self.soft_delete_retention_days: int = int(os.getenv("SOFT_DELETE_RETENTION_DAYS", "30"))

def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
