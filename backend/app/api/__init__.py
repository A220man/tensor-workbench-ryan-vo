"""API package exports."""
from app.api.health import router as health_router
from app.api.version import router as version_router
from app.api.projects import router as projects_router

__all__ = ["health_router", "version_router", "projects_router"]