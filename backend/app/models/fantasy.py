"""Fantasy league models."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FantasyLeague(Base):
    """Fantasy league model."""

    __tablename__ = "fantasy_leagues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    season_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    roster_min: Mapped[int] = mapped_column(Integer, nullable=False)
    roster_max: Mapped[int] = mapped_column(Integer, nullable=False)
    lock_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="fantasy_leagues")
    participants: Mapped[List["FantasyParticipant"]] = relationship(
        "FantasyParticipant", back_populates="league", cascade="all, delete-orphan"
    )
    rosters: Mapped[List["FantasyRoster"]] = relationship(
        "FantasyRoster", back_populates="league", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FantasyLeague {self.name}>"

    __table_args__ = (
        Index("idx_fantasy_leagues_season", "season_id"),
    )


class FantasyParticipant(Base):
    """Fantasy league participant (join table)."""

    __tablename__ = "fantasy_participants"

    league_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fantasy_leagues.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    league: Mapped["FantasyLeague"] = relationship("FantasyLeague", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="fantasy_participations")

    def __repr__(self) -> str:
        return f"<FantasyParticipant league={self.league_id} user={self.user_id}>"


class FantasyRoster(Base):
    """Fantasy roster for a participant in a league."""

    __tablename__ = "fantasy_rosters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    league_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fantasy_leagues.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    league: Mapped["FantasyLeague"] = relationship("FantasyLeague", back_populates="rosters")
    user: Mapped["User"] = relationship("User", back_populates="fantasy_rosters")
    picks: Mapped[List["FantasyRosterPick"]] = relationship(
        "FantasyRosterPick", back_populates="roster", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FantasyRoster league={self.league_id} user={self.user_id}>"

    __table_args__ = (
        Index("idx_fantasy_roster_unique", "league_id", "user_id", unique=True),
        Index("idx_fantasy_rosters_league", "league_id"),
        Index("idx_fantasy_rosters_user", "user_id"),
    )


class FantasyRosterPick(Base):
    """Individual player pick in a fantasy roster."""

    __tablename__ = "fantasy_roster_picks"

    roster_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fantasy_rosters.id", ondelete="CASCADE"), primary_key=True
    )
    picked_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    roster: Mapped["FantasyRoster"] = relationship("FantasyRoster", back_populates="picks")
    picked_user: Mapped["User"] = relationship("User", foreign_keys=[picked_user_id])

    def __repr__(self) -> str:
        return f"<FantasyRosterPick roster={self.roster_id} user={self.picked_user_id} pos={self.position}>"
