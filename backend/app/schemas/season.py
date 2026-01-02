"""Season and Absence Pydantic schemas."""

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.season import SeasonStatus


class SeasonBase(BaseModel):
    """Base Season schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Season name")
    start_at: datetime = Field(..., description="Season start datetime")
    end_at: datetime = Field(..., description="Season end datetime")

    @field_validator("end_at")
    @classmethod
    def validate_end_after_start(cls, v: datetime, info) -> datetime:
        """Validate that end_at is after start_at."""
        if "start_at" in info.data and v <= info.data["start_at"]:
            raise ValueError("end_at must be after start_at")
        return v


class SeasonCreate(SeasonBase):
    """Schema for creating a season."""

    pass


class SeasonUpdate(BaseModel):
    """Schema for updating a season."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class SeasonResponse(SeasonBase):
    """Schema for season response."""

    id: str
    project_id: str
    status: SeasonStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SeasonActivateRequest(BaseModel):
    """Schema for activating a season."""

    pass  # No body needed, just POST to activate


# Absence Schemas


class AbsenceBase(BaseModel):
    """Base Absence schema."""

    start_at: date = Field(..., description="Absence start date")
    end_at: date = Field(..., description="Absence end date")
    reason: Optional[str] = Field(None, max_length=255, description="Reason for absence")

    @field_validator("end_at")
    @classmethod
    def validate_end_after_start(cls, v: date, info) -> date:
        """Validate that end_at is after or equal to start_at."""
        if "start_at" in info.data and v < info.data["start_at"]:
            raise ValueError("end_at must be on or after start_at")
        return v


class AbsenceCreate(AbsenceBase):
    """Schema for creating an absence."""

    user_id: str = Field(..., description="User ID")
    season_id: str = Field(..., description="Season ID")


class AbsenceUpdate(BaseModel):
    """Schema for updating an absence."""

    start_at: Optional[date] = None
    end_at: Optional[date] = None
    reason: Optional[str] = Field(None, max_length=255)


class AbsenceResponse(AbsenceBase):
    """Schema for absence response."""

    id: str
    user_id: str
    season_id: str
    created_at: datetime

    class Config:
        from_attributes = True
