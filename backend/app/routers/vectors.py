from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..database import get_db
from ..schemas import (
    VectorRecord, VectorRecordCreate, VectorRecordUpdate, 
    VectorSearchRequest, VectorSearchResult
)
from ..services.vector_service import VectorService
from ..services.embedding_service import EmbeddingService

router = APIRouter(prefix="/api/collections", tags=["vectors"])

@router.post("/{collection_id}/vectors", response_model=VectorRecord, status_code=status.HTTP_201_CREATED)
def create_vector(
    collection_id: int, 
    vector_data: VectorRecordCreate, 
    db: Session = Depends(get_db)
):
    """创建向量记录"""
    try:
        service = VectorService(db)
        return service.create_vector_record(collection_id, vector_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vector: {str(e)}"
        )

@router.post("/{collection_id}/vectors/batch", response_model=List[VectorRecord], status_code=status.HTTP_201_CREATED)
def create_vectors_batch(
    collection_id: int, 
    vector_data_list: List[VectorRecordCreate], 
    db: Session = Depends(get_db)
):
    """批量创建向量记录"""
    try:
        service = VectorService(db)
        return service.create_vector_records_batch(collection_id, vector_data_list)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vectors: {str(e)}"
        )

@router.get("/{collection_id}/vectors", response_model=List[VectorRecord])
def get_vectors(
    collection_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取集合中的向量记录"""
    try:
        service = VectorService(db)
        return service.get_vector_records(collection_id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vectors: {str(e)}"
        )

@router.get("/{collection_id}/vectors/{vector_id}", response_model=VectorRecord)
def get_vector(
    collection_id: int,
    vector_id: int,
    db: Session = Depends(get_db)
):
    """获取单个向量记录"""
    try:
        service = VectorService(db)
        vector = service.get_vector_record(vector_id)
        if not vector or vector.collection_id != collection_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector not found"
            )
        return vector
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vector: {str(e)}"
        )

@router.put("/{collection_id}/vectors/{vector_id}", response_model=VectorRecord)
def update_vector(
    collection_id: int,
    vector_id: int,
    vector_update: VectorRecordUpdate,
    db: Session = Depends(get_db)
):
    """更新向量记录"""
    try:
        service = VectorService(db)
        
        # 验证向量是否属于指定集合
        existing_vector = service.get_vector_record(vector_id)
        if not existing_vector or existing_vector.collection_id != collection_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector not found"
            )
        
        updated_vector = service.update_vector_record(vector_id, vector_update)
        if not updated_vector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector not found"
            )
        return updated_vector
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vector: {str(e)}"
        )

@router.delete("/{collection_id}/vectors/{vector_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vector(
    collection_id: int,
    vector_id: int,
    db: Session = Depends(get_db)
):
    """删除向量记录"""
    try:
        service = VectorService(db)
        
        # 验证向量是否属于指定集合
        existing_vector = service.get_vector_record(vector_id)
        if not existing_vector or existing_vector.collection_id != collection_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector not found"
            )
        
        success = service.delete_vector_record(vector_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete vector: {str(e)}"
        )

@router.post("/{collection_id}/vectors/search", response_model=List[VectorSearchResult])
def search_similar_vectors(
    collection_id: int,
    search_request: VectorSearchRequest,
    db: Session = Depends(get_db)
):
    """搜索相似向量"""
    try:
        service = VectorService(db)
        search_results = service.search_similar_vectors(collection_id, search_request)
        
        # 转换为响应格式
        return [
            VectorSearchResult(
                vector_record=vector_record,
                similarity_score=similarity_score
            )
            for vector_record, similarity_score in search_results
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search vectors: {str(e)}"
        )

@router.get("/{collection_id}/stats", response_model=Dict[str, Any])
def get_collection_stats(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """获取集合统计信息"""
    try:
        service = VectorService(db)
        return service.get_collection_stats(collection_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection stats: {str(e)}"
        )

# 嵌入服务状态检查
@router.get("/embedding/status")
def check_embedding_service_status():
    """检查嵌入服务状态"""
    try:
        embedding_service = EmbeddingService()
        is_available = embedding_service.check_api_status()
        return {
            "status": "available" if is_available else "unavailable",
            "model": "text-embedding-v4",
            "dimension": 1024
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }