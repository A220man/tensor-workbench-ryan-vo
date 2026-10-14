"""Health check endpoint."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str


@router.get("", response_model=HealthResponse)
async def health_check(
    session: AsyncSession = Depends(get_session),
    settings = Depends(get_settings),
) -> HealthResponse:
    """Health check endpoint with database connectivity test."""
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="healthy" if db_status == "ok" else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        database=db_status,
    )