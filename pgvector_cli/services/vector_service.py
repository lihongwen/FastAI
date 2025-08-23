"""Vector service for pgvector CLI."""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any, Tuple

from ..models.vector_record import VectorRecord
from ..models.collection import Collection
from .embedding_service import EmbeddingService

class VectorService:
    """Service for managing vectors."""
    
    def __init__(self, session: Session):
        self.session = session
        self.embedding_service = EmbeddingService()
    
    def create_vector_record(self, collection_id: int, content: str, 
                           extra_metadata: Optional[Dict[str, Any]] = None) -> VectorRecord:
        """Create a vector record."""
        # Validate collection exists
        collection = self.session.query(Collection).filter(
            Collection.id == collection_id,
            Collection.is_active == True
        ).first()
        
        if not collection:
            raise ValueError(f"Collection with id {collection_id} not found")
        
        # Generate vector
        vector = self.embedding_service.embed_text(content)
        
        # Create vector record
        vector_record = VectorRecord(
            collection_id=collection_id,
            content=content,
            vector=vector,
            extra_metadata=extra_metadata or {}
        )
        
        self.session.add(vector_record)
        self.session.commit()
        self.session.refresh(vector_record)
        
        return vector_record
    
    def get_vector_records(self, collection_id: int, skip: int = 0, limit: int = 100) -> List[VectorRecord]:
        """Get vector records from collection."""
        return self.session.query(VectorRecord).filter(
            VectorRecord.collection_id == collection_id
        ).offset(skip).limit(limit).all()
    
    def get_vector_record(self, vector_id: int) -> Optional[VectorRecord]:
        """Get single vector record."""
        return self.session.query(VectorRecord).filter(VectorRecord.id == vector_id).first()
    
    def delete_vector_record(self, vector_id: int) -> bool:
        """Delete vector record."""
        vector_record = self.get_vector_record(vector_id)
        if not vector_record:
            return False
        
        self.session.delete(vector_record)
        self.session.commit()
        return True
    
    def search_similar_vectors(self, collection_id: int, query: str, 
                             limit: int = 10) -> List[Tuple[VectorRecord, float]]:
        """Search for similar vectors."""
        # Generate query vector
        query_vector = self.embedding_service.embed_text(query)
        
        # Convert query vector to pgvector format
        from pgvector.sqlalchemy import Vector
        
        # Build SQL query
        sql_query = text("""
        SELECT *, (vector <=> :query_vector) AS distance
        FROM vector_records 
        WHERE collection_id = :collection_id
        ORDER BY distance ASC 
        LIMIT :limit
        """)
        
        # Execute query with pgvector type
        result = self.session.execute(sql_query, {
            'query_vector': query_vector,
            'collection_id': collection_id,
            'limit': limit
        })
        
        # Process results
        search_results = []
        for row in result:
            # Reconstruct VectorRecord object
            vector_record = VectorRecord(
                id=row.id,
                collection_id=row.collection_id,
                content=row.content,
                vector=row.vector,
                extra_metadata=row.extra_metadata,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            
            # Convert distance to similarity score (1 - distance)
            similarity_score = max(0, 1 - row.distance)
            search_results.append((vector_record, similarity_score))
        
        return search_results
    
    def get_collection_stats(self, collection_id: int) -> Dict[str, Any]:
        """Get collection statistics."""
        total_vectors = self.session.query(VectorRecord).filter(
            VectorRecord.collection_id == collection_id
        ).count()
        
        return {
            "collection_id": collection_id,
            "total_vectors": total_vectors,
            "dimension": 1024
        }