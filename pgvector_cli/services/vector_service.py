"""Vector service for pgvector CLI."""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..models.collection import Collection
from ..models.vector_record import VectorRecord
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
            Collection.is_active
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

    def create_vector_records_batch(self, collection_id: int,
                                  contents_and_metadata: List[Dict[str, Any]]) -> List[VectorRecord]:
        """Create multiple vector records in batch for better performance."""
        # Validate collection exists
        collection = self.session.query(Collection).filter(
            Collection.id == collection_id,
            Collection.is_active
        ).first()

        if not collection:
            raise ValueError(f"Collection with id {collection_id} not found")

        if not contents_and_metadata:
            return []

        # Extract texts for batch embedding
        texts = [item['content'] for item in contents_and_metadata]

        # Generate embeddings in batch
        embeddings = self.embedding_service.embed_texts(texts)

        # Create vector records
        vector_records = []
        for i, item in enumerate(contents_and_metadata):
            vector_record = VectorRecord(
                collection_id=collection_id,
                content=item['content'],
                vector=embeddings[i],
                extra_metadata=item.get('extra_metadata', {})
            )
            vector_records.append(vector_record)

        # Bulk insert
        self.session.add_all(vector_records)
        self.session.commit()

        # Refresh all records to get IDs
        for record in vector_records:
            self.session.refresh(record)

        return vector_records

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

        # Build SQL query using SQLAlchemy ORM with pgvector
        result = self.session.query(
            VectorRecord,
            VectorRecord.vector.cosine_distance(query_vector).label('distance')
        ).filter(
            VectorRecord.collection_id == collection_id
        ).order_by(
            VectorRecord.vector.cosine_distance(query_vector)
        ).limit(limit).all()

        # Process results
        search_results = []
        for vector_record, distance in result:
            # Convert distance to similarity score (1 - distance)
            similarity_score = max(0, 1 - distance)
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

    def get_vector_count(self, collection_id: int) -> int:
        """Get the count of vectors in a collection."""
        return self.session.query(VectorRecord).filter(
            VectorRecord.collection_id == collection_id
        ).count()

    def search_vectors(self, collection_id: int, query: str, limit: int = 10) -> List[Tuple[VectorRecord, float]]:
        """Search for similar vectors (alias for search_similar_vectors)."""
        return self.search_similar_vectors(collection_id, query, limit)
