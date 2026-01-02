"""Scoring Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScoringCoefficientsSchema(BaseModel):
    """Schema for scoring coefficients."""

    additions_weight: float = Field(1.0, ge=0, description="Weight for additions")
    deletions_weight: float = Field(0.6, ge=0, description="Weight for deletions")
    commit_base: int = Field(10, ge=0, description="Base points per commit")
    multi_file_bonus: int = Field(5, ge=0, description="Bonus for multi-file commits")
    fix_bonus: int = Field(15, ge=0, description="Bonus for fix commits")
    wip_penalty: int = Field(-10, le=0, description="Penalty for WIP commits")
    max_additions_cap: int = Field(1000, ge=0, description="Maximum additions cap")
    max_deletions_cap: int = Field(1000, ge=0, description="Maximum deletions cap")


class ProjectConfigResponse(BaseModel):
    """Schema for project config response."""

    project_id: str
    scoring_coefficients: ScoringCoefficientsSchema
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectConfigUpdate(BaseModel):
    """Schema for updating project config."""

    scoring_coefficients: ScoringCoefficientsSchema


class CommitMetricsResponse(BaseModel):
    """Schema for commit metrics response."""

    commit_id: str
    commit_sha: str
    pts: int = Field(..., description="Points")
    reb: int = Field(..., description="Rebounds")
    ast: int = Field(..., description="Assists")
    blk: int = Field(..., description="Blocks")
    tov: int = Field(..., description="Turnovers")
    impact_score: float = Field(..., description="Impact score")


class CommitMetricsBreakdown(BaseModel):
    """Schema for detailed commit metrics breakdown."""

    commit_id: str
    commit_sha: str
    author_email: str
    commit_date: datetime
    message_title: str

    # Raw stats
    additions: int
    deletions: int
    files_changed: int
    is_merge: bool

    # NBA metrics
    pts: int
    reb: int
    ast: int
    blk: int
    tov: int
    impact_score: float

    # Breakdown explanation
    breakdown: dict[str, str] = Field(
        ...,
        description="Explanation of how each metric was calculated"
    )
