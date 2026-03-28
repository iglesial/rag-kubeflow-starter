"""Semantic search endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from lib_embedding.embedding import EmbeddingClient
from lib_schemas.schemas import SearchRequest, SearchResponse

from rag_retriever.dependencies import get_db_session, get_embedding_client

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    session: AsyncSession = Depends(get_db_session),
    client: EmbeddingClient = Depends(get_embedding_client),
) -> SearchResponse:
    """
    Perform semantic search against pgvector.

    Encode the query, search by cosine similarity, return ranked results.

    Parameters
    ----------
    body : SearchRequest
        Search parameters (query, top_k, similarity_threshold).
    session : AsyncSession
        Database session (injected).
    client : EmbeddingClient
        Embedding client (injected).

    Returns
    -------
    SearchResponse
        Ranked search results with timing information.
    """
    raise NotImplementedError  # TODO: implement
