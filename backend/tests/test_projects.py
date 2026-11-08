"""Tests for projects API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from unittest.mock import patch
from pathlib import Path
import tempfile

from app.models.project import Project, ProjectStatus
from app.services.project_discovery import ProjectDiscoveryService


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
    # Targets are returned as list of objects with name and type
    assert len(data["targets"]) == len(sample_project_data["targets"])
    for i, target in enumerate(data["targets"]):
        assert target["name"] == sample_project_data["targets"][i]
        assert target["type"] == "library"
    # Dependencies are returned as list of objects with url and version
    assert len(data["dependencies"]) == len(sample_project_data["dependencies"])
    for i, dep in enumerate(data["dependencies"]):
        assert dep["url"] == sample_project_data["dependencies"][i]


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    """Test getting non-existent project returns 404."""
    response = await client.get("/api/projects/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient, session: AsyncSession):
    """Test pagination of projects list."""
    # Create multiple projects
    for i in range(5):
        proj = Project(name=f"Project{i}", path=f"/workspace/Project{i}", status=ProjectStatus.VALID)
        session.add(proj)
    await session.commit()

    # First page
    response = await client.get("/api/projects?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert data["total"] == 5

    # Second page
    response = await client.get("/api/projects?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 2

    # Third page
    response = await client.get("/api/projects?limit=2&offset=4")
    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) == 1
    assert data["limit"] == 2
    assert data["offset"] == 4


@pytest.mark.asyncio
async def test_scan_workspace(client: AsyncClient, session: AsyncSession, test_settings):
    """Test scan workspace endpoint creates new projects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        project_dir = workspace / "TestApp"
        project_dir.mkdir()
        (project_dir / "Package.swift").write_text("""
// swift-tools-version: 5.9
import PackageDescription
let package = Package(name: "TestApp", version: "1.0.0")
""")

        # Override workspace_root for this test
        test_settings.workspace_root = str(workspace)

        # Mock _validate_project to return True
        with patch.object(ProjectDiscoveryService, "_validate_project", return_value=True):
            response = await client.post("/api/projects/scan")

        assert response.status_code == 200
        data = response.json()
        assert data["scanned"] == 1
        assert data["added"] == 1
        assert data["updated"] == 0
        assert "TestApp" in data["added_projects"]
        assert len(data["updated_projects"]) == 0
        assert data["errors"] == []


@pytest.mark.asyncio
async def test_scan_workspace_updates_existing(client: AsyncClient, session: AsyncSession, test_settings):
    """Test scan workspace endpoint updates existing projects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        project_dir = workspace / "TestApp"
        project_dir.mkdir()
        (project_dir / "Package.swift").write_text("""
// swift-tools-version: 5.9
import PackageDescription
let package = Package(name: "TestApp", version: "1.0.0")
""")

        # Override workspace_root for this test
        test_settings.workspace_root = str(workspace)

        # Mock _validate_project to return True
        with patch.object(ProjectDiscoveryService, "_validate_project", return_value=True):
            # First scan - should add
            response = await client.post("/api/projects/scan")
            assert response.status_code == 200
            data = response.json()
            assert data["added"] == 1
            assert data["updated"] == 0

            # Update Package.swift
            (project_dir / "Package.swift").write_text("""
// swift-tools-version: 5.9
import PackageDescription
let package = Package(name: "TestApp", version: "2.0.0")
""")

            # Second scan - should update
            response = await client.post("/api/projects/scan")
            assert response.status_code == 200
            data = response.json()
            assert data["added"] == 0
            assert data["updated"] == 1
            assert "TestApp" in data["updated_projects"]
            assert len(data["added_projects"]) == 0


@pytest.mark.asyncio
async def test_scan_workspace_multiple_projects(client: AsyncClient, session: AsyncSession, test_settings):
    """Test scan workspace with multiple projects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create two projects
        for name in ["App1", "App2"]:
            project_dir = workspace / name
            project_dir.mkdir()
            (project_dir / "Package.swift").write_text(f"""
// swift-tools-version: 5.9
import PackageDescription
let package = Package(name: "{name}", version: "1.0.0")
""")

        test_settings.workspace_root = str(workspace)

        with patch.object(ProjectDiscoveryService, "_validate_project", return_value=True):
            response = await client.post("/api/projects/scan")

        assert response.status_code == 200
        data = response.json()
        assert data["scanned"] == 2
        assert data["added"] == 2
        assert set(data["added_projects"]) == {"App1", "App2"}


@pytest.mark.asyncio
async def test_scan_workspace_handles_errors(client: AsyncClient, session: AsyncSession, test_settings):
    """Test scan workspace handles errors gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        project_dir = workspace / "BadApp"
        project_dir.mkdir()
        (project_dir / "Package.swift").write_text("invalid swift code")

        test_settings.workspace_root = str(workspace)

        # Don't mock validation - let it fail
        response = await client.post("/api/projects/scan")

        # Should still return 200 but with errors
        assert response.status_code == 200
        data = response.json()
        # Project validation fails, so project may be marked invalid or not added
        assert "errors" in data
