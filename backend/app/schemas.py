from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    dimension: int = 768

class CollectionCreate(CollectionBase):
    pass

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Collection(CollectionBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True