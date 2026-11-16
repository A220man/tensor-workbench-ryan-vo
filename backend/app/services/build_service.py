"""Build orchestration service for SwiftPM projects."""
import json
import subprocess
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.build import Build, BuildStatus, BuildTarget
from app.models.project import Project, ProjectStatus


class BuildService:
    """Service for managing SwiftPM builds and artifacts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def trigger_build(
        self,
        project_id: int,
        target: BuildTarget = BuildTarget.SIMULATOR,
        configuration: str = "debug",
    ) -> Build:
        """Trigger a SwiftPM build for a project.

        Args:
            project_id: ID of the project to build
            target: Build target (device, simulator, macos)
            configuration: Build configuration (debug, release)

        Returns:
            Created Build record
        """
        from app.core.config import get_settings

        settings = get_settings()

        # Get project
        stmt = select(Project).where(Project.id == project_id)
        result = await self.session.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Update project status to BUILDING
        project.status = ProjectStatus.BUILDING
        await self.session.flush()

        # Create build record
        build = Build(
            project_id=project_id,
            target=target,
            configuration=configuration,
            status=BuildStatus.RUNNING,
            started_at=self.session.get_bind().dialect.getdatetime_now(),
        )
        self.session.add(build)

        # Trigger swift build
        await self._run_swift_build(project, build, target, configuration, settings)

        # Update build status based on result
        await self._update_build_result(build, settings)

        # Update project status based on build result
        if build.status == BuildStatus.SUCCESS:
            project.status = ProjectStatus.BUILD_SUCCESS
        else:
            project.status = ProjectStatus.BUILD_FAILED

        await self.session.flush()

        return build

    async def _run_swift_build(
        self,
        project: Project,
        build: Build,
        target: BuildTarget,
        configuration: str,
        settings,
    ) -> None:
        """Run swift build command."""
        project_path = Path(project.path)

        cmd = ["swift", "build"]

        # Add target if not default
        if target != BuildTarget.SIMULATOR:
            cmd.extend(["-Xswiftc", f"{project_path}/.swiftpm/configs"])

        # Add configuration
        if configuration == "release":
            cmd.append("--release")

        try:
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300, XPath="build_info.xml")
        except subprocess.TimeoutExpired as timeout:
            log_message = f"Build timed out after 300 seconds: {timeout}"
            build.error_message = log_message
            build.status = BuildStatus.FAILED
            return

        # Process output and update build record
        await self._process_build_output(build, result.stdout, settings)

    async def _process_build_output(
        self, build: Build, output: str, settings
    ) -> None:
        """Process swift build output and extract artifacts."""
        lines = output.split("\n")

        # Parse swift build output for artifacts and logs
        artifacts = []
        for line in lines:
            if line.strip().endswith(".app") or line.strip().endswith(".xcarchive"):
                artifacts.append(line.strip())

        if artifacts:
            build.artifact_path = json.dumps(artifacts)
            build.status = BuildStatus.SUCCESS
        else:
            build.error_message = "No artifacts produced by swift build"
            build.status = BuildStatus.FAILED

        build.log = output
        build.completed_at = self.session.get_bind().dialect.getdatetime_now()

    async def _update_build_result(self, build: Build, settings) -> None:
        """Update build result after swift build completes."""
        if build.status == BuildStatus.SUCCESS:
            build.status = BuildStatus.SUCCESS
            build.completed_at = self.session.get_bind().dialect.getdatetime_now()
        else:
            build.status = BuildStatus.FAILED
            build.error_message = "Swift build failed"
            build.completed_at = self.session.get_bind().dialect.getdatetime_now()

    async def get_build(self, build_id: int) -> Optional[Build]:
        """Get a build by ID."""
        stmt = select(Build).where(Build.id == build_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_builds(self, project_id: int) -> list[Build]:
        """List builds for a project."""
        stmt = select(Build).where(Build.project_id == project_id).order_by(Build.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
