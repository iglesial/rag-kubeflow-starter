# rag-loader

Document reader and chunker for the RAG system. First step in the ingestion pipeline.

## What it does

1. **Reads** `.txt` and `.md` files from an input directory (with file metadata extraction)
2. **Chunks** each document using a recursive character-level text splitter:
   - Configurable chunk size (default 512 chars) and overlap (default 64 chars)
   - Separator hierarchy: paragraphs → newlines → sentences → words → characters
   - Merges small segments and adds overlap between chunks
3. **Outputs** `chunks.json` containing `ChunkInput` objects (document_name, chunk_index, content, metadata)

## Dependencies

- `lib-schemas` — data schemas (`ChunkInput`)
- `pydantic-settings` — configuration

## Running

```bash
python -m rag_loader.main
```

Runs as a containerized Kubeflow pipeline component (`Dockerfile` included).

## Role in the pipeline

Ingestion stage. Converts raw documents into uniformly-sized, overlapping chunks suitable for embedding. Output feeds directly into **rag-embedder**.
