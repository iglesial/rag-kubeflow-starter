# rag-pipeline

Kubeflow Pipeline definitions for the RAG system. Orchestrates the ingestion workflow.

## What it does

- Defines a **rag_ingestion_pipeline** that chains **rag-loader** → **rag-embedder** as KFP container components
- Compiles the pipeline to a YAML manifest (`rag-ingestion-pipeline.yaml`)
- Optionally submits pipeline runs to a Kubeflow Pipelines API endpoint

## Pipeline parameters

| Parameter | Description |
|---|---|
| `input_dir` | Directory containing source documents |
| `chunk_size` | Text chunk size in characters |
| `chunk_overlap` | Overlap between chunks |
| `db_url` | PostgreSQL connection URL |
| `embedding_model` | Sentence-transformers model name |
| `batch_size` | Embedding batch size |

## Dependencies

- `kfp` — Kubeflow Pipelines SDK
- `lib-schemas` — data schemas
- `pydantic-settings` — configuration

## Running

```bash
uv run main --pipeline_name rag-ingestion --input_dir data/documents --kubeflow_host "http://localhost:8080" --compile_only true
```

This compiles the pipeline YAML and optionally submits it to a Kubeflow cluster.

## Role in the pipeline

Orchestration layer. Defines the containerized DAG that coordinates **rag-loader** and **rag-embedder** for repeatable document ingestion on Kubeflow.
