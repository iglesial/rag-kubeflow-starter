# lib-embedding

Embedding client library for the RAG system. Wraps [sentence-transformers](https://www.sbert.net/) to generate text embeddings.

## What it does

- **EmbeddingClient**: Loads a pre-trained sentence-transformers model and encodes text into dense vector embeddings
- **EmbeddingSettings**: Environment-based configuration (model name, vector dimension) using the `RAG_` prefix

Default model: `all-MiniLM-L6-v2` (384-dimensional vectors).

## Running

```bash
uv run main --embedding_model all-MiniLM-L6-v2 --vector_dim 384
```

## Usage

```python
from lib_embedding.embedding import EmbeddingClient

client = EmbeddingClient(model_name="all-MiniLM-L6-v2")
vectors = client.encode(["Hello world", "Another sentence"], batch_size=32)
print(client.dimension)  # 384
```

## Dependencies

- `pydantic-settings` — configuration management
- `sentence-transformers` — text embedding generation

## Role in the pipeline

Foundation library used by **rag-embedder** (to vectorize document chunks) and **rag-retriever** (to vectorize search queries).
