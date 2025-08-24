"""Unit tests for validators module."""

import pytest
from pgvector_cli.utils.validators import (
    validate_collection_name,
    validate_dimension,
    validate_metadata_format,
    validate_search_query,
    validate_limit
)


class TestValidateCollectionName:
    """Test collection name validation."""
    
    def test_valid_collection_names(self):
        """Test valid collection names."""
        valid_names = [
            "test_collection",
            "MyCollection",
            "collection-123",
            "test collection",
            "a" * 50,  # 50 chars
        ]
        
        for name in valid_names:
            assert validate_collection_name(name) is True
    
    def test_invalid_collection_names(self):
        """Test invalid collection names."""
        with pytest.raises(ValueError, match="Collection name cannot be empty"):
            validate_collection_name("")
        
        with pytest.raises(ValueError, match="must be at least 2 characters"):
            validate_collection_name("a")
        
        with pytest.raises(ValueError, match="must be 50 characters or less"):
            validate_collection_name("a" * 51)
        
        with pytest.raises(ValueError, match="cannot start or end with spaces"):
            validate_collection_name(" test")
        
        with pytest.raises(ValueError, match="cannot start or end with spaces"):
            validate_collection_name("test ")
        
        with pytest.raises(ValueError, match="can only contain"):
            validate_collection_name("test@collection")


class TestValidateDimension:
    """Test dimension validation."""
    
    def test_valid_dimensions(self):
        """Test valid dimensions."""
        valid_dims = [1, 128, 256, 384, 512, 768, 1024, 1536, 2048, 3072, 4096]
        
        for dim in valid_dims:
            assert validate_dimension(dim) is True
    
    def test_invalid_dimensions(self):
        """Test invalid dimensions."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            validate_dimension(0)
        
        with pytest.raises(ValueError, match="must be a positive integer"):
            validate_dimension(-1)
        
        with pytest.raises(ValueError, match="cannot exceed 4096"):
            validate_dimension(5000)


class TestValidateMetadataFormat:
    """Test metadata format validation."""
    
    def test_valid_metadata_formats(self):
        """Test valid metadata formats."""
        test_cases = [
            ("key=value", ("key", "value")),
            ("name=John Doe", ("name", "John Doe")),
            ("count=123", ("count", 123)),
            ("price=19.99", ("price", 19.99)),
            ("active=true", ("active", True)),
            ("config={\"a\": 1}", ("config", {"a": 1})),
        ]
        
        for metadata_str, expected in test_cases:
            result = validate_metadata_format(metadata_str)
            assert result == expected
    
    def test_invalid_metadata_formats(self):
        """Test invalid metadata formats."""
        with pytest.raises(ValueError, match="Invalid metadata format"):
            validate_metadata_format("no_equals")
        
        with pytest.raises(ValueError, match="Metadata key cannot be empty"):
            validate_metadata_format("=value")


class TestValidateSearchQuery:
    """Test search query validation."""
    
    def test_valid_search_queries(self):
        """Test valid search queries."""
        valid_queries = [
            "test",
            "search query",
            "a" * 1000,  # 1000 chars
        ]
        
        for query in valid_queries:
            assert validate_search_query(query) is True
    
    def test_invalid_search_queries(self):
        """Test invalid search queries."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_search_query("")
        
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_search_query("   ")
        
        with pytest.raises(ValueError, match="cannot exceed 1000 characters"):
            validate_search_query("a" * 1001)


class TestValidateLimit:
    """Test limit validation."""
    
    def test_valid_limits(self):
        """Test valid limits."""
        valid_limits = [1, 10, 50, 100]
        
        for limit in valid_limits:
            assert validate_limit(limit) is True
    
    def test_invalid_limits(self):
        """Test invalid limits."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            validate_limit(0)
        
        with pytest.raises(ValueError, match="must be a positive integer"):
            validate_limit(-1)
        
        with pytest.raises(ValueError, match="cannot exceed 100"):
            validate_limit(200)
        
        # Test custom max limit
        assert validate_limit(150, max_limit=200) is True
        
        with pytest.raises(ValueError, match="cannot exceed 200"):
            validate_limit(250, max_limit=200)