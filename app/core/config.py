from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "production-reliability-platform"
    app_version: str = "0.1.0"
    app_env: str = "local"
    database_url: str = "sqlite+pysqlite:///./reliability.db"
    enable_fault_injection: bool = False
    fault_admin_token: SecretStr = Field(default=SecretStr("local-development-token"))
    recovery_success_threshold: int = Field(default=2, ge=1, le=10)
    incident_provider: str = "mock"
    servicenow_instance_url: str | None = None
    servicenow_username: str | None = None
    servicenow_password: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
