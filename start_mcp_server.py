#!/usr/bin/env python3
"""
MCP Server Launcher for pgvector Collection Management

Cross-platform launcher script for the MCP server.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment variables if .env file exists
env_file = project_root / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        # If python-dotenv is not installed, manually load .env file
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Ensure required environment variables
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'postgresql://lihongwen@localhost:5432/postgres'

# Import and run the MCP server
if __name__ == "__main__":
    try:
        from mcp_server import mcp
        
        # Print server info
        print("🚀 Starting pgvector MCP Server...")
        print(f"📁 Project root: {project_root}")
        print(f"🗄️  Database: {os.getenv('DATABASE_URL', 'Default connection')}")
        print(f"🔧 Environment loaded from: {env_file if env_file.exists() else 'system environment'}")
        print("=" * 50)
        
        # Run the server
        mcp.run()
        
    except KeyboardInterrupt:
        print("\n👋 MCP Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting MCP Server: {e}")
        sys.exit(1)