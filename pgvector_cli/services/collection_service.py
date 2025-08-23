"""Collection service for pgvector CLI."""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional

from ..models.collection import Collection

class CollectionService:
    """Service for managing collections."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_collections(self) -> List[Collection]:
        """Get all active collections."""
        return self.session.query(Collection).filter(Collection.is_active == True).all()
    
    def get_collection(self, collection_id: int) -> Optional[Collection]:
        """Get collection by ID."""
        return self.session.query(Collection).filter(
            Collection.id == collection_id,
            Collection.is_active == True
        ).first()
    
    def get_collection_by_name(self, name: str) -> Optional[Collection]:
        """Get collection by name."""
        return self.session.query(Collection).filter(
            Collection.name == name,
            Collection.is_active == True
        ).first()
    
    def create_collection(self, name: str, dimension: int = 1024, description: Optional[str] = None) -> Collection:
        """Create a new collection."""
        # Check if collection name already exists
        existing = self.get_collection_by_name(name)
        if existing:
            raise ValueError(f"Collection with name '{name}' already exists")
        
        # Create the collection record
        collection = Collection(
            name=name,
            description=description,
            dimension=dimension
        )
        self.session.add(collection)
        self.session.commit()
        self.session.refresh(collection)
        
        # Create the actual vector table for this collection
        self._create_vector_table(collection.name, collection.dimension)
        
        return collection
    
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
        collection = self.get_collection(collection_id)
        if not collection:
            return False
        
        # Drop the vector table
        self._drop_vector_table(collection.name)
        
        # Soft delete the collection record
        collection.is_active = False
        self.session.commit()
        
        return True
    
    def _create_vector_table(self, collection_name: str, dimension: int):
        """Create a vector table for the collection."""
        table_name = f"vectors_{collection_name.lower().replace(' ', '_').replace('-', '_')}"
        
        create_table_sql = text(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                vector vector({dimension}),
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        create_index_sql = text(f"""
            CREATE INDEX IF NOT EXISTS {table_name}_vector_idx 
            ON {table_name} USING ivfflat (vector vector_cosine_ops) 
            WITH (lists = 100)
        """)
        
        self.session.execute(create_table_sql)
        self.session.execute(create_index_sql)
        self.session.commit()
    
    def _rename_vector_table(self, old_name: str, new_name: str):
        """Rename a vector table."""
        old_table = f"vectors_{old_name.lower().replace(' ', '_').replace('-', '_')}"
        new_table = f"vectors_{new_name.lower().replace(' ', '_').replace('-', '_')}"
        
        rename_sql = text(f"ALTER TABLE {old_table} RENAME TO {new_table}")
        self.session.execute(rename_sql)
        self.session.commit()
    
    def _drop_vector_table(self, collection_name: str):
        """Drop a vector table."""
        table_name = f"vectors_{collection_name.lower().replace(' ', '_').replace('-', '_')}"
        
        drop_sql = text(f"DROP TABLE IF EXISTS {table_name}")
        self.session.execute(drop_sql)
        self.session.commit()