"""Test configuration and fixtures."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.database import get_session
from app.main import create_app
from app.models.base import Base
from app.models.project import Project, ProjectStatus


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test settings override."""
    return Settings(
        database_url=TEST_DATABASE_URL,
        environment="test",
        debug=True,
        workspace_root="/tmp/test-workspace",
        demo_mode=True,
    )


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session_factory(test_engine):
    """Create test session factory."""
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def session(test_session_factory) -> AsyncSession:
    """Provide a test database session."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def app(test_settings, test_session_factory):
    """Create test FastAPI app with overridden dependencies."""
    from fastapi import FastAPI
    from app.core.database import get_session as get_session_dep

    app = create_app()

    async def override_get_session() -> AsyncSession:
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session_dep] = override_get_session

    # Override settings
    from app.core.config import get_settings
    app.dependency_overrides[get_settings] = lambda: test_settings

    return app


@pytest_asyncio.fixture(scope="function")
async def client(app):
    """Test client for making requests."""
    from httpx import ASGITransport, AsyncClient
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_project_data() -> dict:
    """Sample project data for tests."""
    return {
        "name": "TestApp",
        "path": "/workspace/TestApp",
        "package_name": "TestApp",
        "package_version": "1.0.0",
        "swift_tools_version": "5.9",
        "description": "A test SwiftPM project",
        "targets": ["TestApp", "TestAppTests"],
        "dependencies": ["https://github.com/apple/swift-argument-parser"],
    }