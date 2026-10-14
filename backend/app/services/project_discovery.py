"""Project discovery service - scans workspace for SwiftPM projects."""
import json
import re
import subprocess
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus
from app.models.build import Build


class ProjectDiscoveryService:
    """Service for discovering and managing SwiftPM projects."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def scan_workspace(self, workspace_root: Path) -> list[Project]:
        """Scan workspace for Package.swift files and create/update projects."""
        projects = []
        for package_swift in workspace_root.rglob("Package.swift"):
            project = await self._process_package_swift(package_swift)
            if project:
                projects.append(project)
        await self.session.commit()
        return projects

    async def _process_package_swift(self, package_swift: Path) -> Optional[Project]:
        """Process a single Package.swift file."""
        project_path = package_swift.parent
        relative_path = project_path.relative_to(project_path.anchor) if project_path.is_absolute() else project_path

        # Parse Package.swift for metadata
        metadata = self._parse_package_swift(package_swift)

        # Check if project exists
        stmt = select(Project).where(Project.path == str(project_path))
        result = await self.session.execute(stmt)
        project = result.scalar_one_or_none()

        if project is None:
            project = Project(
                name=metadata.get("name", project_path.name),
                path=str(project_path),
                package_name=metadata.get("name"),
                package_version=metadata.get("version"),
                swift_tools_version=metadata.get("swift_tools_version"),
                description=metadata.get("description"),
                targets=json.dumps(metadata.get("targets", [])),
                dependencies=json.dumps(metadata.get("dependencies", [])),
                status=ProjectStatus.UNKNOWN,
            )
            self.session.add(project)
        else:
            # Update metadata
            project.name = metadata.get("name", project.name)
            project.package_name = metadata.get("name", project.package_name)
            project.package_version = metadata.get("version", project.package_version)
            project.swift_tools_version = metadata.get("swift_tools_version", project.swift_tools_version)
            project.description = metadata.get("description", project.description)
            project.targets = json.dumps(metadata.get("targets", []))
            project.dependencies = json.dumps(metadata.get("dependencies", []))

        # Validate project by running swift package describe
        is_valid = await self._validate_project(project_path)
        project.status = ProjectStatus.VALID if is_valid else ProjectStatus.INVALID

        return project

    def _parse_package_swift(self, package_swift: Path) -> dict:
        """Parse Package.swift for basic metadata."""
        content = package_swift.read_text(encoding="utf-8")
        metadata = {}

        # Extract swift-tools-version
        tools_match = re.search(r'//\s*swift-tools-version:\s*([\d.]+)', content)
        if tools_match:
            metadata["swift_tools_version"] = tools_match.group(1)

        # Extract package name
        name_match = re.search(r'name:\s*"([^"]+)"', content)
        if name_match:
            metadata["name"] = name_match.group(1)

        # Extract version (if specified)
        version_match = re.search(r'version:\s*"([^"]+)"', content)
        if version_match:
            metadata["version"] = version_match.group(1)

        # Extract targets (simplified - just target names)
        targets = []
        # Match .target(name: "Name") or .executableTarget(name: "Name")
        target_pattern = r'\.(?:target|executableTarget|testTarget)\s*\(\s*name:\s*"([^"]+)"'
        for match in re.finditer(target_pattern, content):
            targets.append(match.group(1))
        metadata["targets"] = targets

        # Extract dependencies (simplified)
        deps = []
        dep_pattern = r'\.package\s*\(\s*(?:url|path):\s*"([^"]+)"'
        for match in re.finditer(dep_pattern, content):
            deps.append(match.group(1))
        metadata["dependencies"] = deps

        return metadata

    async def _validate_project(self, project_path: Path) -> bool:
        """Validate a SwiftPM project by running swift package describe."""
        try:
            result = subprocess.run(
                ["swift", "package", "describe", "--type", "json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
            return False

    async def get_project(self, project_id: int) -> Optional[Project]:
        """Get a project by ID."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_project_by_path(self, path: str) -> Optional[Project]:
        """Get a project by path."""
        stmt = select(Project).where(Project.path == path)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_projects(
        self,
        status: Optional[ProjectStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Project]:
        """List projects with optional filtering."""
        stmt = select(Project).order_by(Project.updated_at.desc()).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Project.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_build(self, project_id: int) -> Optional[Build]:
        """Get the latest build for a project."""
        from app.models.build import Build
        stmt = select(Build).where(Build.project_id == project_id).order_by(Build.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()