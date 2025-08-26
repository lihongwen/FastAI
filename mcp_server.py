#!/usr/bin/env python3
"""
MCP Server for pgvector Collection Management

Model Context Protocol server that provides tools for managing PostgreSQL collections
with pgvector extension. Supports collection management, document processing, and
vector search operations.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, Tool

# Ensure cross-platform compatibility
if sys.platform.startswith('win'):
    # Windows-specific configurations
    import pathlib
    pathlib.PosixPath = pathlib.WindowsPath

from pgvector_cli.config import get_settings
from pgvector_cli.database import get_db_session
from pgvector_cli.services import CollectionService, VectorService, DocumentService, EmbeddingService
# Note: LLMService removed - AI summarization is now handled by the LLM client itself
from pgvector_cli.utils import validate_collection_name, validate_dimension
from pgvector_cli.exceptions import CollectionError, DatabaseError, PgvectorCLIError

# Initialize FastMCP server
mcp = FastMCP("pgvector-mcp-server")

@mcp.tool()
def status() -> Dict[str, Any]:
    """
    Check system status and database connectivity.
    
    Returns:
        Dictionary with comprehensive status information including database 
        connection, pgvector extension, embedding service, and system info.
    """
    import datetime
    import platform
    from sqlalchemy import text
    
    status_info = {
        "timestamp": datetime.datetime.now().isoformat(),
        "success": True,
        "database": {},
        "embedding_service": {},
        "collections": {},
        "system": {}
    }
    
    # Check database connection and pgvector extension
    try:
        with get_db_session() as session:
            # Basic connection test
            session.execute(text("SELECT 1"))
            status_info["database"]["connected"] = True
            
            # Get database URL (mask password)
            settings = get_settings()
            db_url = settings.database_url
            if "@" in db_url:
                # Mask password in URL for security
                parts = db_url.split("@")
                user_pass = parts[0].split("://")[1]
                if ":" in user_pass:
                    user = user_pass.split(":")[0]
                    masked_url = db_url.replace(user_pass, f"{user}:***")
                    status_info["database"]["url"] = masked_url
                else:
                    status_info["database"]["url"] = db_url
            else:
                status_info["database"]["url"] = db_url
            
            # Check pgvector extension
            try:
                result = session.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")).first()
                if result:
                    status_info["database"]["pgvector_installed"] = True
                    status_info["database"]["pgvector_version"] = result[1]
                else:
                    status_info["database"]["pgvector_installed"] = False
                    status_info["database"]["pgvector_version"] = None
            except Exception as e:
                status_info["database"]["pgvector_error"] = str(e)
                status_info["database"]["pgvector_installed"] = False
            
            # Get collection statistics
            try:
                collection_service = CollectionService(session)
                vector_service = VectorService(session)
                collections = collection_service.get_collections()
                
                total_vectors = 0
                for collection in collections:
                    total_vectors += vector_service.get_vector_count(collection.id)
                
                status_info["collections"] = {
                    "total": len(collections),
                    "total_vectors": total_vectors
                }
            except Exception as e:
                status_info["collections"]["error"] = str(e)
                
    except Exception as e:
        status_info["success"] = False
        status_info["database"]["connected"] = False
        status_info["database"]["error"] = str(e)
    
    # Check embedding service
    try:
        embedding_service = EmbeddingService()
        
        # Check if API key is configured
        dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        if dashscope_key and dashscope_key != "your_api_key_here":
            status_info["embedding_service"]["api_key_configured"] = True
            status_info["embedding_service"]["provider"] = "DashScope"
            
            # Test embedding service with a simple query
            try:
                test_embedding = embedding_service.embed_text("test")
                if test_embedding and len(test_embedding) > 0:
                    status_info["embedding_service"]["available"] = True
                    status_info["embedding_service"]["dimension"] = len(test_embedding)
                else:
                    status_info["embedding_service"]["available"] = False
            except Exception as e:
                status_info["embedding_service"]["available"] = False
                status_info["embedding_service"]["error"] = str(e)
        else:
            status_info["embedding_service"]["api_key_configured"] = False
            status_info["embedding_service"]["available"] = False
            status_info["embedding_service"]["message"] = "DASHSCOPE_API_KEY not configured"
            
    except Exception as e:
        status_info["embedding_service"]["error"] = str(e)
        status_info["embedding_service"]["available"] = False
    
    # System information
    try:
        import mcp
        import sqlalchemy
        import pgvector
        
        status_info["system"] = {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "platform_version": platform.release(),
            "mcp_version": getattr(mcp, '__version__', 'unknown'),
            "sqlalchemy_version": sqlalchemy.__version__,
            "pgvector_version": getattr(pgvector, '__version__', 'unknown'),
            "working_directory": str(Path.cwd())
        }
    except Exception as e:
        status_info["system"]["error"] = str(e)
    
    return status_info

@mcp.tool()
def create_collection(name: str, description: str = "", dimension: int = 1024) -> Dict[str, Any]:
    """
    Create a new vector collection.
    
    Args:
        name: Unique name for the collection
        description: Optional description of the collection
        dimension: Vector dimension (fixed at 1024)
    
    Returns:
        Dictionary with collection details
    """
    try:
        # Validate inputs
        validate_collection_name(name)
        validate_dimension(dimension)
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            
            # Check if collection already exists
            existing = collection_service.get_collection_by_name(name)
            if existing:
                raise CollectionError(f"Collection '{name}' already exists")
            
            # Create new collection
            collection = collection_service.create_collection(name, dimension, description)
            
            return {
                "success": True,
                "collection": {
                    "id": collection.id,
                    "name": collection.name,
                    "description": collection.description,
                    "dimension": collection.dimension,
                    "created_at": collection.created_at.isoformat(),
                    "total_vectors": 0
                }
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def list_collections() -> Dict[str, Any]:
    """
    List all active collections.
    
    Returns:
        Dictionary with list of collections
    """
    try:
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            
            collections = collection_service.get_collections()
            result = []
            
            for collection in collections:
                # Get vector count for each collection
                vector_count = vector_service.get_vector_count(collection.id)
                
                result.append({
                    "id": collection.id,
                    "name": collection.name,
                    "description": collection.description,
                    "dimension": collection.dimension,
                    "created_at": collection.created_at.isoformat() if collection.created_at else None,
                    "updated_at": collection.updated_at.isoformat() if collection.updated_at else None,
                    "total_vectors": vector_count
                })
            
            return {
                "success": True,
                "collections": result,
                "total": len(result)
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def show_collection(name: str, include_stats: bool = True) -> Dict[str, Any]:
    """
    Show details for a specific collection.
    
    Args:
        name: Name of the collection
        include_stats: Whether to include statistics
    
    Returns:
        Dictionary with collection details and statistics
    """
    try:
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            
            collection = collection_service.get_collection_by_name(name)
            if not collection:
                return {"success": False, "error": f"Collection '{name}' not found"}
            
            result = {
                "id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "dimension": collection.dimension,
                "created_at": collection.created_at.isoformat() if collection.created_at else None,
                "updated_at": collection.updated_at.isoformat() if collection.updated_at else None
            }
            
            if include_stats:
                vector_count = vector_service.get_vector_count(collection.id)
                result["statistics"] = {
                    "total_vectors": vector_count,
                    "table_name": f"vectors_{collection.name}"
                }
            
            return {"success": True, "collection": result}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def delete_collection(name: str, confirm: bool = False) -> Dict[str, Any]:
    """
    Delete a collection and all its vectors.
    
    Args:
        name: Name of the collection to delete
        confirm: Confirmation flag (required for safety)
    
    Returns:
        Dictionary with deletion result
    """
    try:
        if not confirm:
            return {
                "success": False, 
                "error": "Deletion requires confirmation. Set confirm=True to proceed."
            }
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            
            collection = collection_service.get_collection_by_name(name)
            if not collection:
                return {"success": False, "error": f"Collection '{name}' not found"}
            
            # Delete collection (soft delete with cleanup)
            collection_service.delete_collection(collection.id)
            
            return {
                "success": True,
                "message": f"Collection '{name}' has been deleted"
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def add_text(collection_name: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add text content to a collection as a vector.
    
    Args:
        collection_name: Name of the target collection
        text: Text content to vectorize and add
        metadata: Optional metadata dictionary
    
    Returns:
        Dictionary with the created vector record details
    """
    try:
        if not text.strip():
            return {"success": False, "error": "Text content cannot be empty"}
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            
            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                return {"success": False, "error": f"Collection '{collection_name}' not found"}
            
            # Create vector record
            vector_record = vector_service.create_vector_record(
                collection.id, text, metadata or {}
            )
            
            return {
                "success": True,
                "vector": {
                    "id": vector_record.id,
                    "content": vector_record.content,
                    "metadata": vector_record.extra_metadata,
                    "created_at": vector_record.created_at.isoformat()
                }
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def search_collection(
    collection_name: str, 
    query: str, 
    limit: int = 10,
    min_similarity: float = 0.0
) -> Dict[str, Any]:
    """
    Search for similar vectors in a collection.
    
    Args:
        collection_name: Name of the collection to search
        query: Search query text
        limit: Maximum number of results (default: 10)
        min_similarity: Minimum similarity threshold (default: 0.0)
    
    Returns:
        Dictionary with search results
    """
    try:
        if not query.strip():
            return {"success": False, "error": "Query cannot be empty"}
        
        if limit <= 0 or limit > 100:
            return {"success": False, "error": "Limit must be between 1 and 100"}
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            
            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                return {"success": False, "error": f"Collection '{collection_name}' not found"}
            
            # Perform vector search
            results = vector_service.search_vectors(collection.id, query, limit)
            
            # Filter by similarity threshold and format results
            filtered_results = []
            for vector_record, similarity in results:
                if similarity >= min_similarity:
                    filtered_results.append({
                        "id": vector_record.id,
                        "content": vector_record.content,
                        "metadata": vector_record.extra_metadata,
                        "similarity_score": float(similarity),
                        "created_at": vector_record.created_at.isoformat()
                    })
            
            return {
                "success": True,
                "query": query,
                "collection": collection_name,
                "total_results": len(filtered_results),
                "results": filtered_results
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def add_document(
    collection_name: str, 
    file_path: str, 
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a document file and add its contents to a collection.
    
    Args:
        collection_name: Name of the target collection
        file_path: Path to the document file (PDF, CSV, TXT, etc.)
        metadata: Optional metadata dictionary
    
    Returns:
        Dictionary with processing results
    """
    try:
        # Ensure cross-platform path handling
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            document_service = DocumentService()  # DocumentService doesn't need session
            
            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                return {"success": False, "error": f"Collection '{collection_name}' not found"}
            
            # Process document with default chunking parameters
            chunks = document_service.process_document(
                str(file_path), chunk_size=500, overlap=100
            )
            
            if not chunks:
                return {"success": False, "error": "No content extracted from document"}
            
            # Create vector records from chunks
            results = []
            for chunk in chunks:
                # Merge chunk metadata with user metadata
                combined_metadata = {**chunk.metadata, **(metadata or {})}
                
                vector_record = vector_service.create_vector_record(
                    collection.id, chunk.content, combined_metadata
                )
                results.append(vector_record)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "collection": collection_name,
                "vectors_created": len(results),
                "vectors": [
                    {
                        "id": record.id,
                        "content_preview": record.content[:200] + "..." if len(record.content) > 200 else record.content,
                        "metadata": record.extra_metadata,
                        "created_at": record.created_at.isoformat()
                    }
                    for record in results
                ]
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def delete_vectors(
    collection_name: str,
    file_path: Optional[str] = None,
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    preview_only: bool = False,
    confirm: bool = False
) -> Dict[str, Any]:
    """
    Delete vectors from a collection with flexible filtering options.
    
    Args:
        collection_name: Name of the target collection
        file_path: Delete all vectors from a specific file (optional)
        start_date: Start date for date range deletion in YYYY-MM-DD format (optional) 
        end_date: End date for date range deletion in YYYY-MM-DD format (optional)
        preview_only: Only preview what would be deleted, don't actually delete
        confirm: Required confirmation for actual deletion (ignored if preview_only=True)
    
    Returns:
        Dictionary with deletion results or preview information
    """
    try:
        # Parameter validation
        if not file_path and not (start_date and end_date):
            return {
                "success": False, 
                "error": "Must specify either file_path or both start_date and end_date"
            }
        
        if file_path and (start_date or end_date):
            return {
                "success": False,
                "error": "Cannot specify both file_path and date range. Choose one deletion method."
            }
        
        if start_date and not end_date:
            return {
                "success": False,
                "error": "Both start_date and end_date are required for date range deletion"
            }
        
        if not preview_only and not confirm:
            return {
                "success": False,
                "error": "Deletion requires confirmation. Set confirm=True or use preview_only=True to preview first."
            }
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            
            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                return {"success": False, "error": f"Collection '{collection_name}' not found"}
            
            # Build query conditions
            from sqlalchemy import text, and_
            from pgvector_cli.models.vector_record import VectorRecord
            
            conditions = [VectorRecord.collection_id == collection.id]
            deletion_method = ""
            deletion_criteria = {}
            
            if file_path:
                # Delete by file path - try both absolute and relative paths
                file_path_input = str(file_path)
                file_path_abs = str(Path(file_path_input).resolve())
                file_name = Path(file_path_input).name
                
                # Use OR condition to match file_path, absolute path, or file name
                conditions.append(
                    text("(extra_metadata->>'file_path' = :file_path_exact OR extra_metadata->>'file_path' = :file_path_abs OR extra_metadata->>'file_name' = :file_name)")
                )
                deletion_method = "file_path"
                deletion_criteria = {
                    "file_path": file_path_input,
                    "file_path_abs": file_path_abs,
                    "file_name": file_name
                }
                
            elif start_date and end_date:
                # Delete by date range
                import datetime
                try:
                    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
                    
                    conditions.append(and_(
                        VectorRecord.created_at >= start_dt,
                        VectorRecord.created_at < end_dt
                    ))
                    deletion_method = "date_range"
                    deletion_criteria = {"start_date": start_date, "end_date": end_date}
                    
                except ValueError:
                    return {
                        "success": False,
                        "error": "Invalid date format. Use YYYY-MM-DD format (e.g., '2025-08-25')"
                    }
            
            # Execute query to find matching vectors
            if deletion_method == "file_path":
                # For file path queries, use raw SQL with parameters
                query = session.query(VectorRecord).filter(
                    VectorRecord.collection_id == collection.id
                ).filter(
                    text("(extra_metadata->>'file_path' = :file_path_exact OR extra_metadata->>'file_path' = :file_path_abs OR extra_metadata->>'file_name' = :file_name)")
                ).params(
                    file_path_exact=file_path_input,
                    file_path_abs=file_path_abs, 
                    file_name=file_name
                )
            else:
                # For date range queries, use standard SQLAlchemy
                query = session.query(VectorRecord).filter(and_(*conditions))
            
            matching_vectors = query.all()
            
            if not matching_vectors:
                return {
                    "success": True,
                    "message": "No vectors found matching the specified criteria",
                    "deletion_method": deletion_method,
                    "criteria": deletion_criteria,
                    "matched_count": 0
                }
            
            # Preview mode - return information without deleting
            if preview_only:
                preview_samples = []
                for vector in matching_vectors[:3]:  # Show up to 3 samples
                    preview_samples.append({
                        "id": vector.id,
                        "content_preview": vector.content[:100] + "..." if len(vector.content) > 100 else vector.content,
                        "created_at": vector.created_at.isoformat() if vector.created_at else None,
                        "file_info": {
                            "file_name": vector.extra_metadata.get("file_name"),
                            "file_path": vector.extra_metadata.get("file_path"),
                            "source": vector.extra_metadata.get("source")
                        }
                    })
                
                return {
                    "success": True,
                    "preview": True,
                    "deletion_method": deletion_method,
                    "criteria": deletion_criteria,
                    "matched_count": len(matching_vectors),
                    "preview_samples": preview_samples,
                    "message": f"Preview: {len(matching_vectors)} vectors would be deleted. Use confirm=True to proceed with deletion."
                }
            
            # Actual deletion
            deleted_ids = [vector.id for vector in matching_vectors]
            
            # Perform deletion
            deleted_count = query.delete(synchronize_session='fetch')
            session.commit()
            
            return {
                "success": True,
                "deleted": True,
                "deletion_method": deletion_method,
                "criteria": deletion_criteria,
                "deleted_count": deleted_count,
                "deleted_vector_ids": deleted_ids[:10] if len(deleted_ids) <= 10 else deleted_ids[:10] + [f"... and {len(deleted_ids) - 10} more"],
                "message": f"Successfully deleted {deleted_count} vectors from collection '{collection_name}'"
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def main() -> None:
    """Main entry point for the MCP server."""
    mcp.run()

# Run the server
if __name__ == "__main__":
    main()