"""Projects API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import get_settings
from app.core.database import get_session
from app.models.project import Project, ProjectStatus
from app.models.build import Build, BuildStatus, BuildTarget
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
    status: str
    description: Optional[str] = None
    targets: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    latest_build: Optional["BuildSummary"] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class BuildSummary(BaseModel):
    id: int
    target: str
    configuration: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None

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
    errors: list[str] = Field(default_factory=list)


# Forward reference resolution
ProjectResponse.model_rebuild()


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    status: Optional[ProjectStatus] = Query(None, description="Filter by project status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    settings = Depends(get_settings),
) -> ProjectListResponse:
    """List discovered SwiftPM projects."""
    service = ProjectDiscoveryService(session)

    # Get total count
    count_stmt = select(func.count(Project.id))
    if status:
        count_stmt = count_stmt.where(Project.status == status)
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    # Get projects
    projects = await service.list_projects(status=status, limit=limit, offset=offset)

    # Build response with latest build info
    project_responses = []
    for project in projects:
        latest_build = await service.get_latest_build(project.id)
        build_summary = None
        if latest_build:
            build_summary = BuildSummary(
                id=latest_build.id,
                target=latest_build.target.value,
                configuration=latest_build.configuration,
                status=latest_build.status.value,
                started_at=latest_build.started_at.isoformat() if latest_build.started_at else None,
                completed_at=latest_build.completed_at.isoformat() if latest_build.completed_at else None,
                duration_seconds=latest_build.duration_seconds,
            )

        project_responses.append(ProjectResponse(
            id=project.id,
            name=project.name,
            path=project.path,
            package_name=project.package_name,
            package_version=project.package_version,
            swift_tools_version=project.swift_tools_version,
            status=project.status.value,
            description=project.description,
            targets=project.targets_list,
            dependencies=project.dependencies_list,
            latest_build=build_summary,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
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

    try:
        projects = await service.scan_workspace(workspace_root)
        for project in projects:
            # We can't easily distinguish added vs updated here without more logic
            # For now, count all as scanned
            pass
    except Exception as e:
        errors.append(str(e))

    return ScanResponse(
        scanned=len(projects) if 'projects' in locals() else 0,
        added=added,
        updated=updated,
        errors=errors,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    """Get a single project by ID."""
    service = ProjectDiscoveryService(session)
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    latest_build = await service.get_latest_build(project.id)
    build_summary = None
    if latest_build:
        build_summary = BuildSummary(
            id=latest_build.id,
            target=latest_build.target.value,
            configuration=latest_build.configuration,
            status=latest_build.status.value,
            started_at=latest_build.started_at.isoformat() if latest_build.started_at else None,
            completed_at=latest_build.completed_at.isoformat() if latest_build.completed_at else None,
            duration_seconds=latest_build.duration_seconds,
        )

    return ProjectResponse(
        id=project.id,
        name=project.name,
        path=project.path,
        package_name=project.package_name,
        package_version=project.package_version,
        swift_tools_version=project.swift_tools_version,
        status=project.status.value,
        description=project.description,
        targets=project.targets_list,
        dependencies=project.dependencies_list,
        latest_build=build_summary,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )

