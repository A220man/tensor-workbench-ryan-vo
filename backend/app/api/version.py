"""Version endpoint."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import get_settings


router = APIRouter(prefix="/version", tags=["version"])


class VersionResponse(BaseModel):
    name: str
    version: str
    environment: str
    build_date: str | None = None
    git_commit: str | None = None


@router.get("", response_model=VersionResponse)
async def get_version(settings = Depends(get_settings)) -> VersionResponse:
    """Get application version information."""
    return VersionResponse(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )