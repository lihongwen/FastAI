"""Pytest configuration and fixtures."""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from pgvector_cli.database import Base, get_db_session
from pgvector_cli.config import Settings


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine using SQLite in-memory."""
    # Use SQLite for testing (faster and doesn't require PostgreSQL setup)
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Settings(
        database_url="sqlite:///:memory:",
        debug=True,
        dashscope_api_key="test_api_key",
        dashscope_base_url="https://test.example.com",
        soft_delete_retention_days=30
    )


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    mock = Mock()
    mock.embed_text.return_value = [0.1] * 1024  # Mock 1024-dim vector
    mock.embed_texts.return_value = [[0.1] * 1024, [0.2] * 1024]  # Mock batch embeddings
    mock.check_api_status.return_value = True
    return mock


@pytest.fixture
def sample_collection_data():
    """Sample collection data for testing."""
    return {
        "name": "test_collection",
        "description": "Test collection for unit tests",
        "dimension": 1024
    }


@pytest.fixture
def sample_vector_data():
    """Sample vector data for testing."""
    return {
        "content": "This is a test document",
        "extra_metadata": {"source": "test", "type": "document"}
    }


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file for batch testing."""
    data = [
        {"content": "First test document", "metadata": {"id": 1}},
        {"content": "Second test document", "metadata": {"id": 2}},
        {"content": "Third test document", "metadata": {"id": 3}}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        import json
        json.dump(data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass