"""Definition of the health routes."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

# Not authentication or authorization required to get the health status.
health_router = APIRouter(
    prefix="/v1/health",
    tags=["Health"],
)


class HealthResponse(BaseModel):
    status: Literal["ok"] = Field(default="ok")


@health_router.get("")
async def health_route() -> dict:
    """Health check endpoint.

    Returns:
        A simple health status response.
    """
    return {"status": "ok", "hot_reload_test": "Hot reload is working!"}
