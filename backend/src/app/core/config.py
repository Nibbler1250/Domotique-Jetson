"""Application configuration with Pydantic Settings."""

from functools import lru_cache
from typing import Literal

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
    app_name: str = "Family Hub"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # API
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite+aiosqlite:///./family_hub.db"

    # JWT Authentication
    jwt_secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # MQTT
    mqtt_host: str = "192.168.1.118"
    mqtt_port: int = 1883
    mqtt_topic_prefix: str = "hubitat/genius-hub-000d"

    # Hubitat Maker API
    hubitat_host: str = "192.168.1.66"
    hubitat_app_id: int = 274
    hubitat_token: str = "17a29aed-e45d-4d30-8640-c68adb895a84"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://192.168.1.95:5173",
        "http://192.168.1.95:5174",
        "http://192.168.1.95:5175",
    ]

    @property
    def hubitat_base_url(self) -> str:
        """Construct Hubitat Maker API base URL."""
        return f"http://{self.hubitat_host}/apps/api/{self.hubitat_app_id}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
