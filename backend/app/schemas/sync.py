"""Schemas for push-based Git synchronization."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class CommitMetadata(BaseModel):
    """Single commit metadata for sync."""

    sha: str = Field(..., min_length=40, max_length=40, description="Git commit SHA (40 hex chars)")
    author_name: str = Field(..., min_length=1, max_length=255, description="Author name")
    author_email: str = Field(..., min_length=1, max_length=255, description="Author email")
    committer_name: str = Field(..., min_length=1, max_length=255, description="Committer name")
    committer_email: str = Field(..., min_length=1, max_length=255, description="Committer email")
    commit_date: datetime = Field(..., description="Commit timestamp")
    message_title: str = Field(..., min_length=1, max_length=500, description="Commit message subject")
    message_body: Optional[str] = Field(None, description="Commit message body")
    additions: int = Field(..., ge=0, description="Lines added")
    deletions: int = Field(..., ge=0, description="Lines deleted")
    files_changed: int = Field(..., ge=0, description="Files changed")
    is_merge: bool = Field(False, description="Is merge commit")
    parent_count: int = Field(1, ge=0, description="Number of parents")

    @field_validator("sha")
    @classmethod
    def validate_sha(cls, v: str) -> str:
        """Validate SHA is 40 hex characters."""
        if not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("SHA must be 40 hexadecimal characters")
        return v.lower()

    @field_validator("author_email", "committer_email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower()


class SyncCommitsRequest(BaseModel):
    """Request to sync commits to a repository."""

    commits: List[CommitMetadata] = Field(
        ..., min_items=1, max_items=1000, description="Commits to sync (1-1000)"
    )
    client_version: Optional[str] = Field(None, description="Client version for tracking")
    timestamp: Optional[datetime] = Field(None, description="Client timestamp")

    @field_validator("commits")
    @classmethod
    def validate_commits(cls, v: List[CommitMetadata]) -> List[CommitMetadata]:
        """Validate commits list."""
        if not v:
            raise ValueError("At least one commit is required")
        # Check for duplicate SHAs in the batch
        shas = [c.sha for c in v]
        if len(shas) != len(set(shas)):
            raise ValueError("Duplicate SHAs found in batch")
        return v


class CommitInsertResult(BaseModel):
    """Result of inserting a single commit."""

    sha: str
    inserted: bool
    error: Optional[str] = None


class SyncCommitsResponse(BaseModel):
    """Response from sync endpoint."""

    total: int = Field(..., description="Total commits in request")
    inserted: int = Field(..., description="Commits inserted")
    skipped: int = Field(..., description="Commits skipped (already exist)")
    errors: int = Field(..., description="Commits with errors")
    last_ingested_sha: Optional[str] = Field(None, description="Latest ingested commit SHA")
    details: List[CommitInsertResult] = Field(default_factory=list, description="Per-commit results")

    class Config:
        from_attributes = True


class SyncStatusResponse(BaseModel):
    """Repository sync status."""

    repo_id: str = Field(..., description="Repository ID")
    status: str = Field(..., description="Current status (pending, syncing, healthy, error)")
    last_sync_at: Optional[datetime] = Field(None, description="Last successful sync")
    last_ingested_sha: Optional[str] = Field(None, description="Latest ingested SHA")
    total_commits: int = Field(0, description="Total commits in repository")
    error_message: Optional[str] = Field(None, description="Error message if status is error")

    class Config:
        from_attributes = True
