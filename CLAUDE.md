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
- **Document Processing**: Support for PDF, CSV, and text file parsing with automatic chunking
- **AI-Powered Summarization**: Intelligent search result summarization using Qwen LLM
- **Rich Output**: Beautiful tables, JSON export, colored output with Rich library
- **Embedding Integration**: Automatic text-to-vector conversion with DashScope text-embedding-v4
- **High-Performance Search**: HNSW indexing with tunable precision levels
- **Vector Optimization**: L2 normalization and MRL transformation for 1024 dimensions
- **Index Management**: Rebuild and monitor indexes for optimal performance
- **Batch Operations**: Support for bulk operations via file input
- **Validation**: Comprehensive input validation and error handling
- **Auto-cleanup**: Automatic hard deletion of soft-deleted collections after 30 days

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
│   │   ├── embedding_service.py      # Text embedding generation
│   │   ├── cleanup_service.py        # Automatic cleanup of expired collections
│   │   ├── document_service.py       # Document processing and chunking
│   │   ├── llm_service.py           # LLM integration for summarization
│   │   ├── chunking_service.py      # Text chunking algorithms
│   │   └── parsers/                 # File format parsers
│   │       ├── base_parser.py       # Base parser interface
│   │       ├── pdf_parser.py        # PDF document parsing
│   │       ├── csv_parser.py        # CSV file parsing
│   │       └── text_parser.py       # Plain text parsing
│   └── utils/                        # CLI utilities
│       ├── __init__.py
│       ├── formatters.py             # Output formatting
│       └── validators.py             # Input validation
└── venv/                             # Python virtual environment
```

## Development Environment

### Prerequisites
- **Python**: 3.13.4 (exact version for compatibility)
- **PostgreSQL**: 14.18 with pgvector 0.8.0 extension enabled
- **Database Permissions**: CREATE TABLE permissions for dynamic table management

### Platform Support
- **macOS**: Native development environment (Darwin 24.6.0, arm64)  
- **WSL 2**: Full production deployment support (Ubuntu 22.04 LTS recommended)
- **Linux**: Compatible with most distributions

### Environment Setup
```bash
# Navigate to project root
cd /path/to/FastAI

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install LLM/AI features dependencies (optional)
pip install openai socksio

# Install package in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
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

# DashScope embedding service configuration (阿里云)
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Cleanup configuration
SOFT_DELETE_RETENTION_DAYS=30
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
- `--dimension, -d`: Vector dimension (fixed: 1024, required)
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
- **dimension**: Vector dimension (fixed at 1024)
- **is_active**: Active status (for soft deletion)
- **created_at**: Creation timestamp
- **updated_at**: Last update timestamp
- **deleted_at**: Soft deletion timestamp (for auto-cleanup)

### Vector Record Schema
- **id**: Unique identifier
- **collection_id**: Foreign key to collection
- **content**: Original text content
- **vector**: Vector embedding (pgvector type, 1024 dimensions)
- **extra_metadata**: JSONB metadata field
- **created_at**: Creation timestamp
- **updated_at**: Last update timestamp

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `DEBUG`: Enable debug mode (default: false)
- `DASHSCOPE_API_KEY`: Alibaba DashScope API key for embeddings
- `DASHSCOPE_BASE_URL`: DashScope API base URL
- `SOFT_DELETE_RETENTION_DAYS`: Days to keep soft-deleted collections (default: 30)

### Embedding Services
The CLI uses DashScope (阿里云) as the primary embedding service:

1. **DashScope text-embedding-v4**: Set `DASHSCOPE_API_KEY`
   - High-quality embeddings with MRL transformation to 1024 dimensions
   - Optimized for Chinese and English text
   - API endpoint: https://dashscope.console.aliyun.com/
   - All vectors automatically converted to 1024 dimensions using Multi-Representation Learning (MRL)

#### MRL Vector Transformation
- **Input**: Native DashScope embeddings (typically 1536 dimensions)
- **Output**: Standardized 1024-dimensional vectors
- **Method**: Intelligent dimension reduction using weighted chunking and L2 norm preservation
- **Benefits**: Maintains semantic quality while ensuring consistent dimensionality

### Database Configuration
- Default connection: `postgresql://lihongwen@localhost:5432/postgres`
- Requires pgvector extension
- Auto-creates tables on first run

### Auto-cleanup System
The CLI includes an automatic cleanup system for managing storage efficiently:

#### How it Works
- **Soft Deletion**: When you delete a collection, it's marked as inactive (`is_active = false`) and the deletion time is recorded (`deleted_at`)
- **Vector Table Cleanup**: The associated vector table is immediately dropped to free up storage
- **Metadata Retention**: Collection metadata is kept for 30 days for potential recovery
- **Auto Hard-deletion**: After 30 days, the collection metadata is permanently deleted from PostgreSQL

