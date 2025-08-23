#!/usr/bin/env python3
"""
pgvector Collection Manager CLI

Command-line interface for managing PostgreSQL collections with pgvector extension.
"""

import click
import sys
import json
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from .config import get_settings
from .database import get_session, init_database
from .services import CollectionService, VectorService
from .utils import format_table, format_json, validate_collection_name, validate_dimension

console = Console()

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
            session = get_session()
            # Test basic database connection
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
            
            # Check pgvector extension
            result = session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
            pgvector_installed = result.fetchone() is not None
            
            session.close()
        
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
@click.option('--dimension', '-d', type=int, default=1024, help='Vector dimension (default: 1024)')
@click.option('--description', help='Collection description')
def create_collection(name: str, dimension: int, description: Optional[str]):
    """Create a new collection."""
    try:
        validate_collection_name(name)
        validate_dimension(dimension)
        
        with console.status(f"[bold green]Creating collection '{name}'..."):
            session = get_session()
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
            session.close()
        
        console.print(f"[green]✓[/green] Collection '{name}' created successfully")
        console.print(f"  ID: {collection_data['id']}")
        console.print(f"  Dimension: {collection_data['dimension']}")
        if description:
            console.print(f"  Description: {collection_data['description']}")
            
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Failed to create collection: {e}[/red]")
        sys.exit(1)

@cli.command('list-collections')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def list_collections(output_format: str):
    """List all collections."""
    try:
        session = get_session()
        service = CollectionService(session)
        collections = service.get_collections()
        session.close()
        
        if not collections:
            console.print("[yellow]No collections found.[/yellow]")
            return
        
        if output_format == 'json':
            data = [
                {
                    'id': c.id,
                    'name': c.name,
                    'description': c.description,
                    'dimension': c.dimension,
                    'is_active': c.is_active,
                    'created_at': c.created_at.isoformat() if c.created_at else None
                }
                for c in collections
            ]
            console.print(json.dumps(data, indent=2))
        else:
            table = Table(title="Collections")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description", style="yellow")
            table.add_column("Dimension", style="magenta")
            table.add_column("Created", style="blue")
            
            for c in collections:
                table.add_row(
                    str(c.id),
                    c.name,
                    c.description or "-",
                    str(c.dimension),
                    c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "-"
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
            session = get_session()
            service = CollectionService(session)
            
            collection = service.get_collection_by_name(old_name)
            if not collection:
                console.print(f"[red]Collection '{old_name}' not found.[/red]")
                sys.exit(1)
            
            updated_collection = service.update_collection(collection.id, name=new_name)
            session.close()
        
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
        session = get_session()
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
            session.close()
        
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
        session = get_session()
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
        session.close()
        
    except Exception as e:
        console.print(f"[red]Failed to show collection: {e}[/red]")
        sys.exit(1)

@cli.command('add-vector')
@click.argument('collection_name')
@click.option('--text', required=True, help='Text content to vectorize')
@click.option('--metadata', multiple=True, help='Metadata in key=value format')
def add_vector(collection_name: str, text: str, metadata: tuple):
    """Add a vector to a collection."""
    try:
        # Parse metadata
        meta_dict = {}
        for item in metadata:
            if '=' not in item:
                console.print(f"[red]Invalid metadata format: {item}. Use key=value[/red]")
                sys.exit(1)
            key, value = item.split('=', 1)
            meta_dict[key] = value
        
        with console.status(f"[bold green]Adding vector to collection '{collection_name}'..."):
            session = get_session()
            collection_service = CollectionService(session)
            vector_service = VectorService(session)
            
            collection = collection_service.get_collection_by_name(collection_name)
            if not collection:
                console.print(f"[red]Collection '{collection_name}' not found.[/red]")
                sys.exit(1)
            
            vector_record = vector_service.create_vector_record(
                collection_id=collection.id,
                content=text,
                extra_metadata=meta_dict
            )
            session.close()
        
        console.print(f"[green]✓[/green] Vector added to collection '{collection_name}'")
        console.print(f"  Vector ID: {vector_record.id}")
        console.print(f"  Content: {text[:100]}{'...' if len(text) > 100 else ''}")
        
    except Exception as e:
        console.print(f"[red]Failed to add vector: {e}[/red]")
        sys.exit(1)

@cli.command('search')
@click.argument('collection_name')
@click.option('--query', required=True, help='Search query text')
@click.option('--limit', type=int, default=10, help='Maximum number of results')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def search_vectors(collection_name: str, query: str, limit: int, output_format: str):
    """Search for similar vectors in a collection."""
    try:
        with console.status(f"[bold green]Searching in collection '{collection_name}'..."):
            session = get_session()
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
            session.close()
        
        if not results:
            console.print(f"[yellow]No results found for query: {query}[/yellow]")
            return
        
        if output_format == 'json':
            data = [
                {
                    'id': record.id,
                    'content': record.content,
                    'similarity_score': score,
                    'metadata': record.extra_metadata,
                    'created_at': record.created_at.isoformat() if record.created_at else None
                }
                for record, score in results
            ]
            console.print(json.dumps(data, indent=2))
        else:
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("ID", style="cyan")
            table.add_column("Content", style="green")
            table.add_column("Similarity", style="magenta")
            table.add_column("Created", style="blue")
            
            for record, score in results:
                content = record.content[:80] + "..." if len(record.content) > 80 else record.content
                table.add_row(
                    str(record.id),
                    content,
                    f"{score:.3f}",
                    record.created_at.strftime("%Y-%m-%d %H:%M") if record.created_at else "-"
                )
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Failed to search vectors: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    # Initialize database on startup
    try:
        init_database()
    except Exception as e:
        console.print(f"[red]Failed to initialize database: {e}[/red]")
        sys.exit(1)
    
    cli()