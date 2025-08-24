"""Unit tests for collection service."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError
from pgvector_cli.services.collection_service import CollectionService
from pgvector_cli.models.collection import Collection


class TestCollectionService:
    """Test collection service."""
    
    def test_get_collections(self, test_session):
        """Test getting all active collections."""
        service = CollectionService(test_session)
        
        # Create test collections
        collection1 = Collection(name="test1", dimension=1024, is_active=True)
        collection2 = Collection(name="test2", dimension=1024, is_active=True)
        collection3 = Collection(name="test3", dimension=1024, is_active=False)  # Inactive
        
        test_session.add_all([collection1, collection2, collection3])
        test_session.commit()
        
        collections = service.get_collections()
        
        assert len(collections) == 2  # Only active ones
        names = [c.name for c in collections]
        assert "test1" in names
        assert "test2" in names
        assert "test3" not in names
    
    def test_get_collection_by_name_exists(self, test_session):
        """Test getting collection by name when it exists."""
        service = CollectionService(test_session)
        
        collection = Collection(name="test_collection", dimension=1024, is_active=True)
        test_session.add(collection)
        test_session.commit()
        
        result = service.get_collection_by_name("test_collection")
        
        assert result is not None
        assert result.name == "test_collection"
        assert result.dimension == 1024
    
    def test_get_collection_by_name_not_exists(self, test_session):
        """Test getting collection by name when it doesn't exist."""
        service = CollectionService(test_session)
        
        result = service.get_collection_by_name("nonexistent")
        
        assert result is None
    
    def test_get_collection_by_name_inactive(self, test_session):
        """Test getting inactive collection by name."""
        service = CollectionService(test_session)
        
        collection = Collection(name="inactive_collection", dimension=1024, is_active=False)
        test_session.add(collection)
        test_session.commit()
        
        result = service.get_collection_by_name("inactive_collection")
        
        assert result is None  # Should not return inactive collections
    
    @patch.object(CollectionService, '_create_vector_table')
    def test_create_collection_success(self, mock_create_table, test_session):
        """Test successful collection creation."""
        service = CollectionService(test_session)
        
        collection = service.create_collection(
            name="new_collection",
            dimension=1024,
            description="Test description"
        )
        
        assert collection.name == "new_collection"
        assert collection.dimension == 1024
        assert collection.description == "Test description"
        assert collection.is_active is True
        
        mock_create_table.assert_called_once_with("new_collection", 1024)
    
    def test_create_collection_duplicate_name(self, test_session):
        """Test creating collection with duplicate name."""
        service = CollectionService(test_session)
        
        # Create first collection
        existing = Collection(name="duplicate", dimension=1024, is_active=True)
        test_session.add(existing)
        test_session.commit()
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="Collection with name 'duplicate' already exists"):
            service.create_collection(name="duplicate", dimension=1024)
    
    @patch.object(CollectionService, '_rename_vector_table')
    def test_update_collection_name(self, mock_rename_table, test_session):
        """Test updating collection name."""
        service = CollectionService(test_session)
        
        collection = Collection(name="old_name", dimension=1024, is_active=True)
        test_session.add(collection)
        test_session.commit()
        
        updated = service.update_collection(collection.id, name="new_name")
        
        assert updated.name == "new_name"
        mock_rename_table.assert_called_once_with("old_name", "new_name")
    
    def test_update_collection_description(self, test_session):
        """Test updating collection description."""
        service = CollectionService(test_session)
        
        collection = Collection(name="test", dimension=1024, description="old desc", is_active=True)
        test_session.add(collection)
        test_session.commit()
        
        updated = service.update_collection(collection.id, description="new desc")
        
        assert updated.description == "new desc"
        assert updated.name == "test"  # Name unchanged
    
    def test_update_collection_not_found(self, test_session):
        """Test updating non-existent collection."""
        service = CollectionService(test_session)
        
        result = service.update_collection(999, name="new_name")
        
        assert result is None
    
    @patch.object(CollectionService, '_drop_vector_table')
    def test_delete_collection_success(self, mock_drop_table, test_session):
        """Test successful collection deletion."""
        service = CollectionService(test_session)
        
        collection = Collection(name="to_delete", dimension=1024, is_active=True)
        test_session.add(collection)
        test_session.commit()
        
        result = service.delete_collection(collection.id)
        
        assert result is True
        
        # Check soft delete
        test_session.refresh(collection)
        assert collection.is_active is False
        assert collection.deleted_at is not None
        
        mock_drop_table.assert_called_once_with("to_delete")
    
    def test_delete_collection_not_found(self, test_session):
        """Test deleting non-existent collection."""
        service = CollectionService(test_session)
        
        result = service.delete_collection(999)
        
        assert result is False
    
    def test_safe_table_name_generation(self, test_session):
        """Test safe table name generation."""
        service = CollectionService(test_session)
        
        test_cases = [
            ("simple_name", "vectors_simple_name"),
            ("Name With Spaces", "vectors_name_with_spaces"),
            ("name-with-hyphens", "vectors_name_with_hyphens"),
            ("Name@#$%Special", "vectors_name____special"),
            ("123numeric", "vectors__123numeric"),  # Starts with underscore
        ]
        
        for input_name, expected in test_cases:
            result = service._safe_table_name(input_name)
            assert result == expected
    
    def test_rebuild_collection_index_success(self, test_session):
        """Test successful index rebuild."""
        service = CollectionService(test_session)
        
        # Note: This test will fail with SQLite since it doesn't support vector indexes
        # In a real PostgreSQL environment, this would work
        collection = Collection(name="test_index", dimension=1024, is_active=True)
        test_session.add(collection)
        test_session.commit()
        
        # Mock the SQL execution to avoid SQLite limitations
        with patch.object(test_session, 'execute') as mock_execute:
            result = service.rebuild_collection_index(collection.id)
            
            assert result is True
            assert mock_execute.call_count == 2  # DROP + CREATE INDEX
    
    def test_rebuild_collection_index_not_found(self, test_session):
        """Test index rebuild for non-existent collection."""
        service = CollectionService(test_session)
        
        result = service.rebuild_collection_index(999)
        
        assert result is False
    
    def test_get_collection_index_info(self, test_session):
        """Test getting collection index information."""
        service = CollectionService(test_session)
        
        collection = Collection(name="test_info", dimension=1024, is_active=True)
        test_session.add(collection)
        test_session.commit()
        
        # Mock the query result
        with patch.object(test_session, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.fetchall.return_value = [
                ("vectors_test_info_vector_hnsw_idx", "CREATE INDEX ...")
            ]
            mock_execute.return_value = mock_result
            
            result = service.get_collection_index_info(collection.id)
            
            assert result["collection_name"] == "test_info"
            assert result["table_name"] == "vectors_test_info"
            assert len(result["indexes"]) == 1
            assert result["indexes"][0]["name"] == "vectors_test_info_vector_hnsw_idx"