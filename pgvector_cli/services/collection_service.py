"""Collection service for pgvector CLI."""

import re
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..exceptions import CollectionError, DatabaseError
from ..logging_config import StructuredLogger
from ..models.collection import Collection

logger = StructuredLogger("collection_service")

class CollectionService:
    """Service for managing collections."""

    def __init__(self, session: Session):
        self.session = session

    def get_collections(self) -> List[Collection]:
        """Get all active collections."""
        try:
            collections = self.session.query(Collection).filter(Collection.is_active).all()
            logger.debug("Retrieved collections", count=len(collections))
            return collections
        except SQLAlchemyError as e:
            logger.error("Failed to retrieve collections", error=str(e))
            raise DatabaseError(f"Failed to retrieve collections: {e}") from e

    def get_collection(self, collection_id: int) -> Optional[Collection]:
        """Get collection by ID."""
        return self.session.query(Collection).filter(
            Collection.id == collection_id,
            Collection.is_active
        ).first()

    def get_collection_by_name(self, name: str) -> Optional[Collection]:
        """Get collection by name."""
        return self.session.query(Collection).filter(
            Collection.name == name,
            Collection.is_active
        ).first()

    def create_collection(self, name: str, dimension: int = 1024, description: Optional[str] = None) -> Collection:
        """Create a new collection."""
        try:
            # Check if collection name already exists
            existing = self.get_collection_by_name(name)
            if existing:
                logger.warning("Attempt to create duplicate collection", name=name)
                raise CollectionError(f"Collection with name '{name}' already exists", code="DUPLICATE_NAME")

            # Create the collection record
            collection = Collection(
                name=name,
                description=description,
                dimension=dimension
            )
            self.session.add(collection)
            self.session.commit()
            self.session.refresh(collection)

            logger.info("Created collection record", name=name, id=collection.id, dimension=dimension)

            # Create the actual vector table for this collection
            self._create_vector_table(collection.name, collection.dimension)

            logger.info("Successfully created collection", name=name, id=collection.id)
            return collection

        except CollectionError:
            # Re-raise collection-specific errors
            raise
        except IntegrityError as e:
            self.session.rollback()
            logger.error("Database integrity error creating collection", name=name, error=str(e))
            raise CollectionError(f"Failed to create collection '{name}': integrity constraint violation") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error("Database error creating collection", name=name, error=str(e))
            raise DatabaseError(f"Failed to create collection '{name}': {e}") from e
        except Exception as e:
            self.session.rollback()
            logger.error("Unexpected error creating collection", name=name, error=str(e))
            raise CollectionError(f"Failed to create collection '{name}': {e}") from e

    def update_collection(self, collection_id: int, name: Optional[str] = None,
                         description: Optional[str] = None) -> Optional[Collection]:
        """Update collection."""
        collection = self.get_collection(collection_id)
        if not collection:
            return None

        # If name is being changed, rename the vector table
        old_name = collection.name

        if name and name != old_name:
            # Check if new name already exists
            existing = self.get_collection_by_name(name)
            if existing and existing.id != collection_id:
                raise ValueError(f"Collection with name '{name}' already exists")

            # Rename the vector table
            self._rename_vector_table(old_name, name)
            collection.name = name

        if description is not None:
            collection.description = description

        self.session.commit()
        self.session.refresh(collection)

        return collection

    def delete_collection(self, collection_id: int) -> bool:
        """Delete collection (soft delete)."""
        from sqlalchemy.sql import func

        collection = self.get_collection(collection_id)
        if not collection:
            return False

        # Drop the vector table
        self._drop_vector_table(collection.name)

        # Soft delete the collection record
        collection.is_active = False
        collection.deleted_at = func.now()
        self.session.commit()

        return True

    def rebuild_collection_index(self, collection_id: int) -> bool:
        """Rebuild collection HNSW index to improve search performance"""
        collection = self.get_collection(collection_id)
        if not collection:
            return False

        table_name = self._safe_table_name(collection.name)
        index_name = f"{table_name}_vector_hnsw_idx"

        try:
            # Drop existing index
            drop_index_sql = text(f"DROP INDEX IF EXISTS {index_name}")
            self.session.execute(drop_index_sql)

            # Recreate optimized HNSW index
            create_index_sql = text(f"""
                CREATE INDEX {index_name} 
                ON {table_name} USING hnsw (vector vector_cosine_ops) 
                WITH (m = 16, ef_construction = 64)
            """)

            self.session.execute(create_index_sql)
            self.session.commit()

            logger.info(f"Successfully rebuilt HNSW index for collection {collection.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            self.session.rollback()
            return False

    def get_collection_index_info(self, collection_id: int) -> dict:
        """Get collection index information"""
        collection = self.get_collection(collection_id)
        if not collection:
            return {}

        table_name = self._safe_table_name(collection.name)

        # Query index information using parameterized query
        index_query = text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = :table_name 
            AND indexname LIKE '%vector%'
        """)

        result = self.session.execute(index_query, {"table_name": table_name}).fetchall()

        index_info = {
            "collection_name": collection.name,
            "table_name": table_name,
            "indexes": []
        }

        for row in result:
            index_info["indexes"].append({
                "name": row[0],
                "definition": row[1]
            })

        return index_info

    def get_collection_performance_stats(self, collection_id: int) -> dict:
        """Get collection performance statistics"""
        collection = self.get_collection(collection_id)
        if not collection:
            return {}

        table_name = self._safe_table_name(collection.name)

        try:
            # Get table statistics using parameterized query
            stats_query = text("""
                SELECT 
                    relname as table_name,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables 
                WHERE relname = :table_name
            """)

            table_stats = self.session.execute(stats_query, {"table_name": table_name}).fetchone()

            # Get index statistics using parameterized query
            index_stats_query = text("""
                SELECT 
                    indexrelname as index_name,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched,
                    idx_blks_read as blocks_read,
                    idx_blks_hit as blocks_hit
                FROM pg_stat_user_indexes 
                WHERE relname = :table_name 
                AND indexrelname LIKE '%vector%'
            """)

            index_stats = self.session.execute(index_stats_query, {"table_name": table_name}).fetchall()

            # 计算缓存命中率
            cache_hit_ratio = 0.0
            if index_stats:
                for idx_stat in index_stats:
                    total_reads = idx_stat[3] + idx_stat[4]  # blocks_read + blocks_hit
                    if total_reads > 0:
                        cache_hit_ratio = idx_stat[4] / total_reads * 100  # blocks_hit / total_reads
                        break

            performance_stats = {
                "collection_name": collection.name,
                "table_stats": {
                    "live_tuples": table_stats[4] if table_stats else 0,
                    "dead_tuples": table_stats[5] if table_stats else 0,
                    "total_operations": {
                        "inserts": table_stats[1] if table_stats else 0,
                        "updates": table_stats[2] if table_stats else 0,
                        "deletes": table_stats[3] if table_stats else 0
                    }
                },
                "index_performance": {
                    "cache_hit_ratio_percent": round(cache_hit_ratio, 2),
                    "indexes": []
                }
            }

            for idx_stat in index_stats:
                performance_stats["index_performance"]["indexes"].append({
                    "name": idx_stat[0],
                    "tuples_read": idx_stat[1],
                    "tuples_fetched": idx_stat[2],
                    "blocks_read": idx_stat[3],
                    "blocks_hit": idx_stat[4]
                })

            return performance_stats

        except Exception as e:
            logger.error(f"获取性能统计失败: {e}")
            return {
                "collection_name": collection.name,
                "error": str(e)
            }

    def _safe_table_name(self, collection_name: str) -> str:
        """Generate a safe table name from collection name."""
        import hashlib

        # For names with only ASCII alphanumeric and underscore, use as-is
        if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', collection_name):
            return f"vectors_{collection_name.lower()}"

        # For names with Unicode/special chars, create a hash-based safe name
        # Keep first few ASCII chars if available, then add hash
        ascii_part = re.sub(r'[^a-zA-Z0-9]', '', collection_name)[:10]

        # Create a short hash of the full collection name for uniqueness
        name_hash = hashlib.md5(collection_name.encode('utf-8')).hexdigest()[:8]

        # Combine ASCII part (if any) with hash
        if ascii_part and ascii_part[0].isalpha():
            safe_name = f"{ascii_part}_{name_hash}"
        else:
            safe_name = f"col_{name_hash}"

        return f"vectors_{safe_name.lower()}"

    def _create_vector_table(self, collection_name: str, dimension: int):
        """Create a vector table for the collection."""
        table_name = self._safe_table_name(collection_name)
        index_name = f"{table_name}_vector_hnsw_idx"

        # Use format with validated safe names (already sanitized by _safe_table_name)
        create_table_sql = text(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                vector vector({dimension}),
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # Create HNSW index for better search performance and accuracy
        # Using cosine distance, suitable for 1024-dim document search
        # m=16, ef_construction=64 optimized parameters
        create_index_sql = text(f"""
            CREATE INDEX IF NOT EXISTS {index_name} 
            ON {table_name} USING hnsw (vector vector_cosine_ops) 
            WITH (m = 16, ef_construction = 64)
        """)

        self.session.execute(create_table_sql)
        self.session.execute(create_index_sql)
        self.session.commit()

    def _rename_vector_table(self, old_name: str, new_name: str):
        """Rename a vector table."""
        old_table = self._safe_table_name(old_name)
        new_table = self._safe_table_name(new_name)

        rename_sql = text(f"ALTER TABLE {old_table} RENAME TO {new_table}")
        self.session.execute(rename_sql)
        self.session.commit()

    def _drop_vector_table(self, collection_name: str):
        """Drop a vector table."""
        table_name = self._safe_table_name(collection_name)

        drop_sql = text(f"DROP TABLE IF EXISTS {table_name}")
        self.session.execute(drop_sql)
        self.session.commit()
