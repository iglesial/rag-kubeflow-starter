# lib-schemas

Shared Pydantic schemas for data exchange between RAG system components.

## Schemas

| Schema | Purpose |
|---|---|
| **ChunkInput** | Raw document chunk (document_name, chunk_index, content, metadata) |
| **ChunkWithEmbedding** | Extends ChunkInput with an embedding vector |
| **SearchRequest** | API request: query, top_k (1–50), similarity_threshold (0.0–1.0) |
| **SearchResult** | Single result: chunk_id, document_name, content, similarity_score, metadata |
| **SearchResponse** | Full API response with results and timing info |
| **StatsResponse** | Database statistics (total documents, chunks, dimension, model name) |

## Running

```bash
uv run main
```

## Dependencies

- `pydantic` — data validation
- `pydantic-settings` — configuration management

## Role in the pipeline

Contract layer used by all components. **rag-loader** outputs `ChunkInput`, **rag-embedder** produces `ChunkWithEmbedding`, and **rag-retriever** uses `SearchRequest`/`SearchResponse` for its API.
