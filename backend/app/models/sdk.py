"""SDK model for Darwin SDK management."""
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Enum, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SDKStatus(PyEnum):
    """Status of a Darwin SDK."""

    NOT_INSTALLED = "not_installed"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
    REMOVING = "removing"


class SDK(Base, TimestampMixin):
    """Darwin SDK (iOS/macOS) for cross-compilation."""

    __tablename__ = "sdks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)  # e.g., "18.5"
    build: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # e.g., "22F770"
    xcode_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # e.g., "16.0"
    platform: Mapped[str] = mapped_column(String(32), default="ios", nullable=False)  # ios, macos, watchos, tvos
    status: Mapped[SDKStatus] = mapped_column(
        Enum(SDKStatus, native_enum=False),
        default=SDKStatus.NOT_INSTALLED,
        nullable=False,
        index=True,
    )
    install_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artifact_bundle_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    download_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    installed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    __table_args__ = (
        Index("ix_sdks_platform_status", "platform", "status"),
        UniqueConstraint("version", "platform", name="uq_sdk_version_platform"),
    )

    @property
    def display_name(self) -> str:
        parts = [self.platform.upper(), self.version]
        if self.build:
            parts.append(f"({self.build})")
        return " ".join(parts)

    def __repr__(self) -> str:
        return f"<SDK(version={self.version}, platform={self.platform}, status={self.status.value})>"