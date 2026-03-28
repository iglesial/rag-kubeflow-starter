"""Health and readiness probe endpoints."""

from typing import Any

from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """
    Return a simple health check.

    Returns
    -------
    dict[str, str]
        Always ``{"status": "ok"}``.
    """
    raise NotImplementedError  # TODO: implement


@router.get("/ready")
async def ready(response: Response) -> dict[str, Any]:
    """
    Check readiness of database and embedding model.

    Returns 200 if all healthy, 503 otherwise.

    Parameters
    ----------
    response : Response
        FastAPI response object (to set status code).

    Returns
    -------
    dict[str, Any]
        Dict with keys ``status``, ``db``, ``model``.
    """
    raise NotImplementedError  # TODO: implement
