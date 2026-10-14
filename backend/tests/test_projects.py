"""Tests for projects API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.project import Project, ProjectStatus


@pytest.mark.asyncio
async def test_list_projects_empty(client: AsyncClient):
    """Test listing projects when none exist."""
    response = await client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["projects"] == []
    assert data["total"] == 0
    assert data["limit"] == 50
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_list_projects_with_data(client: AsyncClient, session: AsyncSession, sample_project_data: dict):
    """Test listing projects with existing data."""
    # Create a project directly in DB
    project = Project(**sample_project_data, status=ProjectStatus.VALID)
    session.add(project)
    await session.commit()
    await session.refresh(project)

    response = await client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["projects"]) == 1
    assert data["projects"][0]["name"] == sample_project_data["name"]
    assert data["projects"][0]["status"] == "valid"


@pytest.mark.asyncio
async def test_list_projects_filter_by_status(client: AsyncClient, session: AsyncSession):
    """Test filtering projects by status."""
    # Create projects with different statuses
    valid_project = Project(name="ValidApp", path="/workspace/ValidApp", status=ProjectStatus.VALID)
    invalid_project = Project(name="InvalidApp", path="/workspace/InvalidApp", status=ProjectStatus.INVALID)
    session.add_all([valid_project, invalid_project])
    await session.commit()

    response = await client.get("/api/projects?status=valid")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["projects"][0]["name"] == "ValidApp"


@pytest.mark.asyncio
async def test_get_project_by_id(client: AsyncClient, session: AsyncSession, sample_project_data: dict):
    """Test getting a single project by ID."""
    project = Project(**sample_project_data, status=ProjectStatus.VALID)
    session.add(project)
    await session.commit()
    await session.refresh(project)

    response = await client.get(f"/api/projects/{project.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project.id
    assert data["name"] == sample_project_data["name"]
    assert data["package_version"] == sample_project_data["package_version"]
    assert data["targets"] == sample_project_data["targets"]
    assert data["dependencies"] == sample_project_data["dependencies"]


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    """Test getting non-existent project returns 404."""
    response = await client.get("/api/projects/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient, session: AsyncSession):
    """Test pagination of projects list."""
    # Create 5 projects
    projects = [
        Project(name=f"App{i}", path=f"/workspace/App{i}", status=ProjectStatus.VALID)
        for i in range(5)
    ]
    session.add_all(projects)
    await session.commit()

    # Test limit
    response = await client.get("/api/projects?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) == 2
    assert data["limit"] == 2
    assert data["total"] == 5

    # Test offset
    response = await client.get("/api/projects?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) == 2
    assert data["offset"] == 2