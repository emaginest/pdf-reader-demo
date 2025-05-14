-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS vector_store;

-- Create tables for vector store
CREATE TABLE IF NOT EXISTS vector_store.collections (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vector_store.documents (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES vector_store.collections(id) ON DELETE CASCADE,
    document TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create tables for agents-hub pgvector
CREATE TABLE IF NOT EXISTS vector_store.pg_collection (
    uuid UUID PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vector_store.pg_embedding (
    uuid UUID PRIMARY KEY,
    collection_id UUID REFERENCES vector_store.pg_collection(uuid) ON DELETE CASCADE,
    document TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for vector_store.documents
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON vector_store.documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS documents_document_id_idx ON vector_store.documents ((metadata->>'document_id'));
CREATE INDEX IF NOT EXISTS documents_version_idx ON vector_store.documents ((metadata->>'version'));

-- Create indexes for vector_store.pg_embedding
CREATE INDEX IF NOT EXISTS pg_embedding_embedding_idx ON vector_store.pg_embedding USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS pg_embedding_document_id_idx ON vector_store.pg_embedding ((metadata->>'document_id'));
CREATE INDEX IF NOT EXISTS pg_embedding_version_idx ON vector_store.pg_embedding ((metadata->>'version'));

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA vector_store TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA vector_store TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA vector_store TO postgres;
