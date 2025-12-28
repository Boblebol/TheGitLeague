"""
Application configuration using Pydantic settings.

Loads configuration from environment variables with validation.
Secrets like ENCRYPTION_MASTER_KEY must be set via .env file or environment.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Critical security settings:
    - ENCRYPTION_MASTER_KEY: Fernet key for credential encryption (REQUIRED)
    - SECRET_KEY: JWT signing key for authentication
    - DATABASE_URL: PostgreSQL connection string
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "The Git League"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development | production
    DEBUG: bool = False

    # Security - Encryption
    ENCRYPTION_MASTER_KEY: str  # REQUIRED: Fernet key for encrypting credentials
    ENCRYPTION_KEY_VERSION: str = "v1"  # For key rotation support

    # Security - API Authentication
    SECRET_KEY: str  # REQUIRED: JWT signing key
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Database
    DATABASE_URL: str  # REQUIRED: postgresql://user:password@host:port/dbname

    # Redis (for caching and job queue)
    REDIS_URL: str = "redis://localhost:6379/0"

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]  # Frontend URLs

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_CREDENTIALS_PER_MINUTE: int = 10  # Stricter for credential endpoints

    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG | INFO | WARNING | ERROR
    LOG_FORMAT: str = "json"  # json | text

    @field_validator("ENCRYPTION_MASTER_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate that encryption master key is set and looks valid."""
        if not v:
            raise ValueError(
                "ENCRYPTION_MASTER_KEY is required. "
                "Generate one with: python backend/scripts/generate_encryption_key.py"
            )

        # Basic validation: Fernet keys are 44 characters base64
        if len(v) < 40:
            raise ValueError(
                "ENCRYPTION_MASTER_KEY appears invalid (too short). "
                "It should be a base64-encoded Fernet key (44 characters)."
            )

        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate that JWT secret key is set and strong enough."""
        if not v:
            raise ValueError("SECRET_KEY is required for JWT authentication")

        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters for security. "
                "Generate a strong random key."
            )

        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v:
            raise ValueError("DATABASE_URL is required")

        if not v.startswith("postgresql://"):
            raise ValueError(
                "DATABASE_URL must be a PostgreSQL connection string "
                "(postgresql://user:password@host:port/dbname)"
            )

        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> list[str]:
        """Parse CORS_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings (singleton pattern).

    Returns:
        Settings instance loaded from environment

    Raises:
        ValidationError: If required env vars are missing or invalid
    """
    global _settings

    if _settings is None:
        try:
            _settings = Settings()
        except ValidationError as e:
            print(f"\n❌ Configuration Error:\n")
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                msg = error["msg"]
                print(f"  • {field}: {msg}")
            print(f"\n💡 Check your .env file or environment variables.\n")
            raise

    return _settings


# Convenience for importing
settings = get_settings()
