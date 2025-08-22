from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import Collection, CollectionCreate, CollectionUpdate
from ..services.collection_service import CollectionService

router = APIRouter(prefix="/api/collections", tags=["collections"])

@router.get("/", response_model=List[Collection])
def get_collections(db: Session = Depends(get_db)):
    """获取所有集合"""
    service = CollectionService(db)
    return service.get_collections()

@router.get("/{collection_id}", response_model=Collection)
def get_collection(collection_id: int, db: Session = Depends(get_db)):
    """获取指定集合"""
    service = CollectionService(db)
    collection = service.get_collection(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    return collection

@router.post("/", response_model=Collection, status_code=status.HTTP_201_CREATED)
def create_collection(collection: CollectionCreate, db: Session = Depends(get_db)):
    """创建新集合"""
    service = CollectionService(db)
    try:
        return service.create_collection(collection)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{collection_id}", response_model=Collection)
def update_collection(
    collection_id: int, 
    collection_update: CollectionUpdate, 
    db: Session = Depends(get_db)
):
    """更新集合信息"""
    service = CollectionService(db)
    try:
        collection = service.update_collection(collection_id, collection_update)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )
        return collection
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    """删除集合"""
    service = CollectionService(db)
    success = service.delete_collection(collection_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )