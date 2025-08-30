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

from mcp.server.fastmcp import FastMCP, Context
from mcp.types import Resource, Tool

# 跨平台兼容性处理
from pgvector_cli.platform import setup_cross_platform
setup_cross_platform()

from pgvector_cli.config import get_settings
from pgvector_cli.database import get_db_session
from pgvector_cli.services import CollectionService, VectorService, DocumentService, EmbeddingService
from pgvector_cli.utils import validate_collection_name, validate_dimension
from pgvector_cli.exceptions import CollectionError, DatabaseError, PgvectorCLIError
from pgvector_cli.result import mcp_success, mcp_error, safe_call, Result

# Initialize FastMCP server
mcp = FastMCP("pgvector-mcp-server")

@mcp.tool()
def status() -> Dict[str, Any]:
    """Check system status and database connectivity."""
    return _get_status().to_mcp_dict()

def _get_status():
    """Internal status check with Result pattern."""
    from pgvector_cli.result import Result
    import datetime
    import platform
    from sqlalchemy import text
    
    def check_database():
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
            
            # Mask password in URL
            settings = get_settings()
            db_url = settings.database_url
            if "@" in db_url and":" in db_url.split("@")[0]:
                user = db_url.split("://")[1].split(":")[0]
                masked_url = db_url.replace(db_url.split("://")[1].split("@")[0], f"{user}:***")
            else:
                masked_url = db_url
            
            # Check pgvector
            result = session.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")).first()
            pgvector_version = result[0] if result else None
            
            # Get collection stats
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            collections = collection_service.get_collections()
            total_vectors = sum(vector_service.get_vector_count(c.id) for c in collections)
            
            return {
                "connected": True,
                "url": masked_url,
                "pgvector_installed": result is not None,
                "pgvector_version": pgvector_version,
                "collections_total": len(collections),
                "vectors_total": total_vectors
            }
    
    def check_embedding():
        embedding_service = EmbeddingService()
        dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        
        if not dashscope_key or dashscope_key == "your_api_key_here":
            return {"available": False, "message": "DASHSCOPE_API_KEY not configured"}
        
        test_result = safe_call(embedding_service.embed_text, "test")
        if test_result.is_ok():
            embedding = test_result.unwrap()
            return {"available": True, "dimension": len(embedding), "provider": "DashScope"}
        else:
            return {"available": False, "error": test_result.error}
    
    try:
        db_result = safe_call(check_database)
        embed_result = safe_call(check_embedding)
        
        import mcp, sqlalchemy, pgvector
        system_info = {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "mcp_version": getattr(mcp, '__version__', 'unknown'),
            "sqlalchemy_version": sqlalchemy.__version__,
            "working_directory": str(Path.cwd())
        }
        
        return Result.ok({
            "timestamp": datetime.datetime.now().isoformat(),
            "database": db_result.unwrap_or({}),
            "embedding_service": embed_result.unwrap_or({}),
            "system": system_info
        })
    except Exception as e:
        return Result.err(str(e))

@mcp.tool()
def create_collection(name: str, description: str = "", dimension: int = 1024) -> Dict[str, Any]:
    """Create a new vector collection."""
    def _create():
        validate_collection_name(name)
        validate_dimension(dimension)
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            
            existing = collection_service.get_collection_by_name(name)
            if existing:
                raise CollectionError(f"Collection '{name}' already exists")
            
            collection = collection_service.create_collection(name, dimension, description)
            return {
                "id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "dimension": collection.dimension,
                "created_at": collection.created_at.isoformat(),
                "total_vectors": 0
            }
    
    result = safe_call(_create)
    return mcp_success(result.data) if result.is_ok() else mcp_error(result.error)

@mcp.tool()
def list_collections() -> Dict[str, Any]:
    """List all active collections."""
    def _list():
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            
            collections = collection_service.get_collections()
            result = []
            
            for collection in collections:
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
            
            return {"collections": result, "total": len(result)}
    
    result = safe_call(_list)
    return mcp_success(result.data) if result.is_ok() else mcp_error(result.error)

@mcp.tool()
def show_collection(name: str, include_stats: bool = True, include_files: bool = False) -> Dict[str, Any]:
    """Show details for a specific collection."""
    def _show():
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            
            collection = collection_service.get_collection_by_name(name)
            if not collection:
                raise ValueError(f"Collection '{name}' not found")
            
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
            
            if include_files:
                files = vector_service.get_files_in_collection(collection.id)
                file_summary = vector_service.get_file_summary(collection.id)
                result["files"] = files
                result["file_summary"] = file_summary
            
            return result
    
    result = safe_call(_show)
    return mcp_success(result.data) if result.is_ok() else mcp_error(result.error)

