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
        extra="ignore",
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

    # Frontend URL for OAuth redirect
    frontend_url: str = "http://localhost:3000"

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

    # Retraining Configuration (Requirements 6.1, 6.2)
    retraining_threshold: int = 100  # Minimum validations before retraining
    retraining_test_size: float = 0.2  # Hold out for evaluation
    min_training_samples: int = 100  # Minimum samples required for training
    
    # ML Hyperparameters (Requirements 6.2)
    # Logistic Regression classifier parameters
    classifier_c: float = 10.0
    classifier_solver: str = "lbfgs"
    
    # TF-IDF vectorizer parameters (stored as comma-separated for env vars)
    word_tfidf_ngram_min: int = 1
    word_tfidf_ngram_max: int = 2
    char_tfidf_ngram_min: int = 2
    char_tfidf_ngram_max: int = 4
    
    # Model storage paths
    model_dir: str = "ml/models"
    original_dataset_path: str = "ml/df_all.csv"
    
    # Admin Configuration
    admin_emails: str = ""  # Comma-separated list of admin emails
    
    @property
    def admin_email_list(self) -> list[str]:
        """Get list of admin emails."""
        if not self.admin_emails:
            return []
        return [email.strip() for email in self.admin_emails.split(",") if email.strip()]
    
    @property
    def word_tfidf_ngram_range(self) -> tuple[int, int]:
        """Get word TF-IDF ngram range as tuple."""
        return (self.word_tfidf_ngram_min, self.word_tfidf_ngram_max)
    
    @property
    def char_tfidf_ngram_range(self) -> tuple[int, int]:
        """Get char TF-IDF ngram range as tuple."""
        return (self.char_tfidf_ngram_min, self.char_tfidf_ngram_max)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
