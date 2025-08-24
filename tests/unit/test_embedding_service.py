"""Unit tests for embedding service."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from pgvector_cli.services.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test embedding service."""

    @patch('pgvector_cli.services.embedding_service.get_settings')
    def test_init_with_valid_api_key(self, mock_get_settings):
        """Test initialization with valid API key."""
        mock_settings = Mock()
        mock_settings.dashscope_api_key = "test_api_key"
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()
        assert service.settings == mock_settings
        assert service._client is None
        assert service._dashscope_client is None

    @patch('pgvector_cli.services.embedding_service.get_settings')
    @patch('dashscope.TextEmbedding')
    def test_get_client_success(self, mock_text_embedding, mock_get_settings):
        """Test successful client initialization."""
        mock_settings = Mock()
        mock_settings.dashscope_api_key = "test_api_key"
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()
        client = service._get_client()

        assert client == mock_text_embedding
        assert service._client == "dashscope"
        assert service._dashscope_client == mock_text_embedding

    @patch('pgvector_cli.services.embedding_service.get_settings')
    def test_get_client_no_api_key(self, mock_get_settings):
        """Test client initialization without API key."""
        mock_settings = Mock()
        mock_settings.dashscope_api_key = ""
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()

        with pytest.raises(ValueError, match="DashScope API key is required"):
            service._get_client()

    @patch('pgvector_cli.services.embedding_service.get_settings')
    def test_get_client_import_error(self, mock_get_settings):
        """Test client initialization with missing library."""
        mock_settings = Mock()
        mock_settings.dashscope_api_key = "test_api_key"
        mock_get_settings.return_value = mock_settings

        with patch('builtins.__import__', side_effect=ImportError("No module named 'dashscope'")):
            service = EmbeddingService()

            with pytest.raises(ImportError, match="DashScope library is required"):
                service._get_client()

    @patch('pgvector_cli.services.embedding_service.get_settings')
    def test_embed_text_success(self, mock_get_settings):
        """Test successful text embedding."""
        mock_settings = Mock()
        mock_settings.dashscope_api_key = "test_api_key"
        mock_get_settings.return_value = mock_settings

        # Mock DashScope response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output = {
            'embeddings': [{'embedding': [0.1] * 1024}]
        }

        with patch('pgvector_cli.services.embedding_service.TextEmbedding') as mock_text_embedding:
            mock_text_embedding.call.return_value = mock_response

            service = EmbeddingService()
            service._dashscope_client = mock_text_embedding
            service._client = "dashscope"

            result = service.embed_text("test text")

            assert len(result) == 1024
            assert all(isinstance(x, float) for x in result)
            mock_text_embedding.call.assert_called_once_with(
                model="text-embedding-v4",
                input="test text"
            )

    def test_mrl_transform_to_1024_same_dimension(self):
        """Test MRL transform when input is already 1024 dimensions."""
        service = EmbeddingService()
        input_vector = [0.1] * 1024

        result = service._mrl_transform_to_1024(input_vector)

        assert result == input_vector
        assert len(result) == 1024

    def test_mrl_transform_to_1024_downsample(self):
        """Test MRL transform when downsampling from higher dimensions."""
        service = EmbeddingService()
        input_vector = [0.1] * 1536  # Higher than 1024

        result = service._mrl_transform_to_1024(input_vector)

        assert len(result) == 1024
        assert all(isinstance(x, float) for x in result)

    def test_mrl_transform_to_1024_upsample(self):
        """Test MRL transform when upsampling from lower dimensions."""
        service = EmbeddingService()
        input_vector = [0.1] * 512  # Lower than 1024

        result = service._mrl_transform_to_1024(input_vector)

        assert len(result) == 1024
        assert all(isinstance(x, float) for x in result)

    def test_l2_normalize_vector_normal(self):
        """Test L2 normalization with normal vector."""
        service = EmbeddingService()
        input_vector = [3.0, 4.0]  # Norm = 5.0

        result = service._l2_normalize_vector(input_vector)

        # Check that the result is normalized
        import numpy as np
        np_result = np.array(result)
        norm = np.linalg.norm(np_result)
        assert abs(norm - 1.0) < 1e-10

    def test_l2_normalize_vector_zero(self):
        """Test L2 normalization with zero vector."""
        service = EmbeddingService()
        input_vector = [0.0, 0.0, 0.0]

        result = service._l2_normalize_vector(input_vector)

        # Should return original vector when norm is 0
        assert result == input_vector

    @patch('pgvector_cli.services.embedding_service.get_settings')
    def test_embed_texts_batch_success(self, mock_get_settings):
        """Test successful batch text embedding."""
        mock_settings = Mock()
        mock_settings.dashscope_api_key = "test_api_key"
        mock_get_settings.return_value = mock_settings

        # Mock DashScope batch response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.output = {
            'embeddings': [
                {'embedding': [0.1] * 1024},
                {'embedding': [0.2] * 1024}
            ]
        }

        with patch('pgvector_cli.services.embedding_service.TextEmbedding') as mock_text_embedding:
            mock_text_embedding.call.return_value = mock_response

            service = EmbeddingService()
            service._dashscope_client = mock_text_embedding
            service._client = "dashscope"

            texts = ["text1", "text2"]
            result = service.embed_texts(texts)

            assert len(result) == 2
            assert len(result[0]) == 1024
            assert len(result[1]) == 1024

    @patch('pgvector_cli.services.embedding_service.get_settings')
    def test_embed_texts_empty_list(self, mock_get_settings):
        """Test batch embedding with empty list."""
        mock_settings = Mock()
        mock_settings.dashscope_api_key = "test_api_key"
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()
        result = service.embed_texts([])

        assert result == []

    @patch('pgvector_cli.services.embedding_service.get_settings')
    def test_check_api_status_success(self, mock_get_settings):
        """Test API status check success."""
        mock_settings = Mock()
        mock_settings.dashscope_api_key = "test_api_key"
        mock_get_settings.return_value = mock_settings

        with patch('pgvector_cli.services.embedding_service.TextEmbedding'):
            service = EmbeddingService()
            result = service.check_api_status()

            assert result is True

    @patch('pgvector_cli.services.embedding_service.get_settings')
    def test_check_api_status_failure(self, mock_get_settings):
        """Test API status check failure."""
        mock_settings = Mock()
        mock_settings.dashscope_api_key = ""
        mock_get_settings.return_value = mock_settings

        service = EmbeddingService()
        result = service.check_api_status()

        assert result is False