@mcp.tool()
def delete_collection(name: str, confirm: bool = False) -> Dict[str, Any]:
    """Delete a collection and all its vectors."""
    def _delete():
        if not confirm:
            raise ValueError("Deletion requires confirmation. Set confirm=True to proceed.")
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            
            collection = collection_service.get_collection_by_name(name)
            if not collection:
                raise ValueError(f"Collection '{name}' not found")
            
            collection_service.delete_collection(collection.id)
            return {"message": f"Collection '{name}' has been deleted"}
    
    result = safe_call(_delete)
    return mcp_success(result.data) if result.is_ok() else mcp_error(result.error)

@mcp.tool()
def add_text(collection_name: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Add text content to a collection as a vector."""
    def _add_text():
        if not text.strip():
            raise ValueError("Text content cannot be empty")
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            
            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                raise ValueError(f"Collection '{collection_name}' not found")
            
            vector_record = vector_service.create_vector_record(
                collection.id, text, metadata or {}
            )
            
            return {
                "id": vector_record.id,
                "content": vector_record.content,
                "metadata": vector_record.extra_metadata,
                "created_at": vector_record.created_at.isoformat()
            }
    
    result = safe_call(_add_text)
    return mcp_success(result.data) if result.is_ok() else mcp_error(result.error)

@mcp.tool()
def search_collection(
    collection_name: str, 
    query: str, 
    limit: int = 10,
    min_similarity: float = 0.0
) -> Dict[str, Any]:
    """Search for similar vectors in a collection."""
    def _search():
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        if limit <= 0 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            
            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                raise ValueError(f"Collection '{collection_name}' not found")
            
            results = vector_service.search_vectors(collection.id, query, limit)
            
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
                "query": query,
                "collection": collection_name,
                "total_results": len(filtered_results),
                "results": filtered_results
            }
    
    result = safe_call(_search)
    return mcp_success(result.data) if result.is_ok() else mcp_error(result.error)

@mcp.tool()
async def add_document(
    collection_name: str, 
    file_path: str, 
    metadata: Optional[Dict[str, Any]] = None,
    duplicate_action: str = "smart",
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Process a document file and add its contents to a collection with progress reporting.
    
    Args:
        collection_name: Name of the target collection
        file_path: Path to the document file (PDF, CSV, TXT, etc.)
        metadata: Optional metadata dictionary
        duplicate_action: How to handle duplicate files. Options:
            - "smart": Compare file modification time, skip if unchanged, overwrite if changed
            - "skip": Skip if file already exists
            - "overwrite": Always overwrite existing file vectors
            - "append": Add new vectors without removing old ones
        ctx: MCP context for progress reporting
    
    Returns:
        Dictionary with processing results and duplicate handling information
    """
    import time
    from pgvector_cli.logging_config import StructuredLogger
    
    logger = StructuredLogger("mcp_server.add_document")
    start_time = time.time()
    
    try:
        logger.info(f"开始处理文档", file_path=file_path, collection=collection_name)
        # Stage 1: Document parsing and validation (0-25%)
        if ctx:
            await ctx.report_progress(progress=0, total=100, message="开始解析文档...")
        
        # Ensure cross-platform path handling
        file_path_obj = Path(file_path).resolve()
        if not file_path_obj.exists():
            return {"success": False, "error": f"File not found: {file_path_obj}"}
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            document_service = DocumentService()  # DocumentService doesn't need session
            
            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                return {"success": False, "error": f"Collection '{collection_name}' not found"}
            
            if ctx:
                await ctx.report_progress(progress=15, total=100, message="验证集合和文件...")
            
            # Stage 1.5: Duplicate detection and handling (15-25%)
            if ctx:
                await ctx.report_progress(progress=15, total=100, message="检查文件重复...")
            
            # Validate duplicate_action parameter
            valid_actions = ["smart", "skip", "overwrite", "append"]
            if duplicate_action not in valid_actions:
                return {
                    "success": False, 
                    "error": f"Invalid duplicate_action '{duplicate_action}'. Must be one of: {', '.join(valid_actions)}"
                }
            
            # Check if file already exists
            existing_file_info = vector_service.check_file_exists(collection.id, str(file_path_obj))
            action_taken = "added"  # Default action
            file_status = {
                "existed": False,
                "file_changed": False,
                "previous_vectors": 0,
                "vectors_deleted": 0
            }
            
            if existing_file_info:
                file_status["existed"] = True
                file_status["previous_vectors"] = existing_file_info["vector_count"]
                
                # Get file modification times for smart detection
                current_file_mtime = vector_service.get_file_modification_time(str(file_path_obj))
                
                if duplicate_action == "skip":
                    logger.info("文件已存在，跳过处理", file_path=str(file_path_obj), existing_vectors=existing_file_info["vector_count"])
                    return {
                        "success": True,
                        "action_taken": "skipped",
                        "file_status": file_status,
                        "message": f"文件已存在，跳过处理。现有向量数量: {existing_file_info['vector_count']}",
                        "file_path": str(file_path_obj),
                        "collection": collection_name,
                        "vectors_created": 0,
                        "existing_file_info": existing_file_info
                    }
                
                elif duplicate_action == "smart":
                    # Compare modification times for smart detection
                    if current_file_mtime:
                        # For smart mode, we need to compare with stored metadata if available
                        # For now, we'll use a simple heuristic: if file exists, assume it might have changed
                        # In future, we could store file mtime in metadata for exact comparison
                        logger.info("智能检测模式：文件已存在，将覆盖", 
                                   file_path=str(file_path_obj),
                                   current_mtime=current_file_mtime.isoformat() if current_file_mtime else None)
                        file_status["file_changed"] = True
                        action_taken = "overwrite"
                    else:
                        logger.info("无法获取文件修改时间，跳过处理", file_path=str(file_path_obj))
                        return {
                            "success": False,
                            "error": f"Cannot access file modification time for smart detection: {file_path_obj}"
                        }
                        
                elif duplicate_action == "overwrite":
                    logger.info("强制覆盖模式：删除现有向量", file_path=str(file_path_obj), existing_vectors=existing_file_info["vector_count"])
                    action_taken = "overwrite"
                    file_status["file_changed"] = True
                    
                elif duplicate_action == "append":
                    logger.info("追加模式：保留现有向量，添加新向量", file_path=str(file_path_obj), existing_vectors=existing_file_info["vector_count"])
                    action_taken = "append"
                    # Don't delete existing vectors in append mode
                
                # Delete existing vectors for overwrite and smart modes
                if action_taken in ["overwrite"] or (action_taken == "overwrite" and duplicate_action == "smart"):
                    if ctx:
                        await ctx.report_progress(progress=20, total=100, message=f"删除{existing_file_info['vector_count']}个现有向量...")
                    
                    deleted_count = vector_service.delete_file_vectors(collection.id, str(file_path_obj))
                    file_status["vectors_deleted"] = deleted_count
                    logger.info("删除现有向量完成", deleted_count=deleted_count)
            
            if ctx:
                await ctx.report_progress(progress=25, total=100, message="重复检测完成，开始处理文档...")
            
            # Stage 2: Text chunking (25-50%)
            chunking_start = time.time()
            if ctx:
                await ctx.report_progress(progress=25, total=100, message="正在分块处理文档...")
            
            # Process document with default chunking parameters
            chunks = document_service.process_document(
                str(file_path_obj), chunk_size=500, overlap=100
            )
            
            if not chunks:
                return {"success": False, "error": "No content extracted from document"}
            
            chunking_time = time.time() - chunking_start
            logger.info("文档分块完成", chunks_count=len(chunks), processing_time_seconds=f"{chunking_time:.2f}")
            
            if ctx:
                await ctx.report_progress(progress=50, total=100, message=f"生成{len(chunks)}个文档块")
            
            # Stage 3: Vector generation (50-90%) - True batch processing with single transaction
            vector_start = time.time()
            if ctx:
                await ctx.report_progress(progress=60, total=100, message="准备批量向量生成...")
            
            # Prepare all batch data at once for maximum efficiency
            all_batch_data = []
            for chunk in chunks:
                # Merge chunk metadata with user metadata
                combined_metadata = {**chunk.metadata, **(metadata or {})}
                all_batch_data.append({
                    'content': chunk.content,
                    'extra_metadata': combined_metadata
                })
            
            if ctx:
                await ctx.report_progress(progress=70, total=100, message=f"开始处理{len(all_batch_data)}个文档块（批量模式）...")
            
            logger.info("开始批量向量生成", batch_size=len(all_batch_data))
            
            # Process all chunks in single batch operation (API calls: 10 texts per batch internally)
            # Database: Single transaction for all vectors
            results = vector_service.create_vector_records_batch(collection.id, all_batch_data)
            
            vector_time = time.time() - vector_start
            logger.info("批量向量生成完成", vectors_created=len(results), processing_time_seconds=f"{vector_time:.2f}")
            
            if ctx:
                await ctx.report_progress(progress=85, total=100, message=f"完成批量处理，生成{len(results)}个向量")
            
            # Stage 4: Database storage completion (90-100%)
            if ctx:
                await ctx.report_progress(progress=90, total=100, message="完成向量存储...")
                await ctx.report_progress(progress=100, total=100, message="处理完成")
            
            total_time = time.time() - start_time
            logger.info("文档处理完成", 
                       total_processing_time_seconds=f"{total_time:.2f}",
                       vectors_created=len(results),
                       chunks_processed=len(chunks),
                       avg_time_per_vector=f"{total_time/len(results):.3f}" if results else "N/A")
            
            # Update file_status with final counts
            file_status["vectors_created"] = len(results)
            
            # Generate appropriate message based on action taken
            if action_taken == "append":
                message = f"追加模式：保留{file_status['previous_vectors']}个现有向量，新增{len(results)}个向量"
            elif action_taken == "overwrite":
                message = f"覆盖模式：删除{file_status['vectors_deleted']}个旧向量，添加{len(results)}个新向量"
            else:
                message = f"成功处理文档，创建{len(results)}个向量"
            
            return {
                "success": True,
                "action_taken": action_taken,
                "file_status": file_status,
                "message": message,
                "file_path": str(file_path_obj),
                "collection": collection_name,
                "vectors_created": len(results),
                "processing_stats": {
                    "total_time_seconds": f"{total_time:.2f}",
                    "chunking_time_seconds": f"{chunking_time:.2f}",
                    "vector_generation_time_seconds": f"{vector_time:.2f}",
                    "chunks_processed": len(chunks),
                    "avg_time_per_vector": f"{total_time/len(results):.3f}" if results else "N/A"
                },
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
        total_time = time.time() - start_time
        logger.error("文档处理失败", 
                    error=str(e), 
                    processing_time_seconds=f"{total_time:.2f}",
                    file_path=file_path, 
                    collection=collection_name,
                    exc_info=True)
        if ctx:
            await ctx.report_progress(progress=0, total=100, message=f"处理失败: {str(e)}")
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
    """Delete vectors from a collection with flexible filtering options."""
    def _delete_vectors():
        # Parameter validation
        if not file_path and not (start_date and end_date):
            raise ValueError("Must specify either file_path or both start_date and end_date")
        
        if file_path and (start_date or end_date):
            raise ValueError("Cannot specify both file_path and date range. Choose one deletion method.")
        
        if start_date and not end_date:
            raise ValueError("Both start_date and end_date are required for date range deletion")
        
        if not preview_only and not confirm:
            raise ValueError("Deletion requires confirmation. Set confirm=True or use preview_only=True to preview first.")
        
        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            
            # Find collection
            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                raise ValueError(f"Collection '{collection_name}' not found")
            
            # Handle file path deletion
            if file_path:
                if preview_only:
                    return vector_service.preview_delete_vectors_by_file(collection.id, file_path)
                else:
                    deleted_count = vector_service.delete_file_vectors(collection.id, file_path)
                    return {
                        "deleted_count": deleted_count,
                        "file_path": file_path,
                        "collection": collection_name,
                        "message": f"Successfully deleted {deleted_count} vectors from file: {file_path}"
                    }
            
            # Handle date range deletion
            elif start_date and end_date:
                if preview_only:
                    return vector_service.preview_delete_vectors_by_date_range(collection.id, start_date, end_date)
                else:
                    result = vector_service.delete_vectors_by_date_range(collection.id, start_date, end_date)
                    result["collection"] = collection_name
                    return result
    
    result = safe_call(_delete_vectors)
    return mcp_success(result.data) if result.is_ok() else mcp_error(result.error)

def main() -> None:
    """Main entry point for the MCP server."""
    mcp.run()

# Run the server
if __name__ == "__main__":
    main()