"""Hall of Fame schemas."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AllTimeLeader(BaseModel):
    """All-time leader entry."""

    user_id: str
    display_name: Optional[str]
    email: str
    total_pts: int = Field(ge=0)
    total_commits: int = Field(ge=0)
    total_impact_score: float
    awards_count: int = Field(ge=0, description="Total number of awards won")
    seasons_played: int = Field(ge=0)


class SeasonRecord(BaseModel):
    """Single season record holder."""

    user_id: str
    display_name: Optional[str]
    email: str
    season_id: str
    season_name: str
    value: int = Field(ge=0, description="Record value (commits, pts, etc.)")
    year: int


class AwardRecord(BaseModel):
    """Most awarded player record."""

    user_id: str
    display_name: Optional[str]
    email: str
    awards_count: int = Field(ge=0)
    player_of_week_count: int = Field(ge=0)
    player_of_month_count: int = Field(ge=0)
    mvp_count: int = Field(ge=0)


class StreakRecord(BaseModel):
    """Longest streak record."""

    user_id: str
    display_name: Optional[str]
    email: str
    streak_days: int = Field(ge=0, description="Consecutive days with commits")
    start_date: date
    end_date: date


class RetiredPlayer(BaseModel):
    """Retired player information."""

    user_id: str
    display_name: Optional[str]
    email: str
    role: str
    retired_at: date
    total_commits: int = Field(ge=0)
    total_pts: int = Field(ge=0)
    awards_count: int = Field(ge=0)
    seasons_played: int = Field(ge=0)


class HallOfFameResponse(BaseModel):
    """Hall of Fame response with all-time leaders and records."""

    all_time_leaders: list[AllTimeLeader] = Field(
        description="Top 10 all-time players by total PTS"
    )
    records: dict = Field(
        description="Various records (most commits, highest PTS, etc.)"
    )
    retired_players: list[RetiredPlayer] = Field(
        description="List of retired players (legends)"
    )
