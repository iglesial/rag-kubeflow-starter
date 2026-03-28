"""Document statistics endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from lib_schemas.schemas import StatsResponse

from rag_retriever.dependencies import get_db_session

router = APIRouter(prefix="/documents")


@router.get("/stats", response_model=StatsResponse)
async def stats(
    session: AsyncSession = Depends(get_db_session),
) -> StatsResponse:
    """
    Return document and chunk statistics.

    Parameters
    ----------
    session : AsyncSession
        Database session (injected).

    Returns
    -------
    StatsResponse
        Total documents, chunks, embedding dimension, and model name.
    """
    raise NotImplementedError  # TODO: implement
