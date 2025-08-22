import os
from typing import List, Union
from openai import OpenAI
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url
        )
        self.model = "text-embedding-v4"
        self.dimension = 1024
    
    def embed_text(self, text: str) -> List[float]:
        """
        将单个文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            1024维向量列表
            
        Raises:
            Exception: 当API调用失败时
        """
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            if not settings.dashscope_api_key:
                raise ValueError("DASHSCOPE_API_KEY is not configured")
            
            response = self.client.embeddings.create(
                model=self.model,
                input=text.strip(),
                dimensions=self.dimension,
                encoding_format="float"
            )
            
            # 获取向量数据
            embedding = response.data[0].embedding
            
            if len(embedding) != self.dimension:
                raise ValueError(f"Expected {self.dimension} dimensions, got {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to embed text: {str(e)}")
            raise Exception(f"Embedding failed: {str(e)}")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表的列表
            
        Raises:
            Exception: 当API调用失败时
        """
        try:
            if not texts:
                return []
            
            # 过滤空文本
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            if not valid_texts:
                raise ValueError("No valid texts provided")
            
            if not settings.dashscope_api_key:
                raise ValueError("DASHSCOPE_API_KEY is not configured")
            
            # 批量处理
            response = self.client.embeddings.create(
                model=self.model,
                input=valid_texts,
                dimensions=self.dimension,
                encoding_format="float"
            )
            
            # 提取所有向量
            embeddings = []
            for data in response.data:
                embedding = data.embedding
                if len(embedding) != self.dimension:
                    raise ValueError(f"Expected {self.dimension} dimensions, got {len(embedding)}")
                embeddings.append(embedding)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to embed texts: {str(e)}")
            raise Exception(f"Batch embedding failed: {str(e)}")
    
    def embed_query(self, query: str) -> List[float]:
        """
        为查询文本生成向量（与embed_text相同，但语义上更明确）
        
        Args:
            query: 查询文本
            
        Returns:
            1024维向量列表
        """
        return self.embed_text(query)
    
    def check_api_status(self) -> bool:
        """
        检查API是否可用
        
        Returns:
            True if API is available, False otherwise
        """
        try:
            if not settings.dashscope_api_key:
                return False
            
            # 测试一个简单的文本
            test_text = "测试文本"
            self.embed_text(test_text)
            return True
        except Exception as e:
            logger.error(f"API status check failed: {str(e)}")
            return False