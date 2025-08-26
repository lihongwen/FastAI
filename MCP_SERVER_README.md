# pgvector MCP Server

A Model Context Protocol (MCP) server for managing PostgreSQL collections with pgvector extension. This server provides tools for collection management, document processing, and vector search operations.

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (required for MCP library compatibility)
- **PostgreSQL 14+** with pgvector extension
- **DashScope API key** (for embeddings)
- **uv** (recommended) - Install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Installation

#### Option 1: Using uv (Recommended) ⚡

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone/navigate to project directory
cd /path/to/FastAI

# Set up environment variables
cp env.example .env
# Edit .env with your database and API credentials

# That's it! uv will automatically:
# - Create a virtual environment
# - Install all dependencies from pyproject.toml
# - Use the correct Python version (3.10+)
# - Generate/use uv.lock for reproducible builds
# - Use optimized mirror sources (China: Tsinghua, Global: PyPI)
```

**🇨🇳 中国大陆用户加速配置：**
```bash
# 项目已配置清华大学镜像源，依赖安装速度提升10倍+
# uv.toml文件已预配置最优镜像源，无需手动设置

# 如需切换其他镜像源：
# 阿里云镜像
uv run --index-url https://mirrors.aliyun.com/pypi/simple/ mcp-server

# 华为云镜像  
uv run --index-url https://mirrors.huaweicloud.com/repository/pypi/simple mcp-server
```

**Advantages of uv method:**
- ✅ **Zero manual setup** - Automatic environment and dependency management
- ✅ **Cross-platform** - Same commands work on Windows/macOS/Linux  
- ✅ **Faster** - Parallel dependency installation + China mirrors (6s vs 60s+)
- ✅ **Reproducible** - Locked dependencies ensure consistency
- ✅ **Smart mirrors** - Auto-optimized download sources

#### Option 2: Traditional Python
```bash
# Clone/navigate to project directory
cd /path/to/FastAI

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your database and API credentials
```

#### Option 3: Install as Package
```bash
pip install -e . -f setup_mcp.py
```

### Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/postgres

# DashScope API Configuration (for embeddings)
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Optional Settings
DEBUG=false
SOFT_DELETE_RETENTION_DAYS=30
```

### Running the Server

#### Method 1: Using uv (Recommended) 🚀

**All platforms (Windows/macOS/Linux):**
```bash
# Navigate to project directory
cd /path/to/FastAI

# Run MCP server - uv handles everything automatically
uv run mcp-server
```

**Benefits:**
- ✅ **Universal** - Same command on all platforms
- ✅ **Automatic** - No environment activation needed
- ✅ **Fast** - Optimized dependency loading

#### Method 2: Traditional Python

##### macOS/Linux
```bash
# Using Python directly
python start_mcp_server.py

# Or using the launcher script
./start_mcp_server.py
```

##### Windows Command Prompt
```cmd
start_mcp_server.bat
```

##### PowerShell (Recommended)
```powershell
# Allow script execution (run as administrator if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run the server
.\start_mcp_server.ps1
```

## 🛠️ MCP Client Configuration

### Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Method 1: Using uv (Recommended) ✨

