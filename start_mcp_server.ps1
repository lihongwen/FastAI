# PowerShell script to start the pgvector MCP server on Windows
# Run with: powershell -ExecutionPolicy Bypass -File start_mcp_server.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "     pgvector MCP Server for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Step 1: Check Python installation
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
if (Test-Command "python") {
    $pythonVersion = python --version
    Write-Host "[✓] Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ and add it to your PATH" -ForegroundColor Red
    Write-Host "Download from: https://python.org/downloads/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Check environment variables
Write-Host ""
Write-Host "[2/5] Checking environment variables..." -ForegroundColor Yellow

if (-not $env:DATABASE_URL) {
    Write-Host "[WARNING] DATABASE_URL not set. Using default." -ForegroundColor Yellow
    $env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/postgres"
}

if (-not $env:DASHSCOPE_API_KEY) {
    Write-Host "[WARNING] DASHSCOPE_API_KEY not set. Some features may not work." -ForegroundColor Yellow
}

Write-Host "DATABASE_URL: $env:DATABASE_URL" -ForegroundColor Cyan

# Step 3: Check and activate virtual environment
Write-Host ""
Write-Host "[3/5] Setting up virtual environment..." -ForegroundColor Yellow

if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "[✓] Activating virtual environment..." -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "[WARNING] Virtual environment not found. Using system Python." -ForegroundColor Yellow
    Write-Host "To create a virtual environment, run:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor White
    Write-Host "  venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
}

# Step 4: Check dependencies
Write-Host ""
Write-Host "[4/5] Checking MCP dependencies..." -ForegroundColor Yellow

try {
    pip show mcp | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[INFO] Installing MCP dependencies..." -ForegroundColor Cyan
        pip install mcp
    }
} catch {
    Write-Host "[INFO] Installing MCP dependencies..." -ForegroundColor Cyan
    pip install mcp
}

# Step 5: Start the MCP server
Write-Host ""
Write-Host "[5/5] Starting MCP server..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MCP Server is starting..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

try {
    python start_mcp_server.py
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to start MCP server: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "MCP Server has stopped." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
}