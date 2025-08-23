# pgvector CLI

A command-line interface for managing PostgreSQL collections with pgvector extension.

## Features

- **Collection Management**: Create, list, rename, and delete vector collections
- **Vector Operations**: Add vectors and search for similar content
- **Multiple Embedding Providers**: Support for DashScope and OpenAI
- **Rich Output**: Beautiful tables and JSON formatting
- **Database Integration**: Direct PostgreSQL access with pgvector

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Setup database**:
   ```bash
   psql postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

3. **Check status**:
   ```bash
   python -m pgvector_cli status
   ```

4. **Create a collection**:
   ```bash
   python -m pgvector_cli create-collection my_docs --dimension 1024
   ```

5. **Add vectors and search**:
   ```bash
   python -m pgvector_cli add-vector my_docs --text "Sample document"
   python -m pgvector_cli search my_docs --query "document"
   ```

## Documentation

See [CLAUDE.md](CLAUDE.md) for complete documentation.

## Requirements

- Python 3.8+
- PostgreSQL with pgvector extension
- Optional: DashScope or OpenAI API keys for embeddings