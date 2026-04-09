"""Semantic search endpoint."""

import time

from fastapi import APIRouter, Depends
from lib_embedding.embedding import EmbeddingClient
from lib_orm.models import DocumentChunk
from lib_schemas.schemas import SearchRequest, SearchResponse, SearchResult
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_retriever.dependencies import get_db_session, get_embedding_client

router = APIRouter()


@router.post("/search")
async def search(
    body: SearchRequest,
    session: AsyncSession = Depends(get_db_session),  # noqa: B008
    client: EmbeddingClient = Depends(get_embedding_client),  # noqa: B008
) -> SearchResponse:
    """
    Perform semantic search over document chunks.

    Embeds the query, searches pgvector using cosine distance, and returns
    ranked results filtered by similarity threshold.

    Parameters
    ----------
    body : SearchRequest
        The search request with query, top_k, and similarity_threshold.
    session : AsyncSession
        Injected database session.
    client : EmbeddingClient
        Injected embedding client.

    Returns
    -------
    SearchResponse
        Ranked search results with timing information.
    """
    # Embed the query

    ###########################
    query_embedding = vectors[0]

    # Search pgvector using cosine distance
    # 1 - cosine_distance gives cosine similarity
    similarity =

    # stmt = (
    #     select(??, ??)
    #     .where(similarity >= body.similarity_threshold)
    #     .order_by(similarity.desc())
    #     .limit(body.top_k)
    # )

    result = await session.execute(stmt)
    rows = result.all()
    search_time_ms = (time.perf_counter() - t1) * 1000

    # results = [
    #     SearchResult(
    #         chunk_id=row.DocumentChunk.id,
    #         document_name=row.DocumentChunk.??,
    #         content=row.DocumentChunk.??,
    #         similarity_score=float(row.??),
    #         metadata=row.DocumentChunk.metadata_,
    #     )
    #     for row in rows
    # ]

    return SearchResponse(
        query=body.query,
        results=results,
        total_results=len(results),
        embedding_time_ms=round(embedding_time_ms, 2),
        search_time_ms=round(search_time_ms, 2),
        query_embedding=query_embedding,
    )
