"""Database configuration and session management for pgvector CLI."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pgvector.sqlalchemy import Vector

from .config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_session() -> Session:
    """Get database session."""
    return SessionLocal()

def init_database():
    """Initialize database tables."""
    from .models import Collection, VectorRecord
    Base.metadata.create_all(bind=engine)