"""
Application configuration using Pydantic Settings.
All environment variables are defined here.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Gambling Comment Detector"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/gambling_detector"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT Settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Encryption Key for OAuth tokens
    encryption_key: str = "your-encryption-key-change-in-production"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    # YouTube API
    youtube_api_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Rate Limiting
    scan_rate_limit_per_minute: int = 10
    prediction_rate_limit_per_minute: int = 30

    # ML Model
    ml_model_path: str = "ml/model_pipeline.joblib"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
