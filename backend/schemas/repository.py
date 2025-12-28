"""
Pydantic schemas for repository API endpoints.

Request and response models with validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from backend.models import AccessType, RepoStatus


class RepositoryCreate(BaseModel):
    """Schema for creating a new repository."""

    project_id: int = Field(..., description="ID of parent project")
    name: str = Field(..., min_length=1, max_length=255, description="Repository name")
    remote_url: str = Field(
        ...,
        description="Git remote URL (without credentials)",
        examples=["https://github.com/owner/repo.git"]
    )
    access_type: AccessType = Field(
        default=AccessType.HTTPS_PAT,
        description="Access method: local_bare, ssh, or https_pat"
    )
    branch: str = Field(
        default="main",
        min_length=1,
        max_length=255,
        description="Branch to track"
    )

    # Credentials (only if access_type=https_pat)
    pat_token: Optional[str] = Field(
        None,
        description="Personal Access Token (required for https_pat)",
        examples=["ghp_xxxxxxxxxxxxxx"]
    )
    pat_username: str = Field(
        default="git",
        description="Username for HTTPS authentication"
    )

    @field_validator("pat_token")
    @classmethod
    def validate_pat_token(cls, v: Optional[str], info) -> Optional[str]:
        """Validate PAT token format and requirements."""
        access_type = info.data.get("access_type")

        # PAT required for HTTPS access
        if access_type == AccessType.HTTPS_PAT and not v:
            raise ValueError("pat_token is required when access_type=https_pat")

        # Basic PAT format validation (GitHub/GitLab patterns)
        if v and len(v) < 20:
            raise ValueError("PAT token appears too short (min 20 characters)")

        return v

    @field_validator("remote_url")
    @classmethod
    def validate_remote_url(cls, v: str) -> str:
        """Validate Git remote URL format."""
        if not v.startswith(("https://", "http://", "git@", "ssh://")):
            raise ValueError(
                "remote_url must start with https://, http://, git@, or ssh://"
            )

        # Ensure no credentials embedded in URL
        if "@" in v and not v.startswith("git@"):
            # git@github.com is OK, but https://user:pass@github.com is NOT
            if "://" in v:
                raise ValueError(
                    "Do not include credentials in remote_url. "
                    "Use pat_token field instead."
                )

        return v


class RepositoryUpdate(BaseModel):
    """Schema for updating repository configuration."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    remote_url: Optional[str] = None
    branch: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[RepoStatus] = None

    # Credential update (separate endpoint recommended for security)
    pat_token: Optional[str] = Field(
        None,
        description="New PAT token (if rotating credentials)"
    )
    pat_username: Optional[str] = None


class RepositoryCredentialsUpdate(BaseModel):
    """Schema for updating repository credentials only."""

    pat_token: str = Field(
        ...,
        min_length=20,
        description="New Personal Access Token"
    )
    pat_username: str = Field(
        default="git",
        description="Username for HTTPS authentication"
    )


class RepositoryResponse(BaseModel):
    """
    Schema for repository API responses.

    CRITICAL: Never exposes encrypted_credentials.
    Only shows metadata and has_credentials boolean.
    """

    id: int
    project_id: int
    name: str
    remote_url: str
    access_type: str
    has_credentials: bool  # Boolean only, NOT actual credentials
    encryption_key_id: str
    branch: str
    last_sync_at: Optional[datetime] = None
    last_ingested_sha: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


class RepositoryListResponse(BaseModel):
    """Schema for paginated repository list."""

    total: int
    repositories: list[RepositoryResponse]


class RepositorySyncRequest(BaseModel):
    """Schema for triggering a repository sync."""

    force: bool = Field(
        default=False,
        description="Force full sync (ignore last_ingested_sha)"
    )
