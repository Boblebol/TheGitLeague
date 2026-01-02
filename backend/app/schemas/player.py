"""Player profile schemas."""

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class PlayerSeasonStats(BaseModel):
    """Player statistics for a specific season."""

    season_id: str
    season_name: str
    commits: int = Field(ge=0)
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    files_changed: int = Field(ge=0)
    pts: int
    reb: int
    ast: int
    blk: int
    tov: int
    impact_score: float


class PlayerCareerStats(BaseModel):
    """Player all-time career statistics."""

    total_commits: int = Field(ge=0)
    total_additions: int = Field(ge=0)
    total_deletions: int = Field(ge=0)
    total_files_changed: int = Field(ge=0)
    total_pts: int
    total_reb: int
    total_ast: int
    total_blk: int
    total_tov: int
    total_impact_score: float
    seasons_played: int = Field(ge=0, description="Number of seasons participated in")
    first_commit_date: Optional[date] = Field(None, description="Date of first commit")
    last_commit_date: Optional[date] = Field(None, description="Date of most recent commit")


class RepoContribution(BaseModel):
    """Player's contribution to a specific repository."""

    repo_id: str
    repo_name: str
    commits: int = Field(ge=0)
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    impact_score: float


class PlayerCommitSummary(BaseModel):
    """Summary of a player's recent commit."""

    sha: str
    repo_id: str
    repo_name: str
    message_title: str
    commit_date: date
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)
    files_changed: int = Field(ge=0)

    model_config = ConfigDict(from_attributes=True)


class PlayerProfileResponse(BaseModel):
    """Complete player profile response."""

    id: str
    display_name: Optional[str]
    email: str
    role: str
    status: str
    current_season_stats: Optional[PlayerSeasonStats] = Field(
        None, description="Stats for current/specified season"
    )
    career_stats: PlayerCareerStats
    repo_contributions: List[RepoContribution] = Field(
        default_factory=list, description="Breakdown by repository"
    )
    recent_commits: List[PlayerCommitSummary] = Field(
        default_factory=list, description="Last 50 commits"
    )


class TrendDataPoint(BaseModel):
    """Single data point for trend visualization."""

    period_start: date
    period_type: Literal["day", "week", "month", "season"]
    commits: int = Field(ge=0)
    pts: int
    impact_score: float


class PlayerTrendResponse(BaseModel):
    """Trend data for player visualization."""

    player_id: str
    season_id: str
    period_type: Literal["day", "week", "month", "season"]
    data_points: List[TrendDataPoint] = Field(
        description="Trend data points (up to 12 periods)"
    )
