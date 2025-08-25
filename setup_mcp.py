"""Setup script for pgvector MCP Server package."""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pgvector-mcp-server",
    version="1.0.0",
    author="FastAI Project",
    author_email="noreply@example.com",
    description="MCP Server for managing PostgreSQL collections with pgvector extension",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/pgvector-mcp-server",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.10",
    install_requires=[
        # Core MCP dependencies
        "mcp>=1.2.0",
        
        # Database and vector dependencies
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "pgvector>=0.2.0",
        
        # Configuration and validation
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        
        # AI and embedding services
        "dashscope>=1.0.0",
        "openai>=1.0.0",
        "numpy>=1.20.0",
        
        # Document processing dependencies
        "pymupdf4llm>=0.0.20",
        "python-docx>=1.0.0",
        "openpyxl>=3.0.0",
        "python-pptx>=1.0.0",
        "pandas>=2.0.0",
        "chardet>=5.0.0",
        "langchain-text-splitters>=0.3.0",
        
        # HTTP and networking
        "httpx[socks]>=0.27.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
        "legacy-cli": [
            # Legacy CLI support (optional)
            "click>=8.0.0",
            "rich>=13.0.0",
            "tabulate>=0.9.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "pgvector-mcp-server=start_mcp_server:main",
        ],
    },
    scripts=[
        "start_mcp_server.py",
        "mcp_server.py",
    ],
    include_package_data=True,
    zip_safe=False,
)