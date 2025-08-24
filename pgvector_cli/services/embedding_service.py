"""Embedding service for pgvector CLI."""

import logging
from typing import List, Optional
from ..config import get_settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating text embeddings using DashScope."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client = None
    
    def _get_client(self):
        """Get DashScope embedding client (lazy initialization)."""
        if self._client is not None:
            return self._client
        
        # Only use DashScope
        if self.settings.dashscope_api_key:
            try:
                import dashscope
                dashscope.api_key = self.settings.dashscope_api_key
                self._client = "dashscope"
                return self._client
            except ImportError:
                logger.error("DashScope library not available. Please install: pip install dashscope")
                raise ImportError("DashScope library is required but not installed")
        else:
            logger.error("DashScope API key not configured. Please set DASHSCOPE_API_KEY environment variable")
            raise ValueError("DashScope API key is required but not configured")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using DashScope."""
        client = self._get_client()
        return self._embed_with_dashscope(text)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed_text(text) for text in texts]
    
    def _embed_with_dashscope(self, text: str) -> List[float]:
        """Generate embedding using DashScope."""
        try:
            import dashscope
            from dashscope import TextEmbedding
            
            response = TextEmbedding.call(
                model="text-embedding-v4",
                input=text
            )
            
            if response.status_code == 200:
                return response.output['embeddings'][0]['embedding']
            else:
                logger.error(f"DashScope embedding failed: {response}")
                raise Exception(f"DashScope API error: {response}")
                
        except Exception as e:
            logger.error(f"DashScope embedding error: {e}")
            raise
    
    
    def check_api_status(self) -> bool:
        """Check if DashScope embedding service is available."""
        try:
            client = self._get_client()
            return client == "dashscope"
        except:
            return False