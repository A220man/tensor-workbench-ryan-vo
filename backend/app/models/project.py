"""Project model for SwiftPM projects."""
import json
from datetime import datetime, timezone
from enum import Enum as PyEnum
from pathlib import Path
from typing import Optional

from sqlalchemy import Enum, Index, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ProjectStatus(PyEnum):
    """Status of a SwiftPM project."""

    UNKNOWN = "unknown"
    VALID = "valid"
    INVALID = "invalid"
    BUILDING = "building"
    BUILD_FAILED = "build_failed"
    BUILD_SUCCESS = "build_success"


class Project(Base, TimestampMixin):
    """SwiftPM project discovered in workspace."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True, index=True)
    package_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    package_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    swift_tools_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, native_enum=False),
        default=ProjectStatus.UNKNOWN,
        nullable=False,
        index=True,
    )
    last_build_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    targets: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True, default=list)
    dependencies: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True, default=list)

    # Relationships
    builds: Mapped[list["Build"]] = relationship(
        "Build", back_populates="project", lazy="selectin", order_by="Build.created_at.desc()"
    )

    __table_args__ = (
        Index("ix_projects_path_status", "path", "status"),
    )

    @property
    def package_swift_path(self) -> Path:
        return Path(self.path) / "Package.swift"

    @property
    def is_valid_swiftpm(self) -> bool:
        return self.package_swift_path.exists()

    @property
    def targets_list(self) -> list[str]:
        return self.targets or []

    @property
    def dependencies_list(self) -> list[str]:
        return self.dependencies or []

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, path={self.path}, status={self.status.value})>"