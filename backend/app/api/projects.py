"""Projects API endpoints."""
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models.project import Project, ProjectStatus
from app.models.build import Build, BuildStatus
from app.services.project_discovery import ProjectDiscoveryService


router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectTarget(BaseModel):
    name: str
    type: str  # "executable", "library", "test"


class ProjectDependency(BaseModel):
    url: str
    version: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    path: str
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    swift_tools_version: Optional[str] = None
    description: Optional[str] = None
    targets: list[ProjectTarget]
    dependencies: list[ProjectDependency]
    status: ProjectStatus
    created_at: str
    updated_at: str
    latest_build: Optional["BuildSummary"] = None

    class Config:
        from_attributes = True


class BuildSummary(BaseModel):
    id: int
    project_id: int
    status: BuildStatus
    target: Optional[str] = None
    configuration: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    log: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int
    limit: int
    offset: int


class ScanResponse(BaseModel):
    scanned: int
    added: int
    updated: int
    added_projects: list[str] = Field(default_factory=list)
    updated_projects: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# Forward reference resolution
ProjectResponse.model_rebuild()


def parse_targets(targets_data: Optional[list]) -> list[ProjectTarget]:
    """Parse targets from list (already deserialized by SQLAlchemy JSON column)."""
    if not targets_data:
        return []
    result = []
    for t in targets_data:
        if isinstance(t, str):
            # Old format: list of strings
            result.append(ProjectTarget(name=t, type="library"))
        elif isinstance(t, dict):
            # New format: list of objects with name and type
            result.append(ProjectTarget(name=t.get("name", ""), type=t.get("type", "library")))
    return result


def parse_dependencies(deps_data: Optional[list]) -> list[ProjectDependency]:
    """Parse dependencies from list (already deserialized by SQLAlchemy JSON column)."""
    if not deps_data:
        return []
    result = []
    for d in deps_data:
        if isinstance(d, str):
            # Old format: list of strings (URLs)
            result.append(ProjectDependency(url=d))
        elif isinstance(d, dict):
            # New format: list of objects with url and version
            result.append(ProjectDependency(url=d.get("url", ""), version=d.get("version")))
    return result


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    limit: int = 50,
    offset: int = 0,
    status: Optional[ProjectStatus] = None,
    session: AsyncSession = Depends(get_session),
) -> ProjectListResponse:
    """List discovered SwiftPM projects."""
    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload

    stmt = select(Project)
    if status:
        stmt = stmt.where(Project.status == status)
    stmt = stmt.order_by(Project.updated_at.desc())
    stmt = stmt.limit(limit).offset(offset)

    result = await session.execute(stmt)
    projects = list(result.scalars().all())

    count_stmt = select(func.count(Project.id))
    if status:
        count_stmt = count_stmt.where(Project.status == status)
    count_result = await session.execute(count_stmt)
    total = count_result.scalar_one()

    project_responses = []
    for project in projects:
        targets = parse_targets(project.targets)
        deps = parse_dependencies(project.dependencies)

        latest_build = None
        build_stmt = select(Build).where(Build.project_id == project.id).order_by(Build.started_at.desc()).limit(1)
        build_result = await session.execute(build_stmt)
        build = build_result.scalar_one_or_none()
        if build:
            latest_build = BuildSummary(
                id=build.id,
                project_id=build.project_id,
                status=build.status,
                target=build.target,
                configuration=build.configuration,
                started_at=build.started_at.isoformat() if build.started_at else "",
                completed_at=build.completed_at.isoformat() if build.completed_at else None,
                log=build.log,
            )

        project_responses.append(ProjectResponse(
            id=project.id,
            name=project.name,
            path=project.path,
            package_name=project.package_name,
            package_version=project.package_version,
            swift_tools_version=project.swift_tools_version,
            description=project.description,
            targets=targets,
            dependencies=deps,
            status=project.status,
            created_at=project.created_at.isoformat() if project.created_at else "",
            updated_at=project.updated_at.isoformat() if project.updated_at else "",
            latest_build=latest_build,
        ))

    return ProjectListResponse(
        projects=project_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/scan", response_model=ScanResponse)
async def scan_workspace(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    settings = Depends(get_settings),
) -> ScanResponse:
    """Trigger a workspace scan for SwiftPM projects."""
    service = ProjectDiscoveryService(session)
    workspace_root = Path(settings.workspace_root)

    errors = []
    added = 0
    updated = 0
    added_projects = []
    updated_projects = []

    async def run_scan():
        nonlocal added, updated, added_projects, updated_projects, errors
        try:
            projects, added, updated = await service.scan_workspace(workspace_root)
            added_projects = [p.name for p in projects]
            updated_projects = []
        except Exception as e:
            errors.append(str(e))

    # Run scan in background for better responsiveness
    background_tasks.add_task(run_scan)
    
    # For immediate response, we still run synchronously
    await run_scan()

    return ScanResponse(
        scanned=added + updated,
        added=added,
        updated=updated,
        added_projects=added_projects,
        updated_projects=updated_projects,
        errors=errors,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    """Get a single project by ID."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project not found")

    targets = parse_targets(project.targets)
    deps = parse_dependencies(project.dependencies)

    latest_build = None
    build_stmt = select(Build).where(Build.project_id == project.id).order_by(Build.started_at.desc()).limit(1)
    build_result = await session.execute(build_stmt)
    build = build_result.scalar_one_or_none()
    if build:
        latest_build = BuildSummary(
            id=build.id,
            project_id=build.project_id,
            status=build.status,
            target=build.target,
            configuration=build.configuration,
            started_at=build.started_at.isoformat() if build.started_at else "",
            completed_at=build.completed_at.isoformat() if build.completed_at else None,
            log=build.log,
        )

    return ProjectResponse(
        id=project.id,
        name=project.name,
        path=project.path,
        package_name=project.package_name,
        package_version=project.package_version,
        swift_tools_version=project.swift_tools_version,
        description=project.description,
        targets=targets,
        dependencies=deps,
        status=project.status,
        created_at=project.created_at.isoformat() if project.created_at else "",
        updated_at=project.updated_at.isoformat() if project.updated_at else "",
        latest_build=latest_build,
    )
