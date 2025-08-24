"""Cleanup service for automatic hard deletion of expired collections."""

import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from ..models.collection import Collection
from ..models.vector_record import VectorRecord

logger = logging.getLogger(__name__)

class CleanupService:
    """Service for cleaning up expired soft-deleted collections."""

    def __init__(self, session: Session, retention_days: int = 30):
        self.session = session
        self.retention_days = retention_days

    def get_expired_collections(self) -> List[Collection]:
        """Get collections that are expired and ready for hard deletion."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)

        return self.session.query(Collection).filter(
            ~Collection.is_active,
            Collection.deleted_at.isnot(None),
            Collection.deleted_at < cutoff_date
        ).all()

    def hard_delete_collection(self, collection: Collection) -> bool:
        """Permanently delete a collection and all its data."""
        try:
            # Delete associated vector records
            self.session.query(VectorRecord).filter(
                VectorRecord.collection_id == collection.id
            ).delete()

            # Delete the collection record
            self.session.delete(collection)
            self.session.commit()

            logger.info(f"Hard deleted collection: {collection.name} (ID: {collection.id})")
            return True

        except Exception as e:
            logger.error(f"Failed to hard delete collection {collection.name}: {e}")
            self.session.rollback()
            return False

    def cleanup_expired_collections(self) -> dict:
        """Clean up all expired collections and return cleanup summary."""
        expired_collections = self.get_expired_collections()

        cleanup_result = {
            "total_found": len(expired_collections),
            "successfully_deleted": 0,
            "failed_deletions": 0,
            "deleted_collections": []
        }

        for collection in expired_collections:
            if self.hard_delete_collection(collection):
                cleanup_result["successfully_deleted"] += 1
                cleanup_result["deleted_collections"].append({
                    "name": collection.name,
                    "id": collection.id,
                    "deleted_at": collection.deleted_at.isoformat() if collection.deleted_at else None
                })
            else:
                cleanup_result["failed_deletions"] += 1

        if cleanup_result["successfully_deleted"] > 0:
            logger.info(f"Cleanup completed: {cleanup_result['successfully_deleted']} collections hard deleted")

        return cleanup_result

    def auto_cleanup(self) -> dict:
        """Perform automatic cleanup if there are expired collections."""
        return self.cleanup_expired_collections()
