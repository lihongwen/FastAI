from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from ..database import Base

class VectorRecord(Base):
    __tablename__ = "vector_records"
    
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False)
    content = Column(Text, nullable=False)  # 原始文本内容
    vector = Column(Vector(1024), nullable=False)  # 1024维向量
    extra_metadata = Column(JSON, nullable=True)  # 额外的元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 与Collection的关系
    collection = relationship("Collection", back_populates="vectors")
    
    def __repr__(self):
        return f"<VectorRecord(id={self.id}, collection_id={self.collection_id}, content='{self.content[:50]}...')>"