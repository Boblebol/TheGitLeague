"""Hall of Fame service for all-time records and retired players."""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session

from app.models.award import Award, AwardType
from app.models.commit import Commit
from app.models.leaderboard import PlayerPeriodStats
from app.models.season import Season
from app.models.user import User, UserStatus, GitIdentity
from app.schemas.hall_of_fame import (
    AllTimeLeader,
    SeasonRecord,
    AwardRecord,
    StreakRecord,
    RetiredPlayer,
)

logger = logging.getLogger(__name__)


class HallOfFameService:
    """Service for Hall of Fame operations."""

    def get_all_time_leaders(self, db: Session, limit: int = 10) -> List[AllTimeLeader]:
        """
        Get all-time top players by total PTS.

        Args:
            db: Database session
            limit: Number of players to return (default: 10)

        Returns:
            List of AllTimeLeader
        """
        leaders = (
            db.query(
                User.id.label("user_id"),
                User.display_name,
                User.email,
                func.sum(PlayerPeriodStats.pts).label("total_pts"),
                func.sum(PlayerPeriodStats.commits).label("total_commits"),
                func.sum(PlayerPeriodStats.impact_score).label("total_impact_score"),
                func.count(func.distinct(PlayerPeriodStats.season_id)).label("seasons_played"),
            )
            .join(PlayerPeriodStats, User.id == PlayerPeriodStats.user_id)
            .group_by(User.id, User.display_name, User.email)
            .order_by(desc(func.sum(PlayerPeriodStats.pts)))
            .limit(limit)
            .all()
        )

        result = []
        for leader in leaders:
            # Count awards for this player
            awards_count = (
                db.query(func.count(Award.id))
                .filter(Award.user_id == leader.user_id)
                .scalar()
            ) or 0

            result.append(
                AllTimeLeader(
                    user_id=leader.user_id,
                    display_name=leader.display_name,
                    email=leader.email,
                    total_pts=int(leader.total_pts or 0),
                    total_commits=int(leader.total_commits or 0),
                    total_impact_score=float(leader.total_impact_score or 0.0),
                    awards_count=int(awards_count),
                    seasons_played=int(leader.seasons_played or 0),
                )
            )

        return result

    def get_most_commits_single_season(self, db: Session) -> Optional[SeasonRecord]:
        """
        Get the record for most commits in a single season.

        Args:
            db: Database session

        Returns:
            SeasonRecord or None
        """
        record = (
            db.query(
                PlayerPeriodStats.user_id,
                User.display_name,
                User.email,
                PlayerPeriodStats.season_id,
                Season.name.label("season_name"),
                func.sum(PlayerPeriodStats.commits).label("total_commits"),
            )
            .join(User, PlayerPeriodStats.user_id == User.id)
            .join(Season, PlayerPeriodStats.season_id == Season.id)
            .group_by(
                PlayerPeriodStats.user_id,
                User.display_name,
                User.email,
                PlayerPeriodStats.season_id,
                Season.name,
                Season.start_at,
            )
            .order_by(desc(func.sum(PlayerPeriodStats.commits)))
            .first()
        )

        if not record:
            return None

        return SeasonRecord(
            user_id=record.user_id,
            display_name=record.display_name,
            email=record.email,
            season_id=record.season_id,
            season_name=record.season_name,
            value=int(record.total_commits or 0),
            year=datetime.now().year,  # Simplified - should extract from season
        )

    def get_highest_pts_single_season(self, db: Session) -> Optional[SeasonRecord]:
        """
        Get the record for highest PTS in a single season.

        Args:
            db: Database session

        Returns:
            SeasonRecord or None
        """
        record = (
            db.query(
                PlayerPeriodStats.user_id,
                User.display_name,
                User.email,
                PlayerPeriodStats.season_id,
                Season.name.label("season_name"),
                func.sum(PlayerPeriodStats.pts).label("total_pts"),
            )
            .join(User, PlayerPeriodStats.user_id == User.id)
            .join(Season, PlayerPeriodStats.season_id == Season.id)
            .group_by(
                PlayerPeriodStats.user_id,
                User.display_name,
                User.email,
                PlayerPeriodStats.season_id,
                Season.name,
                Season.start_at,
            )
            .order_by(desc(func.sum(PlayerPeriodStats.pts)))
            .first()
        )

        if not record:
            return None

        return SeasonRecord(
            user_id=record.user_id,
            display_name=record.display_name,
            email=record.email,
            season_id=record.season_id,
            season_name=record.season_name,
            value=int(record.total_pts or 0),
            year=datetime.now().year,
        )

    def get_most_awarded_player(self, db: Session) -> Optional[AwardRecord]:
        """
        Get the player with the most awards.

        Args:
            db: Database session

        Returns:
            AwardRecord or None
        """
        # Get award counts by type
        award_counts = (
            db.query(
                Award.user_id,
                User.display_name,
                User.email,
                func.count(Award.id).label("total_awards"),
                func.sum(
                    func.case((Award.award_type == AwardType.PLAYER_OF_WEEK, 1), else_=0)
                ).label("player_of_week_count"),
                func.sum(
                    func.case((Award.award_type == AwardType.PLAYER_OF_MONTH, 1), else_=0)
                ).label("player_of_month_count"),
                func.sum(
                    func.case((Award.award_type == AwardType.MVP, 1), else_=0)
                ).label("mvp_count"),
            )
            .join(User, Award.user_id == User.id)
            .group_by(Award.user_id, User.display_name, User.email)
            .order_by(desc(func.count(Award.id)))
            .first()
        )

        if not award_counts:
            return None

        return AwardRecord(
            user_id=award_counts.user_id,
            display_name=award_counts.display_name,
            email=award_counts.email,
            awards_count=int(award_counts.total_awards or 0),
            player_of_week_count=int(award_counts.player_of_week_count or 0),
            player_of_month_count=int(award_counts.player_of_month_count or 0),
            mvp_count=int(award_counts.mvp_count or 0),
        )

    def get_longest_streak(self, db: Session) -> Optional[StreakRecord]:
        """
        Get the longest consecutive days streak.

        Args:
            db: Database session

        Returns:
            StreakRecord or None

        Note: This is a simplified implementation.
        A production version would need to calculate streaks more efficiently.
        """
        # Get all users with commits
        users_with_commits = (
            db.query(User.id, User.display_name, User.email)
            .join(GitIdentity, User.id == GitIdentity.user_id)
            .join(Commit, GitIdentity.git_email == Commit.author_email)
            .group_by(User.id, User.display_name, User.email)
            .all()
        )

        max_streak = None
        max_streak_days = 0

        for user in users_with_commits:
            # Get all distinct commit dates for this user
            commit_dates = (
                db.query(func.date(Commit.commit_date).distinct())
                .join(GitIdentity, Commit.author_email == GitIdentity.git_email)
                .filter(GitIdentity.user_id == user.id)
                .order_by(func.date(Commit.commit_date))
                .all()
            )

            if not commit_dates:
                continue

            # Calculate longest streak
            dates = [d[0] for d in commit_dates]
            current_streak_start = dates[0]
            current_streak_end = dates[0]
            current_streak_days = 1

            best_streak_start = dates[0]
            best_streak_end = dates[0]
            best_streak_days = 1

            for i in range(1, len(dates)):
                if dates[i] == dates[i - 1] + timedelta(days=1):
                    # Consecutive day
                    current_streak_end = dates[i]
                    current_streak_days += 1

                    if current_streak_days > best_streak_days:
                        best_streak_days = current_streak_days
                        best_streak_start = current_streak_start
                        best_streak_end = current_streak_end
                else:
                    # Streak broken
                    current_streak_start = dates[i]
                    current_streak_end = dates[i]
                    current_streak_days = 1

            if best_streak_days > max_streak_days:
                max_streak_days = best_streak_days
                max_streak = StreakRecord(
                    user_id=user.id,
                    display_name=user.display_name,
                    email=user.email,
                    streak_days=best_streak_days,
                    start_date=best_streak_start,
                    end_date=best_streak_end,
                )

        return max_streak

    def get_retired_players(self, db: Session) -> List[RetiredPlayer]:
        """
        Get all retired players with their career stats.

        Args:
            db: Database session

        Returns:
            List of RetiredPlayer
        """
        retired_users = (
            db.query(User)
            .filter(User.status == UserStatus.RETIRED)
            .order_by(User.updated_at.desc())  # Most recently retired first
            .all()
        )

        result = []
        for user in retired_users:
            # Get career stats
            career_stats = (
                db.query(
                    func.sum(PlayerPeriodStats.commits).label("total_commits"),
                    func.sum(PlayerPeriodStats.pts).label("total_pts"),
                    func.count(func.distinct(PlayerPeriodStats.season_id)).label("seasons_played"),
                )
                .filter(PlayerPeriodStats.user_id == user.id)
                .first()
            )

            # Get awards count
            awards_count = (
                db.query(func.count(Award.id))
                .filter(Award.user_id == user.id)
                .scalar()
            ) or 0

            result.append(
                RetiredPlayer(
                    user_id=user.id,
                    display_name=user.display_name,
                    email=user.email,
                    role=user.role,
                    retired_at=user.updated_at.date(),
                    total_commits=int(career_stats.total_commits or 0) if career_stats else 0,
                    total_pts=int(career_stats.total_pts or 0) if career_stats else 0,
                    awards_count=int(awards_count),
                    seasons_played=int(career_stats.seasons_played or 0) if career_stats else 0,
                )
            )

        return result


# Create singleton instance
hall_of_fame_service = HallOfFameService()
