"""Tests for health and version endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "environment" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_version_endpoint(client: AsyncClient):
    """Test version endpoint."""
    response = await client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "tensor-workbench-ryan-vo"
    assert "version" in data
    assert "environment" in data