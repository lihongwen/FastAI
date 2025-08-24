"""Setup script for pgvector CLI package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pgvector-cli",
    version="1.0.0",
    author="FastAI Project",
    author_email="noreply@example.com",
    description="Command-line interface for managing PostgreSQL collections with pgvector extension",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/pgvector-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "pgvector>=0.2.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "click>=8.0.0",
        "rich>=13.0.0",
        "tabulate>=0.9.0",
        "dashscope>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pgvector-cli=pgvector_cli.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)