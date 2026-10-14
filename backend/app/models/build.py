"""Build model for tracking build history."""
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class BuildStatus(PyEnum):
    """Status of a build."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BuildTarget(PyEnum):
    """Build target platform."""

    DEVICE = "device"  # arm64-apple-ios
    SIMULATOR = "simulator"  # arm64-apple-ios-simulator
    MACOS = "macos"  # x86_64-apple-macos or arm64-apple-macos


class Build(Base, TimestampMixin):
    """Build record for a project."""

    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    target: Mapped[BuildTarget] = mapped_column(Enum(BuildTarget, native_enum=False), nullable=False)
    configuration: Mapped[str] = mapped_column(String(32), default="debug", nullable=False)  # debug, release
    status: Mapped[BuildStatus] = mapped_column(
        Enum(BuildStatus, native_enum=False),
        default=BuildStatus.PENDING,
        nullable=False,
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    log_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artifact_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    swift_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sdk_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="builds", lazy="selectin")

    __table_args__ = (
        Index("ix_builds_project_status", "project_id", "status"),
        Index("ix_builds_created_desc", "created_at"),
    )

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def __repr__(self) -> str:
        return f"<Build(id={self.id}, project_id={self.project_id}, target={self.target.value}, status={self.status.value})>"