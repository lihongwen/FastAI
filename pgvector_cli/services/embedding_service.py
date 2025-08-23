"""Embedding service for pgvector CLI."""

import logging
from typing import List, Optional
from ..config import get_settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client = None
    
    def _get_client(self):
        """Get embedding client (lazy initialization)."""
        if self._client is not None:
            return self._client
        
        # Try DashScope first
        if self.settings.dashscope_api_key:
            try:
                import dashscope
                dashscope.api_key = self.settings.dashscope_api_key
                self._client = "dashscope"
                return self._client
            except ImportError:
                logger.warning("DashScope library not available")
        
        # Fallback to OpenAI
        if self.settings.openai_api_key:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.settings.openai_api_key)
                return self._client
            except ImportError:
                logger.warning("OpenAI library not available")
        
        # No embedding service available, return dummy embeddings
        logger.warning("No embedding service configured, using dummy embeddings")
        self._client = "dummy"
        return self._client
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        client = self._get_client()
        
        if client == "dashscope":
            return self._embed_with_dashscope(text)
        elif isinstance(client, object) and hasattr(client, 'embeddings'):
            return self._embed_with_openai(text)
        else:
            return self._dummy_embedding()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed_text(text) for text in texts]
    
    def _embed_with_dashscope(self, text: str) -> List[float]:
        """Generate embedding using DashScope."""
        try:
            import dashscope
            from dashscope import TextEmbedding
            
            response = TextEmbedding.call(
                model=TextEmbedding.Models.text_embedding_v2,
                input=text
            )
            
            if response.status_code == 200:
                return response.output['embeddings'][0]['embedding']
            else:
                logger.error(f"DashScope embedding failed: {response}")
                return self._dummy_embedding()
                
        except Exception as e:
            logger.error(f"DashScope embedding error: {e}")
            return self._dummy_embedding()
    
    def _embed_with_openai(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        try:
            response = self._client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return self._dummy_embedding()
    
    def _dummy_embedding(self) -> List[float]:
        """Generate dummy embedding for testing."""
        import random
        random.seed(42)  # For reproducible dummy embeddings
        return [random.random() for _ in range(1024)]
    
    def check_api_status(self) -> bool:
        """Check if embedding service is available."""
        client = self._get_client()
        return client not in [None, "dummy"]