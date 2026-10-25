"""Tests for project discovery service."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.project_discovery import ProjectDiscoveryService
from app.models.project import Project, ProjectStatus


@pytest.mark.asyncio
async def test_parse_package_swift():
    """Test parsing Package.swift for metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        package_swift = Path(tmpdir) / "Package.swift"
        package_swift.write_text("""
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "TestApp",
    version: "1.2.3",
    targets: [
        .target(name: "TestApp"),
        .testTarget(name: "TestAppTests"),
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-argument-parser", from: "1.2.0"),
    ]
)
""")

        service = ProjectDiscoveryService(None)  # type: ignore
        metadata = service._parse_package_swift(package_swift)

        assert metadata["swift_tools_version"] == "5.9"
        assert metadata["name"] == "TestApp"
        assert metadata["version"] == "1.2.3"
        assert "TestApp" in metadata["targets"]
        assert "TestAppTests" in metadata["targets"]
        assert any("swift-argument-parser" in d for d in metadata["dependencies"])


@pytest.mark.asyncio
async def test_validate_project_success():
    """Test project validation with mocked swift command."""
    service = ProjectDiscoveryService(None)  # type: ignore

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout='{"name": "TestApp"}')
        result = await service._validate_project(Path("/fake/path"))
        assert result is True
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_validate_project_failure():
    """Test project validation failure."""
    service = ProjectDiscoveryService(None)  # type: ignore

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        result = await service._validate_project(Path("/fake/path"))
        assert result is False


@pytest.mark.asyncio
async def test_validate_project_timeout():
    """Test project validation timeout."""
    service = ProjectDiscoveryService(None)  # type: ignore

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = TimeoutError()
        result = await service._validate_project(Path("/fake/path"))
        assert result is False


@pytest.mark.asyncio
async def test_scan_workspace_creates_projects():
    """Test scanning workspace creates project records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        project_dir = workspace / "MyApp"
        project_dir.mkdir()
        (project_dir / "Package.swift").write_text("""
    // swift-tools-version: 5.9
    import PackageDescription
    let package = Package(name: "MyApp")
    """)

        # Mock session
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.models.base import Base

        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            service = ProjectDiscoveryService(session)
            # Mock validation to return True (swift not available in test env)
            with patch.object(service, "_validate_project", return_value=True):
                projects, added, updated = await service.scan_workspace(workspace)

            assert len(projects) == 1
            assert added == 1
            assert updated == 0
            assert projects[0].name == "MyApp"
            assert projects[0].path == str(project_dir)
            assert projects[0].status == ProjectStatus.VALID

        await engine.dispose()


@pytest.mark.asyncio
async def test_scan_workspace_updates_existing_projects():
    """Test scanning workspace updates existing project records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        project_dir = workspace / "MyApp"
        project_dir.mkdir()
        (project_dir / "Package.swift").write_text("""
    // swift-tools-version: 5.9
    import PackageDescription
    let package = Package(name: "MyApp", version: "1.0.0")
    """)

        # Mock session
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.models.base import Base

        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            service = ProjectDiscoveryService(session)
            # Mock validation to return True (swift not available in test env)
            with patch.object(service, "_validate_project", return_value=True):
                # First scan - should add the project
                projects, added, updated = await service.scan_workspace(workspace)

            assert len(projects) == 1
            assert added == 1
            assert updated == 0
            assert projects[0].name == "MyApp"
            assert projects[0].package_version == "1.0.0"

            # Second scan with updated Package.swift - should update the project
            (project_dir / "Package.swift").write_text("""
    // swift-tools-version: 5.9
    import PackageDescription
    let package = Package(name: "MyApp", version: "2.0.0")
    """)

            async with session_factory() as session:
                service = ProjectDiscoveryService(session)
                with patch.object(service, "_validate_project", return_value=True):
                    projects, added, updated = await service.scan_workspace(workspace)

            assert len(projects) == 1
            assert added == 0
            assert updated == 1
            assert projects[0].name == "MyApp"
            assert projects[0].package_version == "2.0.0"

        await engine.dispose()