"""Embedding service for pgvector CLI."""

from typing import List

from ..config import get_settings
from ..exceptions import ConfigurationError, EmbeddingError
from ..logging_config import StructuredLogger

logger = StructuredLogger("embedding_service")

class EmbeddingService:
    """Service for generating text embeddings using DashScope."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._dashscope_client = None

    def _get_client(self):
        """Get DashScope embedding client (lazy initialization)."""
        if self._dashscope_client is not None:
            return self._dashscope_client

        # Only use DashScope
        if not self.settings.dashscope_api_key:
            logger.error("DashScope API key not configured")
            raise ConfigurationError(
                "DashScope API key is required but not configured. "
                "Please set DASHSCOPE_API_KEY environment variable",
                code="MISSING_API_KEY"
            )

        try:
            import dashscope
            from dashscope import TextEmbedding
            dashscope.api_key = self.settings.dashscope_api_key
            self._dashscope_client = TextEmbedding
            self._client = "dashscope"
            logger.info("DashScope client initialized successfully")
            return self._dashscope_client
        except ImportError as e:
            logger.error("DashScope library not available", error=str(e))
            raise ConfigurationError(
                "DashScope library is required but not installed. "
                "Please install: pip install dashscope",
                code="MISSING_DEPENDENCY"
            ) from e

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using DashScope."""
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            raise EmbeddingError("Cannot generate embedding for empty text", code="EMPTY_INPUT")

        # 如果文本超过API限制，这说明分块系统有问题，应该报错而不是截断
        if len(text) > 8192:
            logger.error("Text too long for embedding API - this indicates a chunking system bug!",
                        text_length=len(text), max_allowed=8192)
            raise EmbeddingError(
                f"Text too long: {len(text)} characters exceeds API limit of 8192. "
                f"This indicates the chunking system is not working correctly.",
                code="TEXT_TOO_LONG"
            )

        try:
            self._get_client()
            result = self._embed_with_dashscope(text)
            logger.debug("Generated embedding for single text", text_length=len(text))
            return result
        except (ConfigurationError, EmbeddingError):
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error("Unexpected error in embed_text", error=str(e), text_length=len(text))
            raise EmbeddingError(f"Failed to generate embedding: {e}") from e

    def embed_texts(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Generate embeddings for multiple texts with batch processing."""
        if not texts:
            return []

        client = self._get_client()
        all_embeddings = []

        # Process texts in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                # DashScope supports batch processing
                response = client.call(
                    model="text-embedding-v4",
                    input=batch
                )

                if response.status_code == 200:
                    batch_embeddings = []
                    for embedding_data in response.output['embeddings']:
                        embedding = embedding_data['embedding']
                        # Apply MRL transform and L2 normalization
                        if len(embedding) != 1024:
                            embedding = self._mrl_transform_to_1024(embedding)
                        embedding = self._l2_normalize_vector(embedding)
                        batch_embeddings.append(embedding)

                    all_embeddings.extend(batch_embeddings)
                    logger.debug(f"Processed batch {i//batch_size + 1}, embeddings: {len(batch)}")
                else:
                    logger.error(f"DashScope batch embedding failed: {response}")
                    # Fallback to individual processing
                    for text in batch:
                        all_embeddings.append(self.embed_text(text))

            except Exception as e:
                logger.warning(f"Batch embedding failed, falling back to individual processing: {e}")
                # Fallback to individual processing
                for text in batch:
                    all_embeddings.append(self.embed_text(text))

        return all_embeddings

    def _embed_with_dashscope(self, text: str) -> List[float]:
        """Generate embedding using DashScope."""
        try:
            from dashscope import TextEmbedding

            response = TextEmbedding.call(
                model="text-embedding-v4",
                input=text
            )

            if response.status_code == 200:
                embedding = response.output['embeddings'][0]['embedding']
                # 使用MRL转换到1024维度
                if len(embedding) != 1024:
                    embedding = self._mrl_transform_to_1024(embedding)
                    logger.info(f"使用MRL转换向量维度从 {len(response.output['embeddings'][0]['embedding'])} 到 1024")

                # L2标准化向量，优化cosine distance计算性能
                embedding = self._l2_normalize_vector(embedding)
                logger.debug("应用L2标准化，向量长度标准化为1")

                return embedding
            else:
                logger.error(f"DashScope embedding failed: {response}")
                raise Exception(f"DashScope API error: {response}")

        except Exception as e:
            logger.error(f"DashScope embedding error: {e}")
            raise

    def _mrl_transform_to_1024(self, embedding: list) -> list:
        """使用MRL（Multi-Representation Learning）转换向量到1024维度"""
        import numpy as np

        input_dim = len(embedding)
        target_dim = 1024

        if input_dim == target_dim:
            return embedding

        # 转换为numpy数组
        vec = np.array(embedding, dtype=np.float32)

        if input_dim > target_dim:
            # 降维：使用分块平均法 + 权重保持重要信息
            chunk_size = input_dim // target_dim
            remainder = input_dim % target_dim

            result = []
            idx = 0

            for i in range(target_dim):
                # 动态调整块大小以处理余数
                current_chunk_size = chunk_size + (1 if i < remainder else 0)
                chunk = vec[idx:idx + current_chunk_size]

                # 使用L2范数加权平均，保持语义信息
                chunk_norm = np.linalg.norm(chunk)
                if chunk_norm > 0:
                    weighted_avg = np.mean(chunk) * (chunk_norm / np.sqrt(current_chunk_size))
                else:
                    weighted_avg = np.mean(chunk)

                result.append(float(weighted_avg))
                idx += current_chunk_size

            return result

        else:
            # 升维：使用插值策略
            try:
                # 使用线性插值
                old_indices = np.linspace(0, 1, input_dim)
                new_indices = np.linspace(0, 1, target_dim)
                interpolated = np.interp(new_indices, old_indices, vec)

                # 归一化以保持向量范数相对稳定
                original_norm = np.linalg.norm(vec)
                new_norm = np.linalg.norm(interpolated)
                if new_norm > 0:
                    interpolated = interpolated * (original_norm / new_norm)

                return interpolated.tolist()

            except Exception:
                # 如果插值失败，使用重复填充策略
                scale_factor = target_dim / input_dim
                result = []

                for i in range(input_dim):
                    repeat_count = int(scale_factor)
                    if i < target_dim % input_dim:
                        repeat_count += 1
                    result.extend([vec[i]] * repeat_count)

                return result[:target_dim]

    def _l2_normalize_vector(self, vector: list) -> list:
        """L2标准化向量，确保向量长度为1，优化cosine distance计算"""
        import numpy as np

        vec = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(vec)

        if norm == 0:
            logger.warning("向量范数为0，无法进行L2标准化")
            return vector

        normalized = vec / norm
        return normalized.tolist()

    def check_api_status(self) -> bool:
        """Check if DashScope embedding service is available."""
        try:
            client = self._get_client()
            return client == "dashscope"
        except Exception:
            return False
