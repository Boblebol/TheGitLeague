"""Season and Absence models."""

import enum
import uuid
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SeasonStatus(str, enum.Enum):
    """Season status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class Season(Base):
    """Season model - competition timeframes."""

    __tablename__ = "seasons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(SeasonStatus, native_enum=False, length=20), nullable=False, default=SeasonStatus.DRAFT, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="seasons")
    absences: Mapped[List["Absence"]] = relationship(
        "Absence", back_populates="season", cascade="all, delete-orphan"
    )
    period_stats: Mapped[List["PlayerPeriodStats"]] = relationship(
        "PlayerPeriodStats", back_populates="season", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Season {self.name} ({self.status})>"

    __table_args__ = (
        CheckConstraint("end_at > start_at", name="check_season_dates"),
        Index("idx_seasons_project_name", "project_id", "name", unique=True),
    )


class Absence(Base):
    """Absence model - player absences during seasons."""

    __tablename__ = "absences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    season_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_at: Mapped[date] = mapped_column(Date, nullable=False)
    end_at: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="absences")
    season: Mapped["Season"] = relationship("Season", back_populates="absences")

    def __repr__(self) -> str:
        return f"<Absence {self.user_id} ({self.start_at} - {self.end_at})>"

    __table_args__ = (
        CheckConstraint("end_at >= start_at", name="check_absence_dates"),
        Index("idx_absences_user_season", "user_id", "season_id"),
    )
