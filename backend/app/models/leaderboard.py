"""Leaderboard models for player period statistics."""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PlayerPeriodStats(Base):
    """
    Aggregated player statistics for a specific period.

    Pre-computed stats for performance optimization.
    Populated by background workers after each sync.
    """
    __tablename__ = "player_period_stats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    season_id: Mapped[str] = mapped_column(String(36), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'day', 'week', 'month', 'season'
    period_start: Mapped[date] = mapped_column(Date, nullable=False)

    # Raw commit stats
    commits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    additions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deletions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_changed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # NBA metrics
    pts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reb: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ast: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    blk: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tov: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="period_stats")
    season: Mapped["Season"] = relationship("Season", back_populates="period_stats")

    __table_args__ = (
        # Unique constraint: one stats record per player per period
        Index("idx_player_period_unique", "user_id", "season_id", "period_type", "period_start", unique=True),

        # Performance indexes for leaderboard queries
        Index("idx_period_stats_season_period", "season_id", "period_type", "period_start"),
        Index("idx_period_stats_impact_score", "impact_score"),
        Index("idx_period_stats_pts", "pts"),
        Index("idx_period_stats_reb", "reb"),
        Index("idx_period_stats_ast", "ast"),
        Index("idx_period_stats_blk", "blk"),
        Index("idx_period_stats_commits", "commits"),

        # Validation
        CheckConstraint("period_type IN ('day', 'week', 'month', 'season')", name="check_period_type"),
    )

    def __repr__(self) -> str:
        return f"<PlayerPeriodStats user_id={self.user_id} period={self.period_type} start={self.period_start} impact={self.impact_score}>"
