# lib-orm

Database and ORM library for the RAG system. Provides async PostgreSQL access with pgvector support.

## What it does

- **Database utilities** (`db.py`): Async SQLAlchemy engine creation, session factory, and context-managed sessions with auto-commit/rollback
- **DocumentChunk model** (`models.py`): ORM mapping to the `document_chunks` table — stores document name, chunk index, content, JSONB metadata, and a 384-dimensional embedding vector
- **DbSettings**: Database connection URL configuration via environment variables

## Key features

- Async database access via `asyncpg`
- pgvector column for cosine similarity search
- Unique constraint on `(document_name, chunk_index)` pairs

## Dependencies

- `sqlalchemy[asyncio]` — async ORM
- `asyncpg` — PostgreSQL async driver
- `pgvector` — vector similarity search extension
- `pydantic-settings` — configuration management

## Role in the pipeline

Persistent storage layer. **rag-embedder** writes embeddings here; **rag-retriever** reads from here for similarity search.
