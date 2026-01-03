"""Configuration loading and validation."""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from gitleague_client.exceptions import ConfigError


class RepositoryConfig(BaseModel):
    """Configuration for a single repository."""

    path: str = Field(..., description="Local repository path")
    git_url: str = Field(..., description="Git remote URL")
    ssh_key: Optional[str] = Field(None, description="SSH key path for authentication")
    username: Optional[str] = Field(None, description="Username for HTTPS auth")
    password_env: Optional[str] = Field(None, description="Environment variable containing password")

    @field_validator("path", "ssh_key")
    @classmethod
    def expand_paths(cls, v: Optional[str]) -> Optional[str]:
        """Expand ~ and environment variables in paths."""
        if v is None:
            return None
        return os.path.expandvars(os.path.expanduser(v))

    def get_password(self) -> Optional[str]:
        """Get password from environment variable if configured."""
        if self.password_env:
            return os.getenv(self.password_env)
        return None


class ProjectConfig(BaseModel):
    """Configuration for a project."""

    name: str = Field(..., description="Project name")
    project_id: str = Field(..., description="Project ID from GitLeague web UI")
    repos: List[RepositoryConfig] = Field(..., description="Repositories to sync")


class ClientConfig(BaseModel):
    """Root client configuration."""

    api_url: str = Field(..., description="GitLeague API base URL")
    api_key: Optional[str] = Field(None, description="API key (or set GITLEAGUE_API_KEY env var)")
    batch_size: int = Field(100, description="Commits per batch (1-1000)")
    max_retries: int = Field(3, description="Max retries on transient errors")
    projects: List[ProjectConfig] = Field(..., description="Projects to sync")

    @field_validator("api_key", mode="before")
    @classmethod
    def get_api_key_from_env(cls, v: Optional[str]) -> str:
        """Get API key from env var if not provided."""
        if v:
            return v
        api_key = os.getenv("GITLEAGUE_API_KEY")
        if not api_key:
            raise ValueError(
                "API key not provided in config and GITLEAGUE_API_KEY env var not set"
            )
        return api_key

    @field_validator("batch_size")
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        """Validate batch size is between 1 and 1000."""
        if not 1 <= v <= 1000:
            raise ValueError("batch_size must be between 1 and 1000")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        """Validate max_retries is positive."""
        if v < 0:
            raise ValueError("max_retries must be non-negative")
        return v

    class Config:
        """Pydantic config."""

        extra = "forbid"  # Reject unknown fields


class ConfigLoader:
    """Load and validate client configuration from YAML file."""

    @staticmethod
    def load(config_path: str) -> ClientConfig:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML config file

        Returns:
            Validated ClientConfig object

        Raises:
            ConfigError: If file not found or validation fails
        """
        # Expand path
        config_path = os.path.expandvars(os.path.expanduser(config_path))
        config_file = Path(config_path)

        if not config_file.exists():
            raise ConfigError(f"Config file not found: {config_path}")

        try:
            with open(config_file, "r") as f:
                data = yaml.safe_load(f)

            if not data:
                raise ConfigError("Config file is empty")

            # Validate and construct config
            return ClientConfig(**data)

        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
        except ValueError as e:
            raise ConfigError(f"Invalid configuration: {e}")
