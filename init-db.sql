-- Initialize PostgreSQL database for pgvector MCP Server
-- This script runs when the Docker container is first created

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension installation
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Create a test collection to verify setup
-- (This will be managed by the MCP server, but we create a sample for testing)
INSERT INTO collections (name, description, dimension, is_active, created_at) 
VALUES ('docker_test', 'Test collection created during Docker initialization', 1024, true, NOW())
ON CONFLICT (name) DO NOTHING;

-- Display success message
DO $$
BEGIN
    RAISE NOTICE '✅ pgvector database initialized successfully!';
    RAISE NOTICE '📊 Vector extension version: %', (SELECT extversion FROM pg_extension WHERE extname = 'vector');
    RAISE NOTICE '🚀 Ready to accept MCP server connections';
END $$;