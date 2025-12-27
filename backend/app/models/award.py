"""Award and Play of the Day models."""

import enum
import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AwardType(str, enum.Enum):
    """Award type enumeration."""

    PLAYER_OF_WEEK = "player_of_week"
    PLAYER_OF_MONTH = "player_of_month"
    MVP = "mvp"  # Season MVP
    MOST_IMPROVED = "most_improved"


class Award(Base):
    """Award model for recognizing top performers."""

    __tablename__ = "awards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    season_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'week', 'month', 'season'
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    award_type: Mapped[str] = mapped_column(
        Enum(AwardType, native_enum=False, length=50), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Score breakdown
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="awards")
    user: Mapped["User"] = relationship("User", back_populates="awards")

    def __repr__(self) -> str:
        return f"<Award {self.award_type} - {self.user_id} ({self.period_start})>"

    __table_args__ = (
        # Unique constraint: one award per (season, period, award_type)
        Index("idx_award_unique", "season_id", "period_type", "period_start", "award_type", unique=True),
        # Performance indexes
        Index("idx_awards_season", "season_id"),
        Index("idx_awards_user", "user_id"),
        Index("idx_awards_type", "award_type"),
        # Validation
        CheckConstraint("period_type IN ('week', 'month', 'season')", name="check_period_type"),
    )


class PlayOfTheDay(Base):
    """Play of the Day model for highlighting exceptional commits."""

    __tablename__ = "plays_of_day"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    season_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Commit details
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="plays_of_day")
    user: Mapped["User"] = relationship("User", back_populates="plays_of_day")

    def __repr__(self) -> str:
        return f"<PlayOfTheDay {self.date} - {self.commit_sha[:8]}>"

    __table_args__ = (
        # Unique constraint: one play per (season, date)
        Index("idx_play_unique", "season_id", "date", unique=True),
        # Performance indexes
        Index("idx_plays_season", "season_id"),
        Index("idx_plays_user", "user_id"),
        Index("idx_plays_date", "date"),
    )
