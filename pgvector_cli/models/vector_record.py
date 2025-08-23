"""Vector record model for pgvector CLI."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from ..database import Base

class VectorRecord(Base):
    """Vector record model for storing vector data."""
    
    __tablename__ = "vector_records"
    
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False)
    content = Column(Text, nullable=False)
    vector = Column(Vector(1024), nullable=False)  # Default to 1024 dimensions
    extra_metadata = Column(JSONB, nullable=True, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship with Collection
    collection = relationship("Collection", back_populates="vectors")
    
    def __repr__(self):
        return f"<VectorRecord(id={self.id}, collection_id={self.collection_id}, content='{self.content[:50]}...')>"