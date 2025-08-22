from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://lihongwen@localhost:5432/postgres"
    )
    app_name: str = "pgvector Collection Manager"
    debug: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()