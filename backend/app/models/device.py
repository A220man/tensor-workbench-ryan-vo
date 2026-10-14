"""Device model for iOS device management."""
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Enum, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DeviceType(PyEnum):
    """Type of iOS device."""

    PHYSICAL = "physical"
    SIMULATOR = "simulator"


class DeviceConnectionStatus(PyEnum):
    """Connection status of a device."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"
    UNAUTHORIZED = "unauthorized"


class Device(Base, TimestampMixin):
    """iOS device (physical or simulator)."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    udid: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[DeviceType] = mapped_column(Enum(DeviceType, native_enum=False), nullable=False, index=True)
    ios_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    model_identifier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    connection_status: Mapped[DeviceConnectionStatus] = mapped_column(
        Enum(DeviceConnectionStatus, native_enum=False),
        default=DeviceConnectionStatus.DISCONNECTED,
        nullable=False,
        index=True,
    )
    is_trusted: Mapped[bool] = mapped_column(default=False, nullable=False)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    properties: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON for extra properties

    __table_args__ = (
        Index("ix_devices_type_status", "device_type", "connection_status"),
        Index("ix_devices_last_seen", "last_seen_at"),
    )

    def __repr__(self) -> str:
        return f"<Device(udid={self.udid}, name={self.name}, type={self.device_type.value}, status={self.connection_status.value})>"