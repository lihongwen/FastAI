@echo off
REM Windows batch script to start the MCP server
setlocal enabledelayedexpansion

echo ========================================
echo     pgvector MCP Server for Windows
echo ========================================
echo.

REM Check if Python is available
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ and add it to your PATH
    echo Download from: https://python.org/downloads/
    pause
    exit /b 1
)

python --version
echo [✓] Python found

REM Check PostgreSQL connection
echo.
echo [2/5] Checking environment variables...
if "%DATABASE_URL%"=="" (
    echo [WARNING] DATABASE_URL not set. Using default.
    set DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres
)

if "%DASHSCOPE_API_KEY%"=="" (
    echo [WARNING] DASHSCOPE_API_KEY not set. Some features may not work.
)

echo DATABASE_URL: %DATABASE_URL%

REM Check and activate virtual environment
echo.
echo [3/5] Setting up virtual environment...
if exist "venv\Scripts\activate.bat" (
    echo [✓] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found. Using system Python.
    echo To create a virtual environment, run:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
)

REM Install/check dependencies
echo.
echo [4/5] Checking MCP dependencies...
pip show mcp >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing MCP dependencies...
    pip install mcp
)

REM Start the MCP server
echo.
echo [5/5] Starting MCP server...
echo ========================================
echo MCP Server is starting...
echo Press Ctrl+C to stop the server
echo ========================================
python start_mcp_server.py

echo.
echo MCP Server has stopped.
pause