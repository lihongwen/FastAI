#!/usr/bin/env python3
"""
pgvector Collection Manager CLI

Command-line interface for managing PostgreSQL collections with pgvector extension.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import text

from .config import get_settings
from .database import get_db_session, init_database
from .exceptions import (
    CollectionError,
    ConfigurationError,
    PgvectorCLIError,
)
from .logging_config import StructuredLogger, setup_logging
from .services import CleanupService, CollectionService, DocumentService, LLMService, VectorService
from .utils import validate_collection_name, validate_dimension

# Initialize logging
setup_logging()
logger = StructuredLogger("main")

console = Console()

def auto_cleanup():
    """Perform automatic cleanup of expired collections."""
    try:
        settings = get_settings()
        with get_db_session() as session:
            cleanup_service = CleanupService(session, settings.soft_delete_retention_days)
            cleanup_service.auto_cleanup()
    except Exception:
        # Silently handle cleanup errors to avoid disrupting main operations
        pass

@click.group()
@click.version_option(version="1.0.0")
@click.option('--config', help='Configuration file path')
def cli(config: Optional[str]):
    """pgvector Collection Manager CLI
    
    Manage PostgreSQL collections with pgvector extension via command line.
    """
    if config:
        # TODO: Load custom config file
        pass

@cli.command('status')
def status():
    """Check database connection and pgvector status."""
    try:
        with console.status("[bold green]Checking database connection..."):
            with get_db_session() as session:
                # Test basic database connection
                from sqlalchemy import text
                session.execute(text("SELECT 1"))

                # Check pgvector extension
                result = session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
                pgvector_installed = result.fetchone() is not None

        # Display status
        table = Table(title="Database Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")

        table.add_row("PostgreSQL Connection", "✓ Connected")
        table.add_row("pgvector Extension", "✓ Installed" if pgvector_installed else "✗ Not installed")

        console.print(table)

        if not pgvector_installed:
            console.print("[yellow]Warning: pgvector extension is not installed.[/yellow]")
            console.print("Run: [bold]CREATE EXTENSION vector;[/bold] in your PostgreSQL database")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error connecting to database: {e}[/red]")
        sys.exit(1)

@cli.command('create-collection')
@click.argument('name')
@click.option('--dimension', '-d', type=int, default=1024, help='Vector dimension (fixed: 1024)')
@click.option('--description', help='Collection description')
def create_collection(name: str, dimension: int, description: Optional[str]):
    """Create a new collection."""
    try:
        # Auto cleanup expired collections
        auto_cleanup()

        validate_collection_name(name)
        # 强制维度必须为1024
        if dimension != 1024:
            console.print("[red]错误: 向量维度必须为1024[/red]")
            sys.exit(1)
        validate_dimension(dimension)

        with console.status(f"[bold green]Creating collection '{name}'..."):
            with get_db_session() as session:
                service = CollectionService(session)

                collection = service.create_collection(
                    name=name,
                    dimension=dimension,
                    description=description
                )
                collection_data = {
                    'id': collection.id,
                    'name': collection.name,
                    'dimension': collection.dimension,
                    'description': collection.description
                }

        console.print(f"[green]✓[/green] Collection '{name}' created successfully")
        console.print(f"  ID: {collection_data['id']}")
        console.print(f"  Dimension: {collection_data['dimension']}")
        if description:
            console.print(f"  Description: {collection_data['description']}")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.warning("Validation error in create-collection", name=name, error=str(e))
        sys.exit(1)
    except CollectionError as e:
        console.print(f"[red]Collection Error: {e.message}[/red]")
        logger.error("Collection error in create-collection", name=name, code=e.code, error=e.message)
        sys.exit(1)
    except ConfigurationError as e:
        console.print(f"[red]Configuration Error: {e.message}[/red]")
        logger.error("Configuration error in create-collection", code=e.code, error=e.message)
        sys.exit(1)
    except PgvectorCLIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        logger.error("CLI error in create-collection", name=name, code=e.code, error=e.message)
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Failed to create collection: {e}[/red]")
        logger.error("Unexpected error in create-collection", name=name, error=str(e), exc_info=True)
        sys.exit(1)

@cli.command('list-collections')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def list_collections(output_format: str):
    """List all collections."""
    try:
        # Auto cleanup expired collections
        auto_cleanup()

        with get_db_session() as session:
            service = CollectionService(session)
            collections = service.get_collections()

            # 在会话内提取所有需要的数据
            collections_data = []
            for c in collections:
                collections_data.append({
                    'id': c.id,
                    'name': c.name,
                    'description': c.description,
                    'dimension': c.dimension,
                    'is_active': c.is_active,
                    'created_at': c.created_at.isoformat() if c.created_at else None,
                    'created_at_formatted': c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "-"
                })

        if not collections_data:
            console.print("[yellow]No collections found.[/yellow]")
            return

        if output_format == 'json':
            # 移除格式化的时间字段，只保留原始数据
            json_data = []
            for c in collections_data:
                json_data.append({
                    'id': c['id'],
                    'name': c['name'],
                    'description': c['description'],
                    'dimension': c['dimension'],
                    'is_active': c['is_active'],
                    'created_at': c['created_at']
                })
            console.print(json.dumps(json_data, indent=2))
        else:
            table = Table(title="Collections")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description", style="yellow")
            table.add_column("Dimension", style="magenta")
            table.add_column("Created", style="blue")

            for c in collections_data:
                table.add_row(
                    str(c['id']),
                    c['name'],
                    c['description'] or "-",
                    str(c['dimension']),
                    c['created_at_formatted']
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list collections: {e}[/red]")
        sys.exit(1)

@cli.command('rename-collection')
@click.argument('old_name')
@click.argument('new_name')
def rename_collection(old_name: str, new_name: str):
    """Rename a collection."""
    try:
        validate_collection_name(new_name)

        with console.status(f"[bold green]Renaming collection '{old_name}' to '{new_name}'..."):
            with get_db_session() as session:
                service = CollectionService(session)

                collection = service.get_collection_by_name(old_name)
                if not collection:
                    console.print(f"[red]Collection '{old_name}' not found.[/red]")
                    sys.exit(1)

                service.update_collection(collection.id, name=new_name)

        console.print(f"[green]✓[/green] Collection renamed from '{old_name}' to '{new_name}'")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Failed to rename collection: {e}[/red]")
        sys.exit(1)

@cli.command('delete-collection')
@click.argument('name')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def delete_collection(name: str, confirm: bool):
    """Delete a collection."""
    try:
        with get_db_session() as session:
            service = CollectionService(session)

            collection = service.get_collection_by_name(name)
            if not collection:
                console.print(f"[red]Collection '{name}' not found.[/red]")
                sys.exit(1)

            if not confirm:
                if not click.confirm(f"Are you sure you want to delete collection '{name}'? This action cannot be undone."):
                    console.print("Operation cancelled.")
                    return

            with console.status(f"[bold red]Deleting collection '{name}'..."):
                service.delete_collection(collection.id)

        console.print(f"[green]✓[/green] Collection '{name}' deleted successfully")

    except Exception as e:
        console.print(f"[red]Failed to delete collection: {e}[/red]")
        sys.exit(1)

@cli.command('show-collection')
@click.argument('name')
@click.option('--stats', is_flag=True, help='Show collection statistics')
def show_collection(name: str, stats: bool):
    """Show collection details."""
    try:
        with get_db_session() as session:
            service = CollectionService(session)

            collection = service.get_collection_by_name(name)
            if not collection:
                console.print(f"[red]Collection '{name}' not found.[/red]")
                sys.exit(1)

            # Basic collection info
            panel_content = f"""[bold]Name:[/bold] {collection.name}
