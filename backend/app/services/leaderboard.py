"""Leaderboard service for player rankings."""

import logging
from datetime import date, timedelta
from typing import Literal, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, asc, func
from sqlalchemy.orm import Session

from app.models.leaderboard import PlayerPeriodStats
from app.models.season import Season
from app.models.user import User
from app.utils.periods import get_period_start

logger = logging.getLogger(__name__)


class LeaderboardService:
    """Service for leaderboard operations."""

    def get_leaderboard(
        self,
        season_id: str,
        db: Session,
        period_type: Literal["day", "week", "month", "season"] = "season",
        period_start: Optional[date] = None,
        sort_by: str = "impact_score",
        order: Literal["asc", "desc"] = "desc",
        page: int = 1,
        limit: int = 50,
    ) -> Tuple[list[Tuple[PlayerPeriodStats, User]], int, date]:
        """
        Get leaderboard for a season and period.

        Args:
            season_id: Season ID
            db: Database session
            period_type: Type of period (day, week, month, season)
            period_start: Start date of the period (optional, uses current period if not provided)
            sort_by: Column to sort by (default: impact_score)
            order: Sort order (asc or desc)
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (leaderboard items, total count, period_start used)
        """
        # Validate season exists
        season = db.query(Season).filter(Season.id == season_id).first()
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )

        # If period_start not provided, use current period
        if period_start is None:
            from datetime import datetime
            period_start = get_period_start(datetime.utcnow(), period_type, season)

        # Build base query
        query = (
            db.query(PlayerPeriodStats, User)
            .join(User, PlayerPeriodStats.user_id == User.id)
            .filter(
                and_(
                    PlayerPeriodStats.season_id == season_id,
                    PlayerPeriodStats.period_type == period_type,
                    PlayerPeriodStats.period_start == period_start,
                )
            )
        )

        # Validate sort column
        valid_sort_columns = [
            "impact_score", "pts", "reb", "ast", "blk", "tov",
            "commits", "additions", "deletions", "files_changed"
        ]
        if sort_by not in valid_sort_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort column. Must be one of: {', '.join(valid_sort_columns)}",
            )

        # Apply sorting
        sort_column = getattr(PlayerPeriodStats, sort_by)
        if order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Add secondary sort for ties (commits, then email)
        query = query.order_by(
            desc(PlayerPeriodStats.commits),
            asc(User.email)
        )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * limit
        items = query.offset(offset).limit(limit).all()

        return items, total, period_start

    def calculate_trend(
        self,
        user_id: str,
        season_id: str,
        period_type: Literal["day", "week", "month", "season"],
        current_period_start: date,
        db: Session,
    ) -> Optional[Literal["up", "down", "neutral"]]:
        """
        Calculate trend by comparing current period to previous period.

        Args:
            user_id: User ID
            season_id: Season ID
            period_type: Type of period
            current_period_start: Start date of current period
            db: Database session

        Returns:
            'up', 'down', or 'neutral' (None if no previous data)
        """
        # Get current period stats
        current = (
            db.query(PlayerPeriodStats)
            .filter(
                and_(
                    PlayerPeriodStats.user_id == user_id,
                    PlayerPeriodStats.season_id == season_id,
                    PlayerPeriodStats.period_type == period_type,
                    PlayerPeriodStats.period_start == current_period_start,
                )
            )
            .first()
        )

        if not current:
            return None

        # Calculate previous period start
        if period_type == "day":
            previous_period_start = current_period_start - timedelta(days=1)
        elif period_type == "week":
            previous_period_start = current_period_start - timedelta(weeks=1)
        elif period_type == "month":
            # Go back to first day of previous month
            if current_period_start.month == 1:
                previous_period_start = current_period_start.replace(
                    year=current_period_start.year - 1, month=12, day=1
                )
            else:
                previous_period_start = current_period_start.replace(
                    month=current_period_start.month - 1, day=1
                )
        elif period_type == "season":
            # No previous period for season
            return None
        else:
            return None

        # Get previous period stats
        previous = (
            db.query(PlayerPeriodStats)
            .filter(
                and_(
                    PlayerPeriodStats.user_id == user_id,
                    PlayerPeriodStats.season_id == season_id,
                    PlayerPeriodStats.period_type == period_type,
                    PlayerPeriodStats.period_start == previous_period_start,
                )
            )
            .first()
        )

        if not previous or previous.impact_score == 0:
            # No previous data or zero score, can't compare
            return None

        # Compare with 5% threshold
        threshold = 0.05
        if current.impact_score > previous.impact_score * (1 + threshold):
            return "up"
        elif current.impact_score < previous.impact_score * (1 - threshold):
            return "down"
        else:
            return "neutral"


# Create singleton instance
leaderboard_service = LeaderboardService()
