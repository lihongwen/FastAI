"""Vector service for pgvector CLI."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, text, and_
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

    def get_files_in_collection(self, collection_id: int) -> List[Dict[str, Any]]:
        """Get list of files in a collection with statistics."""
        # Query for distinct files with aggregated statistics
        # Use -> operator for JSONB access (compatible with PostgreSQL 9.3+)
        query = self.session.query(
            (VectorRecord.extra_metadata.op('->>')('file_name')).label('file_name'),
            (VectorRecord.extra_metadata.op('->>')('file_path')).label('file_path'),
            func.count(VectorRecord.id).label('vector_count'),
            func.min(VectorRecord.created_at).label('first_added'),
            func.max(VectorRecord.created_at).label('last_added'),
            (VectorRecord.extra_metadata.op('->>')('file_size')).label('file_size_bytes')
        ).filter(
            VectorRecord.collection_id == collection_id,
            VectorRecord.extra_metadata.op('->>')('file_path').isnot(None)  # Only records with file_path metadata
        ).group_by(
            VectorRecord.extra_metadata.op('->>')('file_name'),
            VectorRecord.extra_metadata.op('->>')('file_path'),
            VectorRecord.extra_metadata.op('->>')('file_size')
        ).order_by(
            func.max(VectorRecord.created_at).desc()  # Most recently added first
        )
        
        results = query.all()
        
        files = []
        for result in results:
            file_info = {
                'file_name': result.file_name,
                'file_path': result.file_path,
                'vector_count': result.vector_count,
                'first_added': result.first_added.isoformat() if result.first_added else None,
                'last_added': result.last_added.isoformat() if result.last_added else None,
            }
            
            # Convert file size to int if available
            if result.file_size_bytes:
                try:
                    file_info['file_size_bytes'] = int(result.file_size_bytes)
                except (ValueError, TypeError):
                    file_info['file_size_bytes'] = None
            else:
                file_info['file_size_bytes'] = None
                
            files.append(file_info)
        
        return files

    def get_file_summary(self, collection_id: int) -> Dict[str, Any]:
        """Get summary statistics for files in collection."""
        files = self.get_files_in_collection(collection_id)
        
        if not files:
            return {
                'total_files': 0,
                'total_vectors': 0,
                'file_types': {}
            }
        
        total_vectors = sum(file_info['vector_count'] for file_info in files)
        
        # Count file types by extension
        file_types = {}
        for file_info in files:
            if file_info['file_name']:
                ext = Path(file_info['file_name']).suffix.lower().lstrip('.')
                if not ext:
                    ext = 'unknown'
                file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            'total_files': len(files),
            'total_vectors': total_vectors,
            'file_types': file_types
        }

    def check_file_exists(self, collection_id: int, file_path: str) -> Optional[Dict[str, Any]]:
        """Check if a file already exists in the collection."""
        file_path_obj = Path(file_path).resolve()
        file_path_str = str(file_path_obj)
        file_name = file_path_obj.name
        
        # Query for vectors from this file
        vectors = self.session.query(VectorRecord).filter(
            VectorRecord.collection_id == collection_id
        ).filter(
            text("(extra_metadata->>'file_path' = :file_path_exact OR "
                 "extra_metadata->>'file_path' = :file_path_abs OR "
                 "extra_metadata->>'file_name' = :file_name)")
        ).params(
            file_path_exact=file_path,
            file_path_abs=file_path_str,
            file_name=file_name
        ).all()
        
        if not vectors:
            return None
        
        # Get file info from first vector's metadata
        first_vector = vectors[0]
        stored_file_path = first_vector.extra_metadata.get('file_path')
        
        return {
            'exists': True,
            'vector_count': len(vectors),
            'stored_file_path': stored_file_path,
            'first_added': min(v.created_at for v in vectors).isoformat(),
            'last_added': max(v.created_at for v in vectors).isoformat(),
            'vector_ids': [v.id for v in vectors]
        }

    def get_file_modification_time(self, file_path: str) -> Optional[datetime]:
        """Get file modification time from filesystem."""
        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                return datetime.fromtimestamp(file_path_obj.stat().st_mtime)
        except Exception:
            pass
        return None

    def delete_file_vectors(self, collection_id: int, file_path: str) -> int:
        """Delete all vectors associated with a specific file."""
        file_path_obj = Path(file_path).resolve()
        file_path_str = str(file_path_obj)
        file_name = file_path_obj.name
        
        # Delete vectors from this file
        deleted_count = self.session.query(VectorRecord).filter(
            VectorRecord.collection_id == collection_id
        ).filter(
            text("(extra_metadata->>'file_path' = :file_path_exact OR "
                 "extra_metadata->>'file_path' = :file_path_abs OR "
                 "extra_metadata->>'file_name' = :file_name)")
        ).params(
            file_path_exact=file_path,
            file_path_abs=file_path_str,
            file_name=file_name
        ).delete(synchronize_session='fetch')
        
        self.session.commit()
        return deleted_count

    def delete_vectors_by_date_range(self, collection_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """Delete vectors within a date range."""
        # Parse date strings
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            # If end_date doesn't include time, make it end of day
            if ' ' not in end_date and 'T' not in end_date:
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD or ISO format: {e}")
        
        if start_dt > end_dt:
            raise ValueError("start_date must be before or equal to end_date")
        
        # Get vectors to delete
        vectors_to_delete = self.session.query(VectorRecord).filter(
            and_(
                VectorRecord.collection_id == collection_id,
                VectorRecord.created_at >= start_dt,
                VectorRecord.created_at <= end_dt
            )
        ).all()
        
        if not vectors_to_delete:
            return {
                'deleted_count': 0,
                'date_range': {'start': start_date, 'end': end_date},
                'message': 'No vectors found in the specified date range'
            }
        
        # Collect statistics before deletion
        file_stats = {}
        for vector in vectors_to_delete:
            file_path = vector.extra_metadata.get('file_path')
            if file_path:
                file_stats[file_path] = file_stats.get(file_path, 0) + 1
        
        # Delete vectors
        deleted_count = self.session.query(VectorRecord).filter(
            and_(
                VectorRecord.collection_id == collection_id,
                VectorRecord.created_at >= start_dt,
                VectorRecord.created_at <= end_dt
            )
        ).delete(synchronize_session='fetch')
        
        self.session.commit()
        
        return {
            'deleted_count': deleted_count,
            'date_range': {'start': start_date, 'end': end_date},
            'files_affected': file_stats,
            'message': f'Successfully deleted {deleted_count} vectors from date range {start_date} to {end_date}'
        }

    def preview_delete_vectors_by_date_range(self, collection_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """Preview vectors that would be deleted within a date range."""
        # Parse date strings
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            # If end_date doesn't include time, make it end of day
            if ' ' not in end_date and 'T' not in end_date:
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD or ISO format: {e}")
        
        if start_dt > end_dt:
            raise ValueError("start_date must be before or equal to end_date")
        
        # Get vectors that would be deleted
        vectors_to_delete = self.session.query(VectorRecord).filter(
            and_(
                VectorRecord.collection_id == collection_id,
                VectorRecord.created_at >= start_dt,
                VectorRecord.created_at <= end_dt
            )
        ).all()
        
        # Collect statistics
        file_stats = {}
        vector_details = []
        
        for vector in vectors_to_delete:
            file_path = vector.extra_metadata.get('file_path', 'manual_text')
            file_stats[file_path] = file_stats.get(file_path, 0) + 1
            
            vector_details.append({
                'id': vector.id,
                'content_preview': vector.content[:100] + '...' if len(vector.content) > 100 else vector.content,
                'file_path': file_path,
                'created_at': vector.created_at.isoformat()
            })
        
        return {
            'preview': True,
            'vectors_to_delete': len(vectors_to_delete),
            'date_range': {'start': start_date, 'end': end_date},
            'files_affected': file_stats,
            'vector_details': vector_details,
            'message': f'Would delete {len(vectors_to_delete)} vectors from date range {start_date} to {end_date}'
        }

    def preview_delete_vectors_by_file(self, collection_id: int, file_path: str) -> Dict[str, Any]:
        """Preview vectors that would be deleted for a specific file."""
        file_path_obj = Path(file_path).resolve()
        file_path_str = str(file_path_obj)
        file_name = file_path_obj.name
        
        # Get vectors that would be deleted
        vectors_to_delete = self.session.query(VectorRecord).filter(
            VectorRecord.collection_id == collection_id
        ).filter(
            text("(extra_metadata->>'file_path' = :file_path_exact OR "
                 "extra_metadata->>'file_path' = :file_path_abs OR "
                 "extra_metadata->>'file_name' = :file_name)")
        ).params(
            file_path_exact=file_path,
            file_path_abs=file_path_str,
            file_name=file_name
        ).all()
        
        if not vectors_to_delete:
            return {
                'preview': True,
                'vectors_to_delete': 0,
                'file_path': file_path,
                'message': f'No vectors found for file: {file_path}'
            }
        
        # Collect statistics
        vector_details = []
        first_added = min(v.created_at for v in vectors_to_delete)
        last_added = max(v.created_at for v in vectors_to_delete)
        
        for vector in vectors_to_delete:
            vector_details.append({
                'id': vector.id,
                'content_preview': vector.content[:100] + '...' if len(vector.content) > 100 else vector.content,
                'created_at': vector.created_at.isoformat()
            })
        
        return {
            'preview': True,
            'vectors_to_delete': len(vectors_to_delete),
            'file_path': file_path,
            'file_info': {
                'first_added': first_added.isoformat(),
                'last_added': last_added.isoformat(),
                'stored_file_path': vectors_to_delete[0].extra_metadata.get('file_path')
            },
            'vector_details': vector_details,
            'message': f'Would delete {len(vectors_to_delete)} vectors from file: {file_path}'
        }
