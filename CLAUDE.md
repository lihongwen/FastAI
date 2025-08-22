# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack pgvector Collection Manager built with FastAPI (Python backend) and React TypeScript (frontend). The application manages PostgreSQL collections with pgvector extension for vector similarity search operations.

## Architecture

### Backend (FastAPI)
- **Location**: `backend/` directory
- **Key Architecture**: Service layer pattern with SQLAlchemy ORM
- **Database Integration**: PostgreSQL with pgvector extension
- **Collection Management**: Each collection creates both metadata records and dedicated vector tables
- **Auto-table Creation**: CollectionService automatically creates/renames/drops vector tables (format: `vectors_{collection_name}`)

### Frontend (React + TypeScript)
- **Location**: `frontend/` directory  
- **UI Framework**: Material-UI (MUI) with custom theme
- **API Integration**: Axios-based service layer with centralized API calls
- **State Management**: React hooks with local component state

### Key Integration Points
- Backend API serves at `http://localhost:8000` with CORS configured for frontend
- Frontend API client configured for `http://localhost:8000/api` base URL
- Database connection defaults to `postgresql://lihongwen@localhost:5432/postgres`

## Development Commands

### Environment Setup
```bash
# Create and activate Python virtual environment (located at project root)
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt pydantic-settings

# Install frontend dependencies
cd frontend && npm install
```

### Virtual Environment
- **Location**: `venv/` in project root directory
- **Activation**: `source venv/bin/activate` (from project root)
- **Dependencies**: Managed via `backend/requirements.txt`

### Running Services
```bash
# Start backend API (from project root)
cd backend && source ../venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend development server (from project root)
cd frontend && npm start
```

### Testing
```bash
# Run frontend tests
cd frontend && npm test

# Test API endpoints manually
curl -X GET "http://localhost:8000/health"
curl -X GET "http://localhost:8000/api/collections/"
```

### Build
```bash
# Build frontend for production
cd frontend && npm run build
```

## Database Schema

### Collections Table
- Stores collection metadata (name, description, dimension, timestamps)
- Uses soft deletion (is_active flag)

### Dynamic Vector Tables
- Format: `vectors_{collection_name_normalized}`
- Columns: id (SERIAL), vector (vector type), metadata (JSONB), created_at
- Automatic IVFFlat index creation for vector similarity search

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `DEBUG`: Enable debug mode
- Configuration loaded via `backend/.env` file

### Database Requirements
- PostgreSQL with pgvector extension enabled
- Default assumes PostgreSQL running on localhost:5432
- User should have CREATE TABLE permissions for vector table management

## Key Service Logic

### CollectionService
- Manages both collection metadata and vector table lifecycle
- Validates unique collection names
- Handles table rename operations during collection updates
- Implements soft deletion with table cleanup

## API Endpoints

### Base URLs
- **Backend API**: `http://localhost:8000`
- **API Base Path**: `/api`
- **Health Check**: `GET /health`

### Collection Management API
- `GET /api/collections/` - Get all collections
- `GET /api/collections/{id}` - Get specific collection by ID
- `POST /api/collections/` - Create new collection
- `PUT /api/collections/{id}` - Update collection (rename/description)
- `DELETE /api/collections/{id}` - Delete collection (soft delete)

### API Request/Response Examples
```bash
# Create collection
curl -X POST "http://localhost:8000/api/collections/" \
  -H "Content-Type: application/json" \
  -d '{"name":"my_collection","description":"Test collection","dimension":768}'

# Get all collections
curl -X GET "http://localhost:8000/api/collections/"

# Update collection
curl -X PUT "http://localhost:8000/api/collections/1" \
  -H "Content-Type: application/json" \
  -d '{"name":"renamed_collection","description":"Updated description"}'
```