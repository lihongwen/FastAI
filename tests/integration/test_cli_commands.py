"""Integration tests for CLI commands."""

import pytest
import json
import tempfile
import os
from click.testing import CliRunner
from unittest.mock import patch, Mock

from pgvector_cli.main import cli


@pytest.mark.integration
class TestCLICommands:
    """Test CLI command integration."""
    
    def test_status_command_success(self):
        """Test status command with mocked database."""
        runner = CliRunner()
        
        # Mock database connection and pgvector check
        with patch('pgvector_cli.main.get_db_session') as mock_session:
            mock_ctx = Mock()
            mock_ctx.__enter__ = Mock(return_value=mock_ctx)
            mock_ctx.__exit__ = Mock(return_value=None)
            mock_ctx.execute.side_effect = [
                None,  # SELECT 1
                Mock(fetchone=Mock(return_value=("vector",)))  # pgvector check
            ]
            mock_session.return_value = mock_ctx
            
            result = runner.invoke(cli, ['status'])
            
            assert result.exit_code == 0
            assert "✓ Connected" in result.output
            assert "✓ Installed" in result.output
    
    def test_status_command_no_pgvector(self):
        """Test status command when pgvector is not installed."""
        runner = CliRunner()
        
        with patch('pgvector_cli.main.get_db_session') as mock_session:
            mock_ctx = Mock()
            mock_ctx.__enter__ = Mock(return_value=mock_ctx)
            mock_ctx.__exit__ = Mock(return_value=None)
            mock_ctx.execute.side_effect = [
                None,  # SELECT 1
                Mock(fetchone=Mock(return_value=None))  # No pgvector
            ]
            mock_session.return_value = mock_ctx
            
            result = runner.invoke(cli, ['status'])
            
            assert result.exit_code == 1
            assert "✗ Not installed" in result.output
            assert "Warning: pgvector extension is not installed" in result.output
    
    def test_create_collection_success(self):
        """Test successful collection creation."""
        runner = CliRunner()
        
        mock_collection = Mock()
        mock_collection.id = 1
        mock_collection.name = "test_collection"
        mock_collection.dimension = 1024
        mock_collection.description = "Test description"
        
        with patch('pgvector_cli.main.get_db_session') as mock_session, \
             patch('pgvector_cli.main.CollectionService') as mock_service_class, \
             patch('pgvector_cli.main.auto_cleanup'):
            
            mock_ctx = Mock()
            mock_ctx.__enter__ = Mock(return_value=mock_ctx)
            mock_ctx.__exit__ = Mock(return_value=None)
            mock_session.return_value = mock_ctx
            
            mock_service = Mock()
            mock_service.create_collection.return_value = mock_collection
            mock_service_class.return_value = mock_service
            
            result = runner.invoke(cli, [
                'create-collection', 'test_collection',
                '--dimension', '1024',
                '--description', 'Test description'
            ])
            
            assert result.exit_code == 0
            assert "Collection 'test_collection' created successfully" in result.output
            assert "ID: 1" in result.output
            assert "Dimension: 1024" in result.output
    
    def test_create_collection_invalid_dimension(self):
        """Test collection creation with invalid dimension."""
        runner = CliRunner()
        
        with patch('pgvector_cli.main.auto_cleanup'):
            result = runner.invoke(cli, [
                'create-collection', 'test_collection',
                '--dimension', '512'  # Not 1024
            ])
            
            assert result.exit_code == 1
            assert "向量维度必须为1024" in result.output
    
    def test_list_collections_table_format(self):
        """Test listing collections in table format."""
        runner = CliRunner()
        
        mock_collections = [
            Mock(id=1, name="col1", description="First", dimension=1024, is_active=True, 
                 created_at=Mock(strftime=Mock(return_value="2024-01-01 10:00"))),
            Mock(id=2, name="col2", description="Second", dimension=1024, is_active=True,
                 created_at=Mock(strftime=Mock(return_value="2024-01-02 11:00")))
        ]
        
        with patch('pgvector_cli.main.get_db_session') as mock_session, \
             patch('pgvector_cli.main.CollectionService') as mock_service_class, \
             patch('pgvector_cli.main.auto_cleanup'):
            
            mock_ctx = Mock()
            mock_ctx.__enter__ = Mock(return_value=mock_ctx)
            mock_ctx.__exit__ = Mock(return_value=None)
            mock_session.return_value = mock_ctx
            
            mock_service = Mock()
            mock_service.get_collections.return_value = mock_collections
            mock_service_class.return_value = mock_service
            
            result = runner.invoke(cli, ['list-collections'])
            
            assert result.exit_code == 0
            assert "col1" in result.output
            assert "col2" in result.output
    
    def test_list_collections_json_format(self):
        """Test listing collections in JSON format."""
        runner = CliRunner()
        
        mock_collections = [
            Mock(id=1, name="col1", description="First", dimension=1024, is_active=True, 
                 created_at=Mock(isoformat=Mock(return_value="2024-01-01T10:00:00"))),
        ]
        
        with patch('pgvector_cli.main.get_db_session') as mock_session, \
             patch('pgvector_cli.main.CollectionService') as mock_service_class, \
             patch('pgvector_cli.main.auto_cleanup'):
            
            mock_ctx = Mock()
            mock_ctx.__enter__ = Mock(return_value=mock_ctx)
            mock_ctx.__exit__ = Mock(return_value=None)
            mock_session.return_value = mock_ctx
            
            mock_service = Mock()
            mock_service.get_collections.return_value = mock_collections
            mock_service_class.return_value = mock_service
            
            result = runner.invoke(cli, ['list-collections', '--format', 'json'])
            
            assert result.exit_code == 0
            
            # Parse the JSON output
            output_data = json.loads(result.output)
            assert len(output_data) == 1
            assert output_data[0]['name'] == 'col1'
            assert output_data[0]['id'] == 1
    
    def test_add_vectors_batch_success(self, temp_json_file):
        """Test successful batch vector addition."""
        runner = CliRunner()
        
        mock_collection = Mock()
        mock_collection.id = 1
        mock_collection.name = "test_collection"
        
        mock_vector_records = [Mock(id=i) for i in range(1, 4)]  # 3 records
        
        with patch('pgvector_cli.main.get_db_session') as mock_session, \
             patch('pgvector_cli.main.CollectionService') as mock_coll_service, \
             patch('pgvector_cli.main.VectorService') as mock_vec_service:
            
            mock_ctx = Mock()
            mock_ctx.__enter__ = Mock(return_value=mock_ctx)
            mock_ctx.__exit__ = Mock(return_value=None)
            mock_session.return_value = mock_ctx
            
            # Mock collection service
            mock_coll_service_instance = Mock()
            mock_coll_service_instance.get_collection_by_name.return_value = mock_collection
            mock_coll_service.return_value = mock_coll_service_instance
            
            # Mock vector service
            mock_vec_service_instance = Mock()
            mock_vec_service_instance.create_vector_records_batch.return_value = mock_vector_records
            mock_vec_service.return_value = mock_vec_service_instance
            
            result = runner.invoke(cli, [
                'add-vectors-batch', 'test_collection',
                '--file', temp_json_file
            ])
            
            assert result.exit_code == 0
            assert "3 vectors added to collection" in result.output
            assert "Batch processing improved performance" in result.output
    
    def test_add_vectors_batch_file_not_found(self):
        """Test batch vector addition with non-existent file."""
        runner = CliRunner()
        
        result = runner.invoke(cli, [
            'add-vectors-batch', 'test_collection',
            '--file', '/nonexistent/file.json'
        ])
        
        assert result.exit_code == 1
        assert "File not found" in result.output
    
    def test_search_command_success(self):
        """Test successful search command."""
        runner = CliRunner()
        
        mock_collection = Mock()
        mock_collection.id = 1
        mock_collection.name = "test_collection"
        
        mock_record = Mock()
        mock_record.id = 1
        mock_record.content = "Test document content"
        mock_record.created_at = Mock(strftime=Mock(return_value="2024-01-01 10:00"))
        
        mock_results = [(mock_record, 0.95)]  # (record, similarity_score)
        
        with patch('pgvector_cli.main.get_db_session') as mock_session, \
             patch('pgvector_cli.main.CollectionService') as mock_coll_service, \
             patch('pgvector_cli.main.VectorService') as mock_vec_service:
            
            mock_ctx = Mock()
            mock_ctx.__enter__ = Mock(return_value=mock_ctx)
            mock_ctx.__exit__ = Mock(return_value=None)
            mock_ctx.execute = Mock()  # Mock SET LOCAL command
            mock_session.return_value = mock_ctx
            
            # Mock collection service
            mock_coll_service_instance = Mock()
            mock_coll_service_instance.get_collection_by_name.return_value = mock_collection
            mock_coll_service.return_value = mock_coll_service_instance
            
            # Mock vector service
            mock_vec_service_instance = Mock()
            mock_vec_service_instance.search_similar_vectors.return_value = mock_results
            mock_vec_service.return_value = mock_vec_service_instance
            
            result = runner.invoke(cli, [
                'search', 'test_collection',
                '--query', 'test query',
                '--limit', '5',
                '--precision', 'high'
            ])
            
            assert result.exit_code == 0
            assert "Test document content" in result.output
            assert "0.950" in result.output