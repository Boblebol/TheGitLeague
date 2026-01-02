"""Project and Repository Pydantic schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.project import RemoteType, RepoStatus, SyncMethod


# ===== Project Schemas =====


class ProjectBase(BaseModel):
    """Base Project schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    slug: str = Field(..., min_length=1, max_length=100, description="Project slug (URL-friendly)")
    description: Optional[str] = Field(None, description="Project description")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format (lowercase, alphanumeric, hyphens)."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Slug must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    repos_count: Optional[int] = Field(None, description="Number of repositories (optional)")

    class Config:
        from_attributes = True


class ProjectWithRepos(ProjectResponse):
    """Schema for project with repositories."""

    repos: List["RepositoryResponse"] = []


# ===== Repository Schemas =====


class RepositoryBase(BaseModel):
    """Base Repository schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Repository name")
    remote_url: Optional[str] = Field(None, description="Remote Git URL")
    remote_type: Optional[RemoteType] = Field(None, description="Remote type (local, ssh, https)")
    branch: str = Field("main", min_length=1, max_length=255, description="Git branch to track")
    sync_frequency: Optional[str] = Field(None, description="Sync frequency (cron syntax)")
    sync_method: SyncMethod = Field(SyncMethod.PULL_CELERY, description="Sync method (pull_celery or push_client)")


class RepositoryCreate(RepositoryBase):
    """Schema for creating a repository."""

    credentials: Optional[dict] = Field(None, description="Credentials (will be encrypted)")


class RepositoryUpdate(BaseModel):
    """Schema for updating a repository."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    remote_url: Optional[str] = None
    remote_type: Optional[RemoteType] = None
    branch: Optional[str] = Field(None, min_length=1, max_length=255)
    sync_frequency: Optional[str] = None
    sync_method: Optional[SyncMethod] = None
    credentials: Optional[dict] = None


class RepositoryResponse(RepositoryBase):
    """Schema for repository response."""

    id: str
    project_id: str
    status: RepoStatus
    last_sync_at: Optional[datetime] = None
    last_ingested_sha: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    sync_method: SyncMethod

    class Config:
        from_attributes = True


class RepositorySyncRequest(BaseModel):
    """Schema for triggering a repository sync."""

    force: bool = Field(False, description="Force re-sync from beginning")


class RepositorySyncResponse(BaseModel):
    """Schema for sync response."""

    message: str
    status: RepoStatus
    task_id: Optional[str] = None


class RepositoryTestConnectionRequest(BaseModel):
    """Schema for testing repository connection."""

    remote_url: str
    remote_type: Optional[RemoteType] = None
    branch: str = "main"
    credentials: Optional[dict] = None


class RepositoryTestConnectionResponse(BaseModel):
    """Schema for connection test response."""

    success: bool
    message: str
    available_branches: Optional[List[str]] = None