```json
{
  "mcpServers": {
    "pgvector-mcp-server": {
      "command": "uv",
      "args": ["run", "mcp-server"],
      "cwd": "/absolute/path/to/FastAI",
      "env": {
        "DATABASE_URL": "postgresql://username:password@localhost:5432/postgres",
        "DASHSCOPE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Advantages:**
- ✅ Automatic dependency management
- ✅ Cross-platform compatibility 
- ✅ No manual virtual environment setup
- ✅ Consistent Python version handling

#### Method 2: Traditional Python (Legacy)

```json
{
  "mcpServers": {
    "pgvector-mcp-server": {
      "command": "python",
      "args": [
        "/absolute/path/to/FastAI/start_mcp_server.py"
      ],
      "env": {
        "DATABASE_URL": "postgresql://username:password@localhost:5432/postgres",
        "DASHSCOPE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Other MCP Clients

The server supports standard MCP protocols:
- **Transport**: STDIO (primary), HTTP+SSE
- **Protocol**: JSON-RPC 2.0
- **Specification**: MCP 2025-06-18

## 🔧 Available Tools

### System Status

#### `status`
Check comprehensive system status and connectivity.
```json
{}
```

**Returns detailed information about**:
- Database connection and pgvector extension status
- Embedding service (DashScope API) availability
- Collections overview and statistics
- System environment and version information
- Comprehensive health check for troubleshooting

### Collection Management

#### `create_collection`
Create a new vector collection.
```json
{
  "name": "my_collection",
  "description": "Description of the collection",
  "dimension": 1024
}
```

#### `list_collections`
List all active collections.
```json
{}
```

#### `show_collection`
Show details for a specific collection.
```json
{
  "name": "collection_name",
  "include_stats": true
}
```

#### `delete_collection`
Delete a collection (requires confirmation).
```json
{
  "name": "collection_name",
  "confirm": true
}
```

### Document Management

#### `add_text`
Add text content to a collection.
```json
{
  "collection_name": "my_collection",
  "text": "Your text content here",
  "metadata": {
    "source": "manual",
    "type": "note"
  }
}
```

#### `add_document`
Process and add a document file to a collection.
```json
{
  "collection_name": "my_collection",
  "file_path": "/path/to/document.pdf",
  "metadata": {
    "source": "upload",
    "category": "research"
  }
}
```

### Search Operations

#### `search_collection`
Search for similar content in a collection.
```json
{
  "collection_name": "my_collection",
  "query": "search query text",
  "limit": 10,
  "min_similarity": 0.7
}
```

### Vector Management

#### `delete_vectors`
Delete vectors from a collection with flexible filtering options.

**Deletion Methods**:
- **By File**: Delete all vectors from a specific file
  ```json
  {
    "collection_name": "my_docs",
    "file_path": "document.pdf",
    "confirm": true
  }
  ```

- **By Date Range**: Delete vectors created within a date range
  ```json
  {
    "collection_name": "my_docs", 
    "start_date": "2025-08-01",
    "end_date": "2025-08-15",
    "confirm": true
  }
  ```

- **Preview Mode**: Safely preview what would be deleted
  ```json
  {
    "collection_name": "my_docs",
    "file_path": "document.pdf",
    "preview_only": true
  }
  ```

**Safety Features**:
- Requires `confirm: true` for actual deletion
- `preview_only: true` shows what would be deleted
- Supports file path, absolute path, or filename matching
- Returns detailed deletion statistics

## 📁 Supported File Types

- **PDF**: Text extraction with structure preservation
- **CSV/Excel**: Table data processing with chunking
- **TXT**: Plain text processing
- **DOCX**: Microsoft Word documents
- **PPTX**: PowerPoint presentations

## 🌐 Cross-Platform Support

### Windows Compatibility
- ✅ Windows 10/11 support
- ✅ PowerShell and CMD scripts
- ✅ Path handling with `pathlib`
- ✅ Environment variable management

### Database Connections

#### Windows PostgreSQL URLs
```
# Local PostgreSQL
postgresql://postgres:password@localhost:5432/postgres

# With specific host
postgresql://username:password@192.168.1.100:5432/dbname

# With SSL
postgresql://username:password@host:5432/dbname?sslmode=require
```

#### macOS/Linux PostgreSQL URLs
```
# Local connection
postgresql://username@localhost:5432/postgres

# TCP connection
postgresql://user:pass@localhost:5432/dbname
```

## 🔍 Troubleshooting

### Common Issues

#### "MCP server not found"
- Ensure absolute paths in MCP client configuration
- Verify Python is in your PATH
- Check that virtual environment is activated

#### "Database connection failed"
- Verify PostgreSQL is running
- Check DATABASE_URL format
- Ensure pgvector extension is installed:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

#### "Embedding service error"
- Verify DASHSCOPE_API_KEY is set correctly
- Check network connectivity to DashScope API
- Ensure API key has sufficient credits

#### Windows-Specific Issues

**PowerShell Execution Policy**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Path Issues**
- Use forward slashes or double backslashes in paths
- Ensure no spaces in file paths or escape them properly

### Debug Mode

Enable debug logging by setting in `.env`:
```env
DEBUG=true
```

### Testing the Installation

```bash
# Test MCP server functionality
python -c "
from mcp_server import list_collections
result = list_collections()
print('✅ MCP Server working!' if result.get('success') else '❌ Error:', result)
"
```

## 🏗️ Development

### Project Structure
```
FastAI/
├── mcp_server.py              # Main MCP server
├── start_mcp_server.py        # Cross-platform launcher
├── start_mcp_server.bat       # Windows batch script
├── start_mcp_server.ps1       # Windows PowerShell script
├── mcp_config.json           # macOS/Linux MCP config
├── mcp_config_windows.json   # Windows MCP config
├── setup_mcp.py              # MCP server setup script
├── requirements.txt          # Python dependencies
├── pgvector_cli/             # Core functionality
│   ├── services/             # Business logic
│   ├── models/               # Database models
│   └── utils/                # Utilities
└── tests/                    # Test suite
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pgvector_cli

# Test MCP server specifically
python -m pytest tests/ -k "mcp"
```

### Code Quality
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy pgvector_cli/
```

## 📝 API Reference

### Response Format

All MCP tools return responses in the following format:

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error description"
}
```

### Error Codes

- **Collection Errors**: Collection not found, already exists
- **Database Errors**: Connection issues, SQL errors  
- **Validation Errors**: Invalid input parameters
- **File Errors**: File not found, unsupported format
- **API Errors**: Embedding service issues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: See `CLAUDE.md` for detailed architecture
- **Community**: Join discussions in GitHub Discussions

---

**Note**: This MCP server is built on the pgvector CLI foundation and maintains compatibility with existing collections and data.