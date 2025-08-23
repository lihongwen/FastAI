# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **command-line interface (CLI)** for managing PostgreSQL collections with pgvector extension. The tool provides direct command-line access to create, manage, and search vector collections without any web interface or API layer. It's designed as a pure CLI tool for developers and data scientists working with vector databases.

## Architecture

### CLI Application Structure
- **Location**: `pgvector_cli/` directory
- **Architecture**: Direct database access with service layer pattern
- **Database Integration**: PostgreSQL with pgvector extension
- **CLI Framework**: Click-based command interface with Rich output formatting
- **Collection Management**: Each collection creates both metadata records and dedicated vector tables
- **Auto-table Management**: CollectionService automatically creates/renames/drops vector tables

### Key Features
- **Collection CRUD**: Command-line collection creation, listing, renaming, and deletion
- **Vector Operations**: Add vectors, search similar content, list vectors
- **Rich Output**: Beautiful tables, JSON export, colored output with Rich library
- **Embedding Integration**: Automatic text-to-vector conversion with multiple providers
- **Batch Operations**: Support for bulk operations via file input
- **Validation**: Comprehensive input validation and error handling

### Project Structure
```
FastAI/
├── CLAUDE.md                          # This documentation file
├── requirements.txt                   # Python dependencies
├── setup.py                          # Package installation setup
├── pgvector_cli/                     # Main CLI package
│   ├── __init__.py                   # Package initialization
│   ├── main.py                       # CLI entry point with all commands
│   ├── config.py                     # Configuration management
│   ├── database.py                   # Database connection and session
│   ├── models/                       # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── collection.py             # Collection model
│   │   └── vector_record.py          # Vector record model
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   ├── collection_service.py     # Collection management
│   │   ├── vector_service.py         # Vector operations
│   │   └── embedding_service.py      # Text embedding generation
│   └── utils/                        # CLI utilities
│       ├── __init__.py
│       ├── formatters.py             # Output formatting
│       └── validators.py             # Input validation
└── venv/                             # Python virtual environment
```

## Development Environment

### Prerequisites
- **Python**: 3.8+ (recommended 3.11+)
- **PostgreSQL**: 12+ with pgvector extension enabled
- **Database Permissions**: CREATE TABLE permissions for dynamic table management

### Environment Setup
```bash
# Navigate to project root
cd /path/to/FastAI

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Database Setup
```bash
# Ensure PostgreSQL is running
brew services start postgresql

# Connect to PostgreSQL and enable pgvector extension
psql postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify database connection
psql postgresql://lihongwen@localhost:5432/postgres -c "SELECT version();"
```

### Configuration
Create `.env` file in project root for environment variables:
```bash
# Database connection
DATABASE_URL=postgresql://lihongwen@localhost:5432/postgres

# Application settings
DEBUG=false

# Embedding service configuration (optional)
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=your_openai_key_here
```

## CLI Usage

### Installation
```bash
# Install from source (development)
pip install -e .

# After installation, use either:
python -m pgvector_cli [command] [options]
# or if installed globally:
pgvector-cli [command] [options]
```

### Basic Commands

#### Database Status
```bash
# Check database connection and pgvector status
python -m pgvector_cli status
```

#### Collection Management
```bash
# Create a new collection
python -m pgvector_cli create-collection my_docs --dimension 1024 --description "Document embeddings"

# List all collections
python -m pgvector_cli list-collections
python -m pgvector_cli list-collections --format json

# Show collection details
python -m pgvector_cli show-collection my_docs
python -m pgvector_cli show-collection my_docs --stats

# Rename collection
python -m pgvector_cli rename-collection old_name new_name

# Delete collection (with confirmation)
python -m pgvector_cli delete-collection my_docs
python -m pgvector_cli delete-collection my_docs --confirm
```

#### Vector Operations
```bash
# Add a single vector
python -m pgvector_cli add-vector my_docs --text "This is a sample document" --metadata source=manual --metadata type=doc

# Search for similar vectors
python -m pgvector_cli search my_docs --query "sample document" --limit 5
python -m pgvector_cli search my_docs --query "search text" --format json
```

### Advanced Usage

#### Batch Operations
```bash
# Create collection and add multiple vectors
python -m pgvector_cli create-collection articles --dimension 1024
python -m pgvector_cli add-vector articles --text "First article content"
python -m pgvector_cli add-vector articles --text "Second article content"
python -m pgvector_cli search articles --query "article" --limit 10
```

#### Output Formatting
```bash
# Table format (default)
python -m pgvector_cli list-collections --format table

# JSON format for scripting
python -m pgvector_cli list-collections --format json > collections.json
python -m pgvector_cli search my_docs --query "test" --format json | jq '.[0].content'
```

#### Pipeline Usage
```bash
# List collections and count them
python -m pgvector_cli list-collections --format json | jq length

# Search and extract only content
python -m pgvector_cli search my_docs --query "query" --format json | jq '.[].content'

