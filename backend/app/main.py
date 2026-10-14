"""Main FastAPI application."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import health_router, version_router, projects_router
from app.core.config import get_settings
from app.core.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    settings = get_settings()
    # Ensure data directories exist (handle read-only filesystems gracefully)
    for path_str in [settings.workspace_root, "data"]:
        try:
            Path(path_str).mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError):
            # In test environments or read-only filesystems, directory may not be creatable
            pass

    await init_db()

    yield

    # Shutdown
    await close_db()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Cross-platform Xcode replacement: build and deploy iOS apps with SwiftPM",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(version_router, prefix=settings.api_prefix)
    app.include_router(projects_router, prefix=settings.api_prefix)

    # Serve frontend build in production
    frontend_dist = Path("frontend/dist")
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug,
        workers=settings.backend_workers if not settings.debug else 1,
    )