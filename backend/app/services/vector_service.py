from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from typing import List, Optional, Dict, Any, Tuple
from ..models.vector_record import VectorRecord
from ..models.collection import Collection
from ..schemas import VectorRecordCreate, VectorRecordUpdate, VectorSearchRequest
from .embedding_service import EmbeddingService
import logging

logger = logging.getLogger(__name__)

class VectorService:
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    def create_vector_record(self, collection_id: int, vector_data: VectorRecordCreate) -> VectorRecord:
        """
        创建向量记录
        
        Args:
            collection_id: 集合ID
            vector_data: 向量记录数据
            
        Returns:
            创建的向量记录
            
        Raises:
            Exception: 当集合不存在或嵌入失败时
        """
        try:
            # 验证集合是否存在
            collection = self.db.query(Collection).filter(
                Collection.id == collection_id,
                Collection.is_active == True
            ).first()
            
            if not collection:
                raise ValueError(f"Collection with id {collection_id} not found")
            
            # 生成向量
            vector = self.embedding_service.embed_text(vector_data.content)
            
            # 创建向量记录
            db_vector = VectorRecord(
                collection_id=collection_id,
                content=vector_data.content,
                vector=vector,
                extra_metadata=vector_data.extra_metadata or {}
            )
            
            self.db.add(db_vector)
            self.db.commit()
            self.db.refresh(db_vector)
            
            return db_vector
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create vector record: {str(e)}")
            raise
    
    def create_vector_records_batch(self, collection_id: int, vector_data_list: List[VectorRecordCreate]) -> List[VectorRecord]:
        """
        批量创建向量记录
        
        Args:
            collection_id: 集合ID
            vector_data_list: 向量记录数据列表
            
        Returns:
            创建的向量记录列表
        """
        try:
            # 验证集合是否存在
            collection = self.db.query(Collection).filter(
                Collection.id == collection_id,
                Collection.is_active == True
            ).first()
            
            if not collection:
                raise ValueError(f"Collection with id {collection_id} not found")
            
            if not vector_data_list:
                return []
            
            # 批量生成向量
            texts = [vd.content for vd in vector_data_list]
            vectors = self.embedding_service.embed_texts(texts)
            
            # 创建向量记录
            db_vectors = []
            for i, vector_data in enumerate(vector_data_list):
                db_vector = VectorRecord(
                    collection_id=collection_id,
                    content=vector_data.content,
                    vector=vectors[i],
                    extra_metadata=vector_data.extra_metadata or {}
                )
                db_vectors.append(db_vector)
            
            self.db.add_all(db_vectors)
            self.db.commit()
            
            # 刷新所有记录
            for db_vector in db_vectors:
                self.db.refresh(db_vector)
            
            return db_vectors
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create vector records batch: {str(e)}")
            raise
    
    def get_vector_records(self, collection_id: int, skip: int = 0, limit: int = 100) -> List[VectorRecord]:
        """
        获取集合中的向量记录
        
        Args:
            collection_id: 集合ID
            skip: 跳过记录数
            limit: 限制记录数
            
        Returns:
            向量记录列表
        """
        return self.db.query(VectorRecord).filter(
            VectorRecord.collection_id == collection_id
        ).offset(skip).limit(limit).all()
    
    def get_vector_record(self, vector_id: int) -> Optional[VectorRecord]:
        """
        获取单个向量记录
        
        Args:
            vector_id: 向量记录ID
            
        Returns:
            向量记录或None
        """
        return self.db.query(VectorRecord).filter(VectorRecord.id == vector_id).first()
    
    def update_vector_record(self, vector_id: int, vector_update: VectorRecordUpdate) -> Optional[VectorRecord]:
        """
        更新向量记录
        
        Args:
            vector_id: 向量记录ID
            vector_update: 更新数据
            
        Returns:
            更新后的向量记录或None
        """
        try:
            db_vector = self.get_vector_record(vector_id)
            if not db_vector:
                return None
            
            # 如果内容发生变化，需要重新生成向量
            content_changed = False
            update_data = vector_update.dict(exclude_unset=True)
            
            if "content" in update_data and update_data["content"] != db_vector.content:
                content_changed = True
                new_vector = self.embedding_service.embed_text(update_data["content"])
                db_vector.vector = new_vector
            
            # 更新其他字段
            for field, value in update_data.items():
                if field != "content" or not content_changed:  # 避免重复设置content
                    setattr(db_vector, field, value)
            
            self.db.commit()
            self.db.refresh(db_vector)
            
            return db_vector
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update vector record: {str(e)}")
            raise
    
    def delete_vector_record(self, vector_id: int) -> bool:
        """
        删除向量记录
        
        Args:
            vector_id: 向量记录ID
            
        Returns:
            删除是否成功
        """
        try:
            db_vector = self.get_vector_record(vector_id)
            if not db_vector:
                return False
            
            self.db.delete(db_vector)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete vector record: {str(e)}")
            raise
    
    def search_similar_vectors(self, collection_id: int, search_request: VectorSearchRequest) -> List[Tuple[VectorRecord, float]]:
        """
        搜索相似向量
        
        Args:
            collection_id: 集合ID
            search_request: 搜索请求
            
        Returns:
            (向量记录, 相似度分数) 元组列表，按相似度降序排列
        """
        try:
            # 生成查询向量
            query_vector = self.embedding_service.embed_query(search_request.query)
            
            # 构建SQL查询
            query = """
            SELECT *, (vector <=> %s) AS distance
            FROM vector_records 
            WHERE collection_id = %s
            """
            
            params = [query_vector, collection_id]
            
            # 添加元数据过滤
            if search_request.metadata_filter:
                for key, value in search_request.metadata_filter.items():
                    query += f" AND extra_metadata->>%s = %s"
                    params.extend([key, str(value)])
            
            query += " ORDER BY distance ASC LIMIT %s"
            params.append(search_request.limit)
            
            # 执行查询
            result = self.db.execute(text(query), params)
            
            # 处理结果
            search_results = []
            for row in result:
                # 重新构造VectorRecord对象
                vector_record = VectorRecord(
                    id=row.id,
                    collection_id=row.collection_id,
                    content=row.content,
                    vector=row.vector,
                    extra_metadata=row.extra_metadata,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                
                # 将距离转换为相似度分数 (1 - distance)
                similarity_score = max(0, 1 - row.distance)
                search_results.append((vector_record, similarity_score))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search similar vectors: {str(e)}")
            raise
    
    def get_collection_stats(self, collection_id: int) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Args:
            collection_id: 集合ID
            
        Returns:
            统计信息字典
        """
        try:
            total_vectors = self.db.query(VectorRecord).filter(
                VectorRecord.collection_id == collection_id
            ).count()
            
            return {
                "collection_id": collection_id,
                "total_vectors": total_vectors,
                "dimension": 1024
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            raise