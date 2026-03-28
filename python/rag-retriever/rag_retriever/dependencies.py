"""FastAPI dependency injection and shared resource management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from lib_embedding.embedding import EmbeddingClient

_engine: AsyncEngine | None = None
_embedding_client: EmbeddingClient | None = None


async def init_dependencies() -> None:
    """Initialize the database engine and embedding client."""
    raise NotImplementedError  # TODO: implement


async def shutdown_dependencies() -> None:
    """Dispose the database engine and release resources."""
    raise NotImplementedError  # TODO: implement


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """
    Yield an async database session.

    Commits on success, rolls back on error.

    Yields
    ------
    AsyncSession
        An active database session.

    Raises
    ------
    RuntimeError
        If the database engine has not been initialized.
    """
    raise NotImplementedError  # TODO: implement
    yield  # type: ignore[misc]  # make it a generator


def get_embedding_client() -> EmbeddingClient:
    """
    Return the pre-loaded embedding client.

    Returns
    -------
    EmbeddingClient
        The embedding client singleton.

    Raises
    ------
    RuntimeError
        If the embedding client has not been initialized.
    """
    raise NotImplementedError  # TODO: implement


async def check_db_health() -> bool:
    """
    Check database connectivity by executing ``SELECT 1``.

    Returns
    -------
    bool
        True if the database is reachable.
    """
    raise NotImplementedError  # TODO: implement


def check_model_health() -> bool:
    """
    Check whether the embedding model is loaded.

    Returns
    -------
    bool
        True if ``_embedding_client`` is not None.
    """
    raise NotImplementedError  # TODO: implement
