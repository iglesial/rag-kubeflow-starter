# rag-retriever

FastAPI retrieval service for the RAG system. Provides a REST API for semantic search over stored document embeddings.

## What it does

- **POST `/search`** — Accepts a query, embeds it, and performs cosine similarity search against pgvector. Returns ranked results with timing info.
- **GET `/documents/stats`** — Returns database statistics (document count, chunk count, model info).
- **GET `/health`** — Liveness probe (always OK).
- **GET `/ready`** — Readiness probe (checks database and model availability).

## Architecture

- **Dependency injection**: Singleton embedding client and async database engine, initialized at startup
- **Lifespan management**: Startup/shutdown hooks for resource initialization and cleanup
- **Per-request sessions**: Async database sessions with auto-commit/rollback

## Dependencies

- `fastapi` — web framework
- `uvicorn` — ASGI server
- `lib-embedding` — query embedding
- `lib-orm` — database access
- `lib-schemas` — API schemas
- `pydantic-settings` — configuration

## Running

```bash
python -m rag_retriever.main
```

Runs as a containerized service (`Dockerfile` included), designed for Kubernetes deployment with health/readiness probes.

## Role in the pipeline

Query-time service. Long-lived API server that accepts semantic search queries, vectorizes them, and performs similarity search against document embeddings stored in pgvector.
