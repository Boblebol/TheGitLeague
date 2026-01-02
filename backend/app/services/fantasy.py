"""Fantasy league service."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.fantasy import (
    FantasyLeague,
    FantasyParticipant,
    FantasyRoster,
    FantasyRosterPick,
)
from app.models.leaderboard import PlayerPeriodStats
from app.models.season import Season
from app.models.user import User
from app.schemas.fantasy import (
    FantasyLeagueCreate,
    RosterPickResponse,
    FantasyLeaderboardEntry,
)

logger = logging.getLogger(__name__)


class FantasyService:
    """Service for fantasy league operations."""

    def create_league(
        self,
        league_data: FantasyLeagueCreate,
        db: Session,
        current_user: User,
    ) -> FantasyLeague:
        """
        Create a new fantasy league (Commissioner only).

        Args:
            league_data: League creation data
            db: Database session
            current_user: Current user (must be Commissioner)

        Returns:
            Created FantasyLeague

        Raises:
            HTTPException: If season not found
        """
        # Validate season exists
        season = db.query(Season).filter(Season.id == league_data.season_id).first()
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )

        league = FantasyLeague(
            name=league_data.name,
            season_id=league_data.season_id,
            roster_min=league_data.roster_min,
            roster_max=league_data.roster_max,
            lock_at=league_data.lock_at,
        )

        db.add(league)
        db.commit()
        db.refresh(league)

        logger.info(f"Created fantasy league {league.name} for season {season.name}")
        return league

    def get_league(self, league_id: str, db: Session) -> FantasyLeague:
        """
        Get fantasy league by ID.

        Args:
            league_id: League ID
            db: Database session

        Returns:
            FantasyLeague

        Raises:
            HTTPException: If league not found
        """
        league = db.query(FantasyLeague).filter(FantasyLeague.id == league_id).first()
        if not league:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fantasy league not found",
            )
        return league

    def list_leagues(
        self,
        db: Session,
        season_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FantasyLeague]:
        """
        List fantasy leagues with optional filters.

        Args:
            db: Database session
            season_id: Filter by season
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of FantasyLeague
        """
        query = db.query(FantasyLeague)

        if season_id:
            query = query.filter(FantasyLeague.season_id == season_id)

        return query.offset(skip).limit(limit).all()

    def join_league(
        self,
        league_id: str,
        db: Session,
        current_user: User,
    ) -> FantasyParticipant:
        """
        Join a fantasy league.

        Args:
            league_id: League ID
            db: Database session
            current_user: Current user

        Returns:
            FantasyParticipant

        Raises:
            HTTPException: If league not found or already joined
        """
        league = self.get_league(league_id, db)

        # Check if already a participant
        existing = (
            db.query(FantasyParticipant)
            .filter(
                and_(
                    FantasyParticipant.league_id == league_id,
                    FantasyParticipant.user_id == current_user.id,
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already a participant in this league",
            )

        participant = FantasyParticipant(
            league_id=league_id,
            user_id=current_user.id,
        )

        db.add(participant)
        db.commit()
        db.refresh(participant)

        logger.info(f"User {current_user.email} joined fantasy league {league.name}")
        return participant

    def update_roster(
        self,
        league_id: str,
        picks: List[str],
        db: Session,
        current_user: User,
    ) -> FantasyRoster:
        """
        Update fantasy roster.

        Args:
            league_id: League ID
            picks: List of user IDs to pick
            db: Database session
            current_user: Current user

        Returns:
            Updated FantasyRoster

        Raises:
            HTTPException: If league locked, invalid picks, or validation fails
        """
        league = self.get_league(league_id, db)

        # Check if league is locked
        if league.lock_at and datetime.utcnow() > league.lock_at:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="League is locked, roster changes not allowed",
            )

        # Validate roster size
        if len(picks) < league.roster_min or len(picks) > league.roster_max:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Roster must have between {league.roster_min} and {league.roster_max} players",
            )

        # Validate no duplicates
        if len(picks) != len(set(picks)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate picks are not allowed",
            )

        # Validate all picked users exist
        for user_id in picks:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} not found",
                )

        # Get or create roster
        roster = (
            db.query(FantasyRoster)
            .filter(
                and_(
                    FantasyRoster.league_id == league_id,
                    FantasyRoster.user_id == current_user.id,
                )
            )
            .first()
        )

        if not roster:
            roster = FantasyRoster(
                league_id=league_id,
                user_id=current_user.id,
            )
            db.add(roster)
            db.flush()

        # Delete old picks
        db.query(FantasyRosterPick).filter(
            FantasyRosterPick.roster_id == roster.id
        ).delete()

        # Add new picks
        for position, picked_user_id in enumerate(picks):
            pick = FantasyRosterPick(
                roster_id=roster.id,
                picked_user_id=picked_user_id,
                position=position + 1,
            )
            db.add(pick)

        db.commit()
        db.refresh(roster)

        logger.info(f"Updated roster for {current_user.email} in league {league.name}")
        return roster

    def get_my_roster(
        self,
        league_id: str,
        db: Session,
        current_user: User,
    ) -> Optional[FantasyRoster]:
        """
        Get current user's roster for a league.

        Args:
            league_id: League ID
            db: Database session
            current_user: Current user

        Returns:
            FantasyRoster or None if no roster exists
        """
        return (
            db.query(FantasyRoster)
            .filter(
                and_(
                    FantasyRoster.league_id == league_id,
                    FantasyRoster.user_id == current_user.id,
                )
            )
            .first()
        )

    def get_leaderboard(
        self,
        league_id: str,
        db: Session,
    ) -> List[FantasyLeaderboardEntry]:
        """
        Get fantasy league leaderboard.

        Args:
            league_id: League ID
            db: Database session

        Returns:
            List of FantasyLeaderboardEntry sorted by total score
        """
        league = self.get_league(league_id, db)

        rosters = (
            db.query(FantasyRoster)
            .filter(FantasyRoster.league_id == league_id)
            .all()
        )

        leaderboard = []
        for roster in rosters:
            # Calculate total score from all picks
            total_score = 0.0
            for pick in roster.picks:
                # Aggregate player's season stats
                player_stats = (
                    db.query(func.sum(PlayerPeriodStats.impact_score))
                    .filter(
                        and_(
                            PlayerPeriodStats.user_id == pick.picked_user_id,
                            PlayerPeriodStats.season_id == league.season_id,
                        )
                    )
                    .scalar()
                )
                total_score += float(player_stats or 0.0)

            leaderboard.append(
                FantasyLeaderboardEntry(
                    rank=0,  # Will be set after sorting
                    user_id=roster.user_id,
                    display_name=roster.user.display_name,
                    email=roster.user.email,
                    roster_id=roster.id,
                    total_score=total_score,
                    picks_count=len(roster.picks),
                    locked_at=roster.locked_at,
                )
            )

        # Sort by total score (descending)
        leaderboard.sort(key=lambda x: x.total_score, reverse=True)

        # Assign ranks
        for rank, entry in enumerate(leaderboard):
            entry.rank = rank + 1

        return leaderboard


# Create singleton instance
fantasy_service = FantasyService()
