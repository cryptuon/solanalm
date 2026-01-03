-- SolanaLM Database Initialization
-- This script runs on first PostgreSQL container startup

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for common queries (tables are created by SQLAlchemy/Alembic)
-- These are placeholder comments; actual indexes are in the SQLAlchemy models

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE solanalm TO solanalm;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'SolanaLM database initialized successfully';
END $$;
