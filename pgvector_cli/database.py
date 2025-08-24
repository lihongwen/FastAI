"""Database configuration and session management for pgvector CLI."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings

settings = get_settings()

# Create database engine with connection pool configuration
engine = create_engine(
    settings.database_url,
    # Connection pool settings for better reliability
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Validates connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=settings.debug  # Log SQL queries in debug mode
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_session() -> Session:
    """Get database session (legacy method - prefer get_db_session context manager)."""
    return SessionLocal()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_database():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
