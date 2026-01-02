"""Commit Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommitBase(BaseModel):
    """Base Commit schema."""

    sha: str = Field(..., min_length=40, max_length=40, description="Git commit SHA (full)")
    author_name: str = Field(..., description="Author name")
    author_email: str = Field(..., description="Author email (normalized to lowercase)")
    committer_name: str = Field(..., description="Committer name")
    committer_email: str = Field(..., description="Committer email (normalized to lowercase)")
    commit_date: datetime = Field(..., description="Commit date/time")
    message_title: str = Field(..., max_length=500, description="First line of commit message")
    message_body: Optional[str] = Field(None, description="Full commit message")
    additions: int = Field(0, ge=0, description="Lines added")
    deletions: int = Field(0, ge=0, description="Lines deleted")
    files_changed: int = Field(0, ge=0, description="Number of files changed")
    is_merge: bool = Field(False, description="Is this a merge commit?")
    parent_count: int = Field(1, ge=0, description="Number of parent commits")


class CommitResponse(CommitBase):
    """Schema for commit response."""

    id: str
    repo_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class CommitListResponse(BaseModel):
    """Schema for paginated commit list."""

    items: list[CommitResponse]
    total: int
    page: int
    pages: int
    per_page: int


class CommitStatsResponse(BaseModel):
    """Schema for commit statistics."""

    total_commits: int
    total_additions: int
    total_deletions: int
    total_files_changed: int
    merge_commits: int
    unique_authors: int
    date_range: dict[str, Optional[datetime]]
