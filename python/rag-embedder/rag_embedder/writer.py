"""Batch writer for pgvector storage."""

from sqlalchemy.ext.asyncio import AsyncSession

from lib_schemas.schemas import ChunkWithEmbedding


async def write_chunks(session: AsyncSession, chunks: list[ChunkWithEmbedding]) -> int:
    """
    Write embedding chunks to the database with upsert logic.

    For each chunk, look up an existing ``DocumentChunk`` by
    ``(document_name, chunk_index)``. If found, update it in place.
    If not found, create a new row.

    Parameters
    ----------
    session : AsyncSession
        SQLAlchemy async session.
    chunks : list[ChunkWithEmbedding]
        Chunks with embeddings to write.

    Returns
    -------
    int
        Number of rows affected (inserted or updated).
    """
    raise NotImplementedError  # TODO: implement