#### Configuration
- `SOFT_DELETE_RETENTION_DAYS`: Configure retention period (default: 30 days)
- Cleanup runs automatically during normal CLI operations (`list-collections`, `create-collection`)
- No manual intervention required - the system maintains itself

#### Benefits
- **Storage Efficiency**: Automatic cleanup prevents database bloat
- **Safety Buffer**: 30-day retention period prevents accidental permanent loss
- **Zero Maintenance**: Runs transparently in the background
- **Configurable**: Adjust retention period based on your needs

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
- **EmbeddingService**: Text-to-vector conversion with DashScope text-embedding-v4
- **CleanupService**: Automatic cleanup of expired soft-deleted collections

## Development Commands

### Code Quality and Testing
```bash
# Run linting with ruff
ruff check .
ruff check --fix .  # Auto-fix issues

# Run type checking with mypy
mypy pgvector_cli/

# Run tests with pytest
pytest                           # Run all tests
pytest tests/unit/              # Run unit tests only
pytest tests/integration/       # Run integration tests only
pytest -v                       # Verbose output
pytest -k test_collection      # Run specific test pattern

# Run tests with coverage
pytest --cov=pgvector_cli --cov-report=html
# View coverage report in htmlcov/index.html

# Run specific test file
pytest tests/unit/test_collection_service.py
pytest tests/unit/test_collection_service.py::TestCollectionService::test_create_collection
```

### Development Workflow
```bash
# Using uv (recommended) - with Chinese mirrors for faster development
# Install development dependencies (defined in pyproject.toml)
uv sync --dev

# Run full development check (recommended before commits)
uv run ruff check . && uv run ruff format . && uv run mypy pgvector_cli/ && uv run mypy mcp_server.py && uv run pytest

# Quick quality check
uv run ruff check --fix . && uv run ruff format .

# Manual testing workflow
uv run python -m pgvector_cli status
uv run python -m pgvector_cli create-collection test_collection --description "Test collection"
uv run python -m pgvector_cli add-vector test_collection --text "test content"  
uv run python -m pgvector_cli search test_collection --query "test"
uv run python -m pgvector_cli delete-collection test_collection --confirm

# Test MCP server directly
uv run mcp-server                 # Uses entry point from pyproject.toml

# Legacy pip method (slower)
pip install -e ".[dev]"
ruff check . && mypy pgvector_cli/ && pytest
python -m pgvector_cli status
python start_mcp_server.py
```

### Database Development
```bash
# Check database status
python -m pgvector_cli status

# Inspect database tables directly
psql $DATABASE_URL -c "\\dt"

# View collection tables
psql $DATABASE_URL -c "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'vectors_%';"

# Check pgvector extension
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Drop test collections (cleanup)
python -m pgvector_cli list-collections --format json | jq -r '.[].name' | grep test | xargs -I {} python -m pgvector_cli delete-collection {} --confirm
```

### Package Building and Distribution
```bash
# Build package
python -m build

# Install from local build
pip install dist/pgvector_cli-*.whl

# Clean build artifacts
rm -rf build/ dist/ *.egg-info/
```

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
   - Set DASHSCOPE_API_KEY in .env file
   - Get API key from https://dashscope.console.aliyun.com/

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

## Cross-Platform Deployment

### Windows Support
Full Windows compatibility with dedicated launcher scripts:

```bash
# Windows Command Prompt
start_mcp_server.bat

# Windows PowerShell (recommended)
.\start_mcp_server.ps1

# Set execution policy if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### WSL 2 Support
完全支持WSL 2环境部署，与macOS环境保持一致：

- **兼容性验证**: `python verify_wsl_compatibility.py`
- **版本要求**: Python 3.13.4, PostgreSQL 14.18, pgvector 0.8.0
- **快速测试**: 运行CLI和MCP服务器功能测试

### macOS/Linux
Native support with modern tooling and cross-platform compatibility:

```bash
# Using uv (recommended) - automatic environment management + Chinese mirrors
uv run mcp-server

# 🇨🇳 中国大陆用户：项目已预配置清华大学镜像源，安装速度提升10倍+
# 如需切换镜像源：
# uv run --index-url https://mirrors.aliyun.com/pypi/simple/ mcp-server

# Traditional Python methods
python start_mcp_server.py

# With proper virtual environment activation
source venv/bin/activate && python start_mcp_server.py
```

## MCP Integration

### Supported MCP Clients
- **Claude Desktop**: Primary integration target
- **Other MCP Clients**: Standard JSON-RPC 2.0 protocol support
- **Protocol**: MCP 2025-06-18 specification
- **Transport**: STDIO (primary), HTTP+SSE support

### MCP Server Architecture
- **Entry Point**: `mcp_server.py` with FastMCP framework
- **Cross-Platform**: Automatic Windows/Unix path handling
- **Service Integration**: Reuses all CLI services and business logic
- **Error Handling**: Structured error responses with proper MCP formatting
- **Tools Available**: Collection management, document processing, vector search

See `MCP_SERVER_README.md` for detailed MCP integration documentation.