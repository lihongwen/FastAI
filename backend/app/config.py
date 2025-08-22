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
    
    # 阿里云百炼API配置
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    dashscope_base_url: str = os.getenv(
        "DASHSCOPE_BASE_URL", 
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    class Config:
        env_file = ".env"

settings = Settings()