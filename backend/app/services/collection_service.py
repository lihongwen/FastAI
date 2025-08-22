from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models.collection import Collection
from ..schemas import CollectionCreate, CollectionUpdate
from typing import List, Optional

class CollectionService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_collections(self) -> List[Collection]:
        return self.db.query(Collection).filter(Collection.is_active == True).all()
    
    def get_collection(self, collection_id: int) -> Optional[Collection]:
        return self.db.query(Collection).filter(
            Collection.id == collection_id,
            Collection.is_active == True
        ).first()
    
    def get_collection_by_name(self, name: str) -> Optional[Collection]:
        return self.db.query(Collection).filter(
            Collection.name == name,
            Collection.is_active == True
        ).first()
    
    def create_collection(self, collection: CollectionCreate) -> Collection:
        # Check if collection name already exists
        existing = self.get_collection_by_name(collection.name)
        if existing:
            raise ValueError(f"Collection with name '{collection.name}' already exists")
        
        # Create the collection record
        db_collection = Collection(**collection.dict())
        self.db.add(db_collection)
        self.db.commit()
        self.db.refresh(db_collection)
        
        # Create the actual vector table for this collection
        self._create_vector_table(db_collection.name, db_collection.dimension)
        
        return db_collection
    
    def update_collection(self, collection_id: int, collection_update: CollectionUpdate) -> Optional[Collection]:
        db_collection = self.get_collection(collection_id)
        if not db_collection:
            return None
        
        # If name is being changed, rename the vector table
        old_name = db_collection.name
        update_data = collection_update.dict(exclude_unset=True)
        
        if "name" in update_data and update_data["name"] != old_name:
            new_name = update_data["name"]
            # Check if new name already exists
            existing = self.get_collection_by_name(new_name)
            if existing and existing.id != collection_id:
                raise ValueError(f"Collection with name '{new_name}' already exists")
            
            # Rename the vector table
            self._rename_vector_table(old_name, new_name)
        
        # Update the collection record
        for field, value in update_data.items():
            setattr(db_collection, field, value)
        
        self.db.commit()
        self.db.refresh(db_collection)
        
        return db_collection
    
    def delete_collection(self, collection_id: int) -> bool:
        db_collection = self.get_collection(collection_id)
        if not db_collection:
            return False
        
        # Drop the vector table
        self._drop_vector_table(db_collection.name)
        
        # Soft delete the collection record
        db_collection.is_active = False
        self.db.commit()
        
        return True
    
    def _create_vector_table(self, collection_name: str, dimension: int):
        """Create a vector table for the collection"""
        table_name = f"vectors_{collection_name.lower().replace(' ', '_')}"
        
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
        
        self.db.execute(create_table_sql)
        self.db.execute(create_index_sql)
        self.db.commit()
    
    def _rename_vector_table(self, old_name: str, new_name: str):
        """Rename a vector table"""
        old_table = f"vectors_{old_name.lower().replace(' ', '_')}"
        new_table = f"vectors_{new_name.lower().replace(' ', '_')}"
        
        rename_sql = text(f"ALTER TABLE {old_table} RENAME TO {new_table}")
        self.db.execute(rename_sql)
        self.db.commit()
    
    def _drop_vector_table(self, collection_name: str):
        """Drop a vector table"""
        table_name = f"vectors_{collection_name.lower().replace(' ', '_')}"
        
        drop_sql = text(f"DROP TABLE IF EXISTS {table_name}")
        self.db.execute(drop_sql)
        self.db.commit()