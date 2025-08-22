from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional

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