# Get collection stats
python -m pgvector_cli show-collection my_docs --stats
```

## Command Reference

### Global Options
- `--help`: Show help message
- `--version`: Show version information

### Collection Commands

#### `create-collection <name>`
Create a new vector collection
- `--dimension, -d`: Vector dimension (default: 1024)
- `--description`: Collection description

#### `list-collections`
List all collections
- `--format`: Output format (table, json)

#### `show-collection <name>`
Show collection details
- `--stats`: Include collection statistics

#### `rename-collection <old_name> <new_name>`
Rename an existing collection

#### `delete-collection <name>`
Delete a collection
- `--confirm`: Skip confirmation prompt

### Vector Commands

#### `add-vector <collection_name>`
Add a vector to collection
- `--text`: Text content to vectorize (required)
- `--metadata`: Metadata in key=value format (multiple allowed)

#### `search <collection_name>`
Search for similar vectors
- `--query`: Search query text (required)
- `--limit`: Maximum results (default: 10)
- `--format`: Output format (table, json)

### Utility Commands

#### `status`
Check database connection and pgvector extension status

## Data Models

### Collection Schema
- **id**: Unique identifier
- **name**: Collection name (unique)
- **description**: Optional description
- **dimension**: Vector dimension
- **is_active**: Active status (for soft deletion)
- **created_at**: Creation timestamp
- **updated_at**: Last update timestamp

### Vector Record Schema
- **id**: Unique identifier
- **collection_id**: Foreign key to collection
- **content**: Original text content
- **vector**: Vector embedding (pgvector type)
- **extra_metadata**: JSONB metadata field
- **created_at**: Creation timestamp
- **updated_at**: Last update timestamp

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `DEBUG`: Enable debug mode (default: false)
- `DASHSCOPE_API_KEY`: Alibaba DashScope API key for embeddings
- `DASHSCOPE_BASE_URL`: DashScope API base URL
- `OPENAI_API_KEY`: OpenAI API key for embeddings

### Embedding Services
The CLI supports multiple embedding providers:

1. **DashScope (Alibaba)**: Set `DASHSCOPE_API_KEY`
2. **OpenAI**: Set `OPENAI_API_KEY`  
3. **Dummy**: Fallback with random embeddings for testing

### Database Configuration
- Default connection: `postgresql://lihongwen@localhost:5432/postgres`
- Requires pgvector extension
- Auto-creates tables on first run

## Development

### Adding New Commands
1. Add command function to `pgvector_cli/main.py`
2. Use Click decorators for arguments and options
3. Follow existing patterns for error handling
4. Add validation using utilities in `utils/validators.py`
5. Format output using utilities in `utils/formatters.py`

### Testing
```bash
# Manual testing workflow
python -m pgvector_cli status
python -m pgvector_cli create-collection test_collection
python -m pgvector_cli add-vector test_collection --text "test content"
python -m pgvector_cli search test_collection --query "test"
python -m pgvector_cli delete-collection test_collection --confirm
```

### Error Handling
- All commands include comprehensive error handling
- Database errors are caught and displayed with helpful messages
- Input validation prevents common user errors
- Connection issues are clearly reported

### Service Layer
- **CollectionService**: Manages collection lifecycle and metadata
- **VectorService**: Handles vector CRUD operations and search
- **EmbeddingService**: Text-to-vector conversion with multiple providers

## Integration Examples

### Shell Scripting
```bash
#!/bin/bash
# Bulk collection creation
for name in docs articles notes; do
    python -m pgvector_cli create-collection "$name" --dimension 1024
done

# Export all collections
python -m pgvector_cli list-collections --format json > collections_backup.json

# Search across collections
for collection in $(python -m pgvector_cli list-collections --format json | jq -r '.[].name'); do
    echo "Searching in $collection:"
    python -m pgvector_cli search "$collection" --query "important" --limit 3
done
```

### Python Integration
```python
# Direct service usage
from pgvector_cli.database import get_session
from pgvector_cli.services import CollectionService, VectorService

session = get_session()
collection_service = CollectionService(session)
vector_service = VectorService(session)

# Create collection programmatically
collection = collection_service.create_collection("my_collection", dimension=1024)

# Add vectors
vector_service.create_vector_record(collection.id, "Sample text", {"source": "api"})

session.close()
```

### JSON Processing
```bash
# Process search results with jq
python -m pgvector_cli search my_docs --query "search term" --format json | \
  jq '.[] | select(.similarity_score > 0.8) | .content'

# Extract collection metadata
python -m pgvector_cli list-collections --format json | \
  jq '.[] | {name: .name, vectors: .total_vectors}'
```

## Performance Considerations

### Database Optimization
- pgvector uses IVFFlat indexes for fast similarity search
- Indexes are automatically created for each collection
- Consider dimension size impact on performance
- Use appropriate `lists` parameter for IVFFlat index

### CLI Performance
- Lazy loading of embedding services
- Efficient database connection management
- Progress indicators for long-running operations
- Batch operations where applicable

### Memory Usage
- Vectors are processed one at a time to minimize memory usage
- Database connections are properly closed
- Embedding services use appropriate batch sizes

## Troubleshooting

### Common Issues

1. **"Extension vector not found"**
   ```bash
   psql postgres -c "CREATE EXTENSION vector;"
   ```

2. **"Permission denied for relation"**
   - Ensure database user has CREATE permissions
   - Check DATABASE_URL connection string

3. **"No embedding service configured"**
   - Set DASHSCOPE_API_KEY or OPENAI_API_KEY
   - Dummy embeddings used as fallback

4. **"Collection already exists"**
   - Use unique collection names
   - Check existing collections with `list-collections`

### Debug Mode
Set `DEBUG=true` in environment for verbose logging:
```bash
DEBUG=true python -m pgvector_cli status
```

### Database Inspection
```bash
# Check database tables
psql $DATABASE_URL -c "\dt"

# Inspect vector table structure
psql $DATABASE_URL -c "\d vectors_collection_name"

# Check pgvector extension
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```