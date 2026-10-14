"""Application configuration using pydantic-settings."""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "tensor-workbench-ryan-vo"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_workers: int = 1
    database_url: str = "sqlite+aiosqlite:///./data/tensor-workbench.db"
    secret_key: str = "change-me-in-production-use-strong-random"
    api_prefix: str = "/api"

    # Frontend
    frontend_port: int = 5173
    vite_api_url: str = "http://localhost:8000/api"

    # Keycloak OIDC
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "tensor-workbench"
    keycloak_client_id: str = "tensor-workbench"
    keycloak_client_secret: str = "change-me"
    keycloak_admin_user: str = "admin"
    keycloak_admin_password: str = "change-me"

    # OIDC endpoints (auto-discovered if not set)
    oidc_issuer: str = "http://localhost:8080/realms/tensor-workbench"
    oidc_authorization_endpoint: str = "http://localhost:8080/realms/tensor-workbench/protocol/openid-connect/auth"
    oidc_token_endpoint: str = "http://localhost:8080/realms/tensor-workbench/protocol/openid-connect/token"
    oidc_jwks_uri: str = "http://localhost:8080/realms/tensor-workbench/protocol/openid-connect/certs"
    oidc_userinfo_endpoint: str = "http://localhost:8080/realms/tensor-workbench/protocol/openid-connect/userinfo"
    oidc_logout_endpoint: str = "http://localhost:8080/realms/tensor-workbench/protocol/openid-connect/logout"

    # Apple Developer
    apple_team_id: Optional[str] = None
    apple_key_id: Optional[str] = None
    apple_private_key_path: Optional[str] = None
    app_store_connect_issuer_id: Optional[str] = None

    # LLM
    llm_api_key: Optional[str] = None
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"

    # SwiftPM / Build
    swift_path: str = "swift"
    swiftpm_config_dir: str = ".swiftpm"
    workspace_root: str = "/workspace"
    sdk_install_dir: str = "/opt/swift-sdks"

    # Device / USB
    usbmuxd_socket: str = "/var/run/usbmuxd"
    libimobiledevice_path: Optional[str] = None

    # Demo mode
    demo_mode: bool = True
    demo_user_email: str = "demo@tensor-workbench.local"
    demo_user_role: str = "admin"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @field_validator("database_url")
    @classmethod
    def ensure_data_dir(cls, v: str) -> str:
        """Ensure SQLite database directory exists."""
        if v.startswith("sqlite"):
            # Extract path from sqlite:///./data/file.db or sqlite+aiosqlite:///./data/file.db
            prefix = "sqlite+aiosqlite:///" if "aiosqlite" in v else "sqlite:///"
            if v.startswith(prefix):
                db_path = v[len(prefix) :]
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("workspace_root")
    @classmethod
    def ensure_workspace(cls, v: str) -> str:
        """Ensure workspace directory exists."""
        try:
            Path(v).mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError):
            # In test environments or read-only filesystems, directory may not be creatable
            # The actual workspace will be created at runtime if needed
            pass
        return v

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def demo_allowed(self) -> bool:
        return self.demo_mode and not self.is_production


@lru_cache
def get_settings() -> Settings:
    return Settings()