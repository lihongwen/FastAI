from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional, List, Dict, Any

class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None

class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dimension: int = 1024  # Fixed dimension, not user-modifiable
    
    @validator('dimension')
    def validate_dimension(cls, v):
        if v != 1024:
            raise ValueError('Dimension must be 1024 and cannot be changed')
        return v

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Collection(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    dimension: int = 1024
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 向量记录相关的schemas
class VectorRecordBase(BaseModel):
    content: str
    extra_metadata: Optional[Dict[str, Any]] = None

class VectorRecordCreate(VectorRecordBase):
    pass

class VectorRecordUpdate(BaseModel):
    content: Optional[str] = None
    extra_metadata: Optional[Dict[str, Any]] = None

class VectorRecord(VectorRecordBase):
    id: int
    collection_id: int
    vector: List[float]  # 向量数据
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class VectorSearchRequest(BaseModel):
    query: str
    limit: int = 10
    metadata_filter: Optional[Dict[str, Any]] = None

class VectorSearchResult(BaseModel):
    vector_record: VectorRecord
    similarity_score: float