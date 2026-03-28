"""KFP pipeline definition for RAG ingestion."""

from kfp import dsl

from rag_pipeline.components.embedder import embedder_component
from rag_pipeline.components.loader import loader_component


@dsl.pipeline(
    name="RAG Ingestion Pipeline",
    description="Load documents, chunk, embed, and store in pgvector.",
)
def rag_ingestion_pipeline(
    input_dir: str = "/data/documents",
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    db_url: str = "postgresql+asyncpg://rag:rag@host.docker.internal:5432/rag",
    embedding_model: str = "all-MiniLM-L6-v2",
    batch_size: int = 32,
) -> None:
    """
    RAG ingestion pipeline: loader -> embedder.

    Parameters
    ----------
    input_dir : str
        Path to documents inside the loader container.
    chunk_size : int
        Maximum characters per chunk.
    chunk_overlap : int
        Overlap between consecutive chunks.
    db_url : str
        PostgreSQL connection string (use host.docker.internal for Kind).
    embedding_model : str
        Sentence-transformers model name.
    batch_size : int
        Batch size for embedding.
    """
    raise NotImplementedError  # TODO: implement
