"""Fantasy league schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FantasyLeagueCreate(BaseModel):
    """Schema for creating a fantasy league."""

    name: str = Field(min_length=1, max_length=255)
    season_id: str
    roster_min: int = Field(ge=1, description="Minimum number of players in a roster")
    roster_max: int = Field(ge=1, description="Maximum number of players in a roster")
    lock_at: Optional[datetime] = Field(None, description="When rosters lock")

    @field_validator("roster_max")
    @classmethod
    def validate_roster_max(cls, v, info):
        """Validate that roster_max >= roster_min."""
        if "roster_min" in info.data and v < info.data["roster_min"]:
            raise ValueError("roster_max must be >= roster_min")
        return v


class FantasyLeagueResponse(BaseModel):
    """Schema for fantasy league response."""

    id: str
    name: str
    season_id: str
    season_name: Optional[str] = None
    roster_min: int
    roster_max: int
    lock_at: Optional[datetime]
    created_at: datetime
    participants_count: int = Field(default=0, description="Number of participants")
    is_locked: bool = Field(default=False, description="Whether the league is locked")

    model_config = ConfigDict(from_attributes=True)


class RosterPickResponse(BaseModel):
    """Schema for a single roster pick."""

    picked_user_id: str
    display_name: Optional[str]
    email: str
    position: int


class FantasyRosterResponse(BaseModel):
    """Schema for fantasy roster response."""

    id: str
    league_id: str
    user_id: str
    locked_at: Optional[datetime]
    created_at: datetime
    picks: List[RosterPickResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RosterUpdateRequest(BaseModel):
    """Schema for updating a roster."""

    picks: List[str] = Field(description="List of user IDs to pick")

    @field_validator("picks")
    @classmethod
    def validate_no_duplicates(cls, v):
        """Validate no duplicate picks."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate picks are not allowed")
        return v


class FantasyLeaderboardEntry(BaseModel):
    """Schema for a single fantasy leaderboard entry."""

    rank: int = Field(ge=1)
    user_id: str
    display_name: Optional[str]
    email: str
    roster_id: str
    total_score: float
    picks_count: int = Field(ge=0)
    locked_at: Optional[datetime]


class FantasyLeaderboardResponse(BaseModel):
    """Schema for fantasy leaderboard response."""

    league_id: str
    league_name: str
    entries: List[FantasyLeaderboardEntry]
