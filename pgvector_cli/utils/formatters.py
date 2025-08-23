"""Output formatting utilities for pgvector CLI."""

import json
from typing import List, Dict, Any
from tabulate import tabulate

def format_table(data: List[Dict[str, Any]], headers: List[str] = None, 
                table_format: str = "grid") -> str:
    """Format data as a table."""
    if not data:
        return "No data to display"
    
    if headers is None:
        headers = list(data[0].keys()) if data else []
    
    rows = []
    for item in data:
        row = [item.get(header, "") for header in headers]
        rows.append(row)
    
    return tabulate(rows, headers=headers, tablefmt=table_format)

def format_json(data: Any, indent: int = 2) -> str:
    """Format data as JSON."""
    return json.dumps(data, indent=indent, default=str)

def format_collection_summary(collection) -> str:
    """Format collection as a summary string."""
    return f"{collection.name} (ID: {collection.id}, Dim: {collection.dimension})"

def format_vector_summary(vector_record) -> str:
    """Format vector record as a summary string."""
    content = vector_record.content[:50] + "..." if len(vector_record.content) > 50 else vector_record.content
    return f"ID: {vector_record.id} - {content}"

def format_search_result(vector_record, similarity_score: float) -> str:
    """Format search result as a summary string."""
    content = vector_record.content[:60] + "..." if len(vector_record.content) > 60 else vector_record.content
    return f"[{similarity_score:.3f}] {content}"