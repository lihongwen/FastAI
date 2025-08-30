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

# 使用统一的跨平台配置管理
from pgvector_cli.platform import setup_cross_platform
setup_cross_platform()

# 配置已经在pgvector_cli.config中统一处理，无需在此重复加载

# 环境变量由统一配置类管理，无需手动设置默认值

# Import and run the MCP server
if __name__ == "__main__":
    try:
        from mcp_server import mcp
        
        from pgvector_cli.config import get_settings
        settings = get_settings()
        config_info = settings.mask_sensitive_data()
        
        # Print server info
        print("🚀 Starting pgvector MCP Server (Linus重构版)...")
        print(f"📁 Project root: {project_root}")
        print(f"🗄️  Database: {config_info['database_url']}")
        print(f"🔑 DashScope API: {'已配置' if config_info['dashscope_api_key'] else '未配置'}")
        print(f"🐛 Debug mode: {config_info['debug']}")
        print("=" * 50)
        
        # Run the server
        mcp.run()
        
    except KeyboardInterrupt:
        print("\n👋 MCP Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting MCP Server: {e}")
        sys.exit(1)