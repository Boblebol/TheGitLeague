"""Leaderboard schemas."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class PlayerPeriodStatsBase(BaseModel):
    """Base schema for player period stats."""

    commits: int = Field(ge=0, description="Number of commits")
    additions: int = Field(ge=0, description="Total lines added")
    deletions: int = Field(ge=0, description="Total lines deleted")
    files_changed: int = Field(ge=0, description="Total files changed")
    pts: int = Field(description="Points metric")
    reb: int = Field(description="Rebounds metric")
    ast: int = Field(description="Assists metric")
    blk: int = Field(description="Blocks metric")
    tov: int = Field(description="Turnovers metric")
    impact_score: float = Field(description="Overall impact score")


class PlayerPeriodStatsResponse(PlayerPeriodStatsBase):
    """Response schema for player period stats."""

    id: str
    user_id: str
    season_id: str
    period_type: Literal["day", "week", "month", "season"]
    period_start: date

    model_config = ConfigDict(from_attributes=True)


class PlayerInfo(BaseModel):
    """Player information for leaderboard."""

    id: str
    display_name: Optional[str]
    email: str
    role: str
    status: str


class LeaderboardEntry(BaseModel):
    """Single entry in the leaderboard."""

    rank: int = Field(ge=1, description="Player's rank")
    player: PlayerInfo = Field(description="Player information")
    stats: PlayerPeriodStatsResponse = Field(description="Player's period stats")
    trend: Optional[Literal["up", "down", "neutral"]] = Field(
        default=None, description="Trend compared to previous period"
    )


class LeaderboardResponse(BaseModel):
    """Paginated leaderboard response."""

    items: list[LeaderboardEntry] = Field(description="Leaderboard entries")
    total: int = Field(ge=0, description="Total number of players")
    page: int = Field(ge=1, description="Current page number")
    pages: int = Field(ge=0, description="Total number of pages")
    period_type: Literal["day", "week", "month", "season"]
    period_start: Optional[date] = Field(
        default=None, description="Start date of the period"
    )


class AllTimeRankingEntry(BaseModel):
    """Single entry in all-time rankings."""

    rank: int = Field(ge=1, description="Player's all-time rank")
    user_id: str
    display_name: Optional[str]
    email: str
    status: str = Field(description="User status (active/retired)")

    # Total stats
    total_pts: int = Field(ge=0)
    total_commits: int = Field(ge=0)
    total_impact_score: float
    total_additions: int = Field(ge=0)
    total_deletions: int = Field(ge=0)
    total_reb: int = Field(ge=0)
    total_ast: int = Field(ge=0)
    total_blk: int = Field(ge=0)
    total_tov: int = Field(ge=0)

    # Metadata
    seasons_count: int = Field(ge=0, description="Number of seasons played")
    awards_count: int = Field(ge=0, description="Total awards won")

    # Averages
    avg_pts_per_season: float = Field(ge=0.0, description="Average PTS per season")
    avg_commits_per_season: float = Field(ge=0.0, description="Average commits per season")


class AllTimeLeaderboardResponse(BaseModel):
    """All-time leaderboard response."""

    items: list[AllTimeRankingEntry] = Field(description="All-time ranking entries")
    total: int = Field(ge=0, description="Total number of players")
    page: int = Field(ge=1, description="Current page number")
    pages: int = Field(ge=0, description="Total number of pages")
    sort_by: str = Field(description="Sort column used")
    order: Literal["asc", "desc"] = Field(description="Sort order")