[bold]ID:[/bold] {collection.id}
[bold]Dimension:[/bold] {collection.dimension}
[bold]Description:[/bold] {collection.description or 'None'}
[bold]Status:[/bold] {'Active' if collection.is_active else 'Inactive'}
[bold]Created:[/bold] {collection.created_at.strftime("%Y-%m-%d %H:%M:%S") if collection.created_at else 'Unknown'}"""

            if stats:
                vector_service = VectorService(session)
                collection_stats = vector_service.get_collection_stats(collection.id)
                panel_content += f"""
[bold]Total Vectors:[/bold] {collection_stats.get('total_vectors', 0)}"""

            console.print(Panel(panel_content, title=f"Collection: {name}", expand=False))

    except Exception as e:
        console.print(f"[red]Failed to show collection: {e}[/red]")
        sys.exit(1)

@cli.command('add-vector')
@click.argument('collection_name')
@click.option('--file', type=click.Path(exists=True), help='Document file to process and vectorize')
@click.option('--text', help='Text content to vectorize (alternative to --file)')
@click.option('--chunk-size', type=int, default=500, help='Chunk size for text splitting (default: 500)')
@click.option('--overlap', type=int, default=100, help='Overlap size between chunks (default: 100)')
@click.option('--metadata', multiple=True, help='Additional metadata in key=value format')
def add_vector(collection_name: str, file: Optional[str], text: Optional[str],
               chunk_size: int, overlap: int, metadata: tuple):
    """Add vector(s) to a collection from file or text."""
    try:
        # Validate input
        if not file and not text:
            console.print("[red]Error: Either --file or --text must be provided[/red]")
            sys.exit(1)

        if file and text:
            console.print("[red]Error: Provide either --file or --text, not both[/red]")
            sys.exit(1)

        # Parse additional metadata
        meta_dict = {}
        for item in metadata:
            if '=' not in item:
                console.print(f"[red]Invalid metadata format: {item}. Use key=value[/red]")
                sys.exit(1)
            key, value = item.split('=', 1)
            meta_dict[key] = value

        with get_db_session() as session:
            collection_service = CollectionService(session)
            vector_service = VectorService(session)

            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                console.print(f"[red]Collection '{collection_name}' not found.[/red]")
                sys.exit(1)

            if file:
                # Process document file
                document_service = DocumentService()

                # Validate file type
                if not document_service.validate_file_type(file):
                    supported = document_service.get_supported_extensions()
                    console.print(f"[red]Unsupported file type: {Path(file).suffix}[/red]")
                    console.print("Supported extensions:")
                    for ext, desc in supported.items():
                        console.print(f"  {ext}: {desc}")
                    sys.exit(1)

                with console.status(f"[bold green]Processing document '{Path(file).name}'..."):
                    # Process document into chunks
                    chunks = document_service.process_document(file, chunk_size, overlap)

                if not chunks:
                    console.print(f"[red]No content extracted from file: {file}[/red]")
                    sys.exit(1)

                console.print(f"[cyan]Document processed into {len(chunks)} chunks[/cyan]")

                # Prepare data for batch processing
                contents_and_metadata = []
                for chunk in chunks:
                    # Merge chunk metadata with user metadata
                    combined_metadata = chunk.metadata.copy()
                    combined_metadata.update(meta_dict)
                    combined_metadata.update({
                        'chunk_index': chunk.chunk_index,
                        'total_chunks': chunk.total_chunks,
                        'source_file': Path(file).name,
                        'processing_params': {
                            'chunk_size': chunk_size,
                            'overlap': overlap
                        }
                    })

                    contents_and_metadata.append({
                        'content': chunk.content,
                        'extra_metadata': combined_metadata
                    })

                with console.status(f"[bold green]Adding {len(chunks)} vectors to collection '{collection_name}'..."):
                    # Use batch processing for efficiency
                    vector_records = vector_service.create_vector_records_batch(
                        collection_id=collection.id,
                        contents_and_metadata=contents_and_metadata
                    )

                console.print(f"[green]✓[/green] Document processed and added to collection '{collection_name}'")
                console.print(f"  Source file: {Path(file).name}")
                console.print(f"  Total chunks: {len(chunks)}")
                console.print(f"  Vectors created: {len(vector_records)}")

                # Show sample content
                if chunks:
                    sample_content = chunks[0].content[:100]
                    console.print(f"  Sample content: {sample_content}{'...' if len(chunks[0].content) > 100 else ''}")

            else:
                # Process text input (legacy mode)
                with console.status(f"[bold green]Adding text vector to collection '{collection_name}'..."):
                    vector_record = vector_service.create_vector_record(
                        collection_id=collection.id,
                        content=text,
                        extra_metadata=meta_dict
                    )

                console.print(f"[green]✓[/green] Text vector added to collection '{collection_name}'")
                console.print(f"  Vector ID: {vector_record.id}")
                console.print(f"  Content: {text[:100]}{'...' if len(text) > 100 else ''}")

    except FileNotFoundError as e:
        console.print(f"[red]File error: {e}[/red]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Failed to add vector(s): {e}[/red]")
        logger.error("Error in add-vector command", exc_info=True)
        sys.exit(1)

@cli.command('add-vectors-batch')
@click.argument('collection_name')
@click.option('--file', required=True, help='JSON file containing texts and metadata')
def add_vectors_batch(collection_name: str, file: str):
    """Add multiple vectors to a collection from a JSON file."""
    import json
    import os

    try:
        # Check if file exists
        if not os.path.exists(file):
            console.print(f"[red]File not found: {file}[/red]")
            sys.exit(1)

        # Load data from JSON file
        with open(file, encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            console.print("[red]JSON file must contain a list of objects with 'content' field[/red]")
            sys.exit(1)

        # Validate data format
        for i, item in enumerate(data):
            if not isinstance(item, dict) or 'content' not in item:
                console.print(f"[red]Invalid data format at index {i}. Each item must have 'content' field[/red]")
                sys.exit(1)

        with console.status(f"[bold green]Adding {len(data)} vectors to collection '{collection_name}'..."):
            with get_db_session() as session:
                collection_service = CollectionService(session)
                vector_service = VectorService(session)

                collection = collection_service.get_collection_by_name(collection_name)
                if not collection:
                    console.print(f"[red]Collection '{collection_name}' not found.[/red]")
                    sys.exit(1)

                # Prepare data for batch processing
                contents_and_metadata = []
                for item in data:
                    contents_and_metadata.append({
                        'content': item['content'],
                        'extra_metadata': item.get('metadata', {})
                    })

                # Use batch processing
                vector_records = vector_service.create_vector_records_batch(
                    collection_id=collection.id,
                    contents_and_metadata=contents_and_metadata
                )

        console.print(f"[green]✓[/green] {len(vector_records)} vectors added to collection '{collection_name}'")
        console.print(f"  Batch processing improved performance for {len(data)} items")

    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON format: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Failed to add vectors: {e}[/red]")
        sys.exit(1)

@cli.command('search')
@click.argument('collection_name')
@click.option('--query', required=True, help='Search query text')
@click.option('--limit', type=int, default=10, help='Maximum number of results')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--precision', type=click.Choice(['high', 'medium', 'fast']), default='medium', help='Search precision level (high=ef_search=100, medium=40, fast=20)')
@click.option('--summarize', is_flag=True, help='Generate AI summary based on search results')
def search_vectors(collection_name: str, query: str, limit: int, output_format: str, precision: str, summarize: bool):
    """Search for similar vectors in a collection."""
    try:
        # 根据精度级别设置ef_search参数
        precision_settings = {
            'high': 100,    # 高精度，更好的召回率
            'medium': 40,   # 中等精度，平衡性能
            'fast': 20      # 快速搜索，优先速度
        }
        ef_search_value = precision_settings[precision]

        with console.status(f"[bold green]Searching in collection '{collection_name}' (precision: {precision})..."):
            with get_db_session() as session:
                # Set HNSW search precision parameters
                session.execute(text(f"SET LOCAL hnsw.ef_search = {ef_search_value}"))

                collection_service = CollectionService(session)
                vector_service = VectorService(session)

                collection = collection_service.get_collection_by_name(collection_name)
                if not collection:
                    console.print(f"[red]Collection '{collection_name}' not found.[/red]")
                    sys.exit(1)

                results = vector_service.search_similar_vectors(
                    collection_id=collection.id,
                    query=query,
                    limit=limit
                )

                # Extract all needed data while session is active
                if results:
                    extracted_results = []
                    for record, score in results:
                        extracted_results.append({
                            'id': record.id,
                            'content': record.content,
                            'similarity_score': score,
                            'metadata': record.extra_metadata,
                            'created_at': record.created_at.isoformat() if record.created_at else None
                        })
                else:
                    extracted_results = []

        if not extracted_results:
            console.print(f"[yellow]No results found for query: {query}[/yellow]")
            return

        # 生成LLM总结（如果启用）
        llm_summary = None
        if summarize:
            try:
                with console.status("[bold blue]Generating AI summary..."):
                    llm_service = LLMService()
                    summary_result = llm_service.summarize_search_results(
                        user_query=query,
                        search_results=extracted_results,
                        max_results=min(5, len(extracted_results))  # 限制处理前5个结果以控制token使用
                    )

                if summary_result['success']:
                    llm_summary = summary_result['summary']
                    if 'token_usage' in summary_result:
                        token_info = summary_result['token_usage']
                        logger.info(f"LLM tokens used: {token_info.get('total_tokens', 0)}")
                else:
                    console.print(f"[yellow]AI总结生成失败: {summary_result.get('error', 'Unknown error')}[/yellow]")

            except Exception as e:
                console.print(f"[yellow]AI总结功能暂时不可用: {str(e)}[/yellow]")
                logger.warning(f"LLM summary failed: {e}")

        # 显示AI总结
        if llm_summary:
            from rich.panel import Panel
            summary_panel = Panel(
                llm_summary,
                title="🤖 AI智能总结",
                title_align="left",
                border_style="blue"
            )
            console.print(summary_panel)
            console.print("")  # 添加空行分隔

        # 显示搜索结果
        if output_format == 'json':
            # JSON格式：如果有总结，将其包含在输出中
            output_data = {
                "query": query,
                "results": extracted_results
            }
            if llm_summary:
                output_data["ai_summary"] = llm_summary
            console.print(json.dumps(output_data, indent=2))
        else:
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("ID", style="cyan")
            table.add_column("Content", style="green")
            table.add_column("Similarity", style="magenta")
            table.add_column("Created", style="blue")

            for result in extracted_results:
                content = result['content'][:80] + "..." if len(result['content']) > 80 else result['content']
                table.add_row(
                    str(result['id']),
                    content,
                    f"{result['similarity_score']:.3f}",
                    result['created_at'][:16] if result['created_at'] else "-"
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to search vectors: {e}[/red]")
        sys.exit(1)

@cli.command('rebuild-index')
@click.argument('collection_name')
@click.confirmation_option(prompt='Are you sure you want to rebuild the index? This may take some time.')
def rebuild_index(collection_name: str):
    """重建集合的HNSW索引以提升搜索性能"""
    try:
        with get_db_session() as session:
            service = CollectionService(session)

            # Find collection
            collection = service.get_collection_by_name(collection_name)
            if not collection:
                console.print(f"[red]Collection '{collection_name}' not found[/red]")
                sys.exit(1)

            with console.status(f"[bold yellow]Rebuilding index for collection '{collection_name}'..."):
                success = service.rebuild_collection_index(collection.id)

            if success:
                console.print(f"[green]✓ Index rebuilt successfully: {collection_name}[/green]")
            else:
                console.print(f"[red]✗ Index rebuild failed: {collection_name}[/red]")
                sys.exit(1)

    except Exception as e:
        console.print(f"[red]Failed to rebuild index: {e}[/red]")
        sys.exit(1)

@cli.command('show-index')
@click.argument('collection_name')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def show_index(collection_name: str, output_format: str):
    """显示集合的索引信息"""
    try:
        with get_db_session() as session:
            service = CollectionService(session)

            # Find collection
            collection = service.get_collection_by_name(collection_name)
            if not collection:
                console.print(f"[red]Collection '{collection_name}' not found[/red]")
                sys.exit(1)

            index_info = service.get_collection_index_info(collection.id)

        if not index_info or not index_info["indexes"]:
            console.print(f"[yellow]No vector indexes found for collection '{collection_name}'[/yellow]")
            return

        if output_format == 'json':
            console.print(json.dumps(index_info, indent=2))
        else:
            table = Table(title=f"Index Information for '{collection_name}'")
            table.add_column("Index Name", style="cyan")
            table.add_column("Definition", style="green")

            for index in index_info["indexes"]:
                table.add_row(index["name"], index["definition"])

            console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to show index info: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    # Initialize database on startup
    try:
        init_database()
    except Exception as e:
        console.print(f"[red]Failed to initialize database: {e}[/red]")
        sys.exit(1)

    cli()
