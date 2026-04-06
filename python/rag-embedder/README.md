# rag-embedder

Batch embedding and storage component for the RAG system. Takes chunked documents and vectorizes them for storage.

## What it does

1. Reads `chunks.json` produced by **rag-loader**
2. Deserializes chunks into `ChunkInput` objects
3. Batch-encodes text content using `EmbeddingClient` (configurable batch size, default 32)
4. Writes `embeddings.json` to the output directory
5. Upserts embeddings into PostgreSQL via pgvector (updates existing `(document_name, chunk_index)` pairs, inserts new ones)

## Dependencies

- `lib-embedding` — embedding generation
- `lib-orm` — database access
- `lib-schemas` — data schemas
- `pydantic-settings` — configuration

## Running

```bash
uv run main --input_dir data/chunks --output_dir data/embeddings --db_url "postgresql+asyncpg://rag:rag@localhost:5432/rag" --embedding_model all-MiniLM-L6-v2 --batch_size 32
```

Runs as a containerized Kubeflow pipeline component (`Dockerfile` included).

## Role in the pipeline

Post-processing stage between **rag-loader** and the pgvector database. Orchestrated by **rag-pipeline** as a Kubeflow component.
