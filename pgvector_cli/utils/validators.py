"""Input validation utilities for pgvector CLI."""

import re


def validate_collection_name(name: str) -> bool:
    """Validate collection name format for safe SQL usage."""
    if not name:
        raise ValueError("Collection name cannot be empty")

    if len(name) < 2:
        raise ValueError("Collection name must be at least 2 characters long")

    if len(name) > 50:
        raise ValueError("Collection name must be 50 characters or less")

    # For security, only allow alphanumeric characters, underscores, and hyphens
    # Spaces and special characters will be converted to underscores in table names
    if not re.match(r'^[a-zA-Z0-9_\-\s]+$', name):
        raise ValueError("Collection name can only contain letters, numbers, underscores, hyphens, and spaces")

    # Cannot start or end with space
    if name.startswith(' ') or name.endswith(' '):
        raise ValueError("Collection name cannot start or end with spaces")

    # Warn if name contains characters that will be converted to underscores
    if ' ' in name or '-' in name:
        print("Note: Spaces and hyphens in collection name will be converted to underscores in the database table name.")

    return True

def validate_dimension(dimension: int) -> bool:
    """Validate vector dimension."""
    if dimension < 1:
        raise ValueError("Dimension must be a positive integer")

    if dimension > 4096:
        raise ValueError("Dimension cannot exceed 4096")

    # Common embedding dimensions
    common_dims = [128, 256, 384, 512, 768, 1024, 1536, 2048, 3072, 4096]
    if dimension not in common_dims:
        # Warning but not error
        print(f"Warning: Dimension {dimension} is not a common embedding size. "
              f"Common sizes are: {', '.join(map(str, common_dims))}")

    return True

def validate_metadata_format(metadata_str: str) -> tuple:
    """Validate and parse metadata string in key=value format."""
    if '=' not in metadata_str:
        raise ValueError(f"Invalid metadata format: {metadata_str}. Use key=value")

    parts = metadata_str.split('=', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid metadata format: {metadata_str}. Use key=value")

    key, value = parts
    key = key.strip()
    value = value.strip()

    if not key:
        raise ValueError("Metadata key cannot be empty")

    # Try to parse value as JSON if it looks like it
    if value.startswith('{') or value.startswith('[') or value.lower() in ['true', 'false', 'null']:
        try:
            import json
            value = json.loads(value)
        except json.JSONDecodeError:
            pass  # Keep as string
    elif value.isdigit():
        value = int(value)
    elif value.replace('.', '').isdigit():
        value = float(value)

    return key, value

def validate_search_query(query: str) -> bool:
    """Validate search query."""
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    if len(query.strip()) < 1:
        raise ValueError("Search query must contain at least 1 character")

    if len(query) > 1000:
        raise ValueError("Search query cannot exceed 1000 characters")

    return True

def validate_limit(limit: int, max_limit: int = 100) -> bool:
    """Validate limit parameter."""
    if limit < 1:
        raise ValueError("Limit must be a positive integer")

    if limit > max_limit:
        raise ValueError(f"Limit cannot exceed {max_limit}")

    return True
