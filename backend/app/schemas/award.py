"""Award and Play of the Day schemas."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AwardResponse(BaseModel):
    """Award response schema."""

    id: str
    season_id: str
    period_type: str
    period_start: date
    award_type: str
    user_id: str
    user_display_name: Optional[str] = None
    user_email: str
    score: float
    metadata_json: Optional[dict] = Field(None, description="Score breakdown")
    created_at: date

    model_config = ConfigDict(from_attributes=True)


class PlayOfTheDayResponse(BaseModel):
    """Play of the Day response schema."""

    id: str
    season_id: str
    date: date
    commit_sha: str
    user_id: str
    user_display_name: Optional[str] = None
    user_email: str
    score: float
    metadata_json: Optional[dict] = Field(None, description="Commit details")
    created_at: date

    model_config = ConfigDict(from_attributes=True)
