"""Award calculation and management service."""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session

from app.models.award import Award, PlayOfTheDay, AwardType
from app.models.commit import Commit
from app.models.leaderboard import PlayerPeriodStats
from app.models.project import Repository
from app.models.season import Season, SeasonStatus, Absence
from app.models.user import User, GitIdentity
from app.utils.scoring import (
    ScoringCoefficients,
    calculate_pts,
    calculate_reb,
    calculate_ast,
    calculate_blk,
    calculate_tov,
)
from app.services.scoring import scoring_service

logger = logging.getLogger(__name__)


class AwardService:
    """Service for award calculation and management."""

    def _is_user_absent(self, user_id: str, period_start: date, db: Session) -> bool:
        """
        Check if user is absent during the period.

        Args:
            user_id: User ID
            period_start: Period start date
            db: Database session

        Returns:
            True if user is absent
        """
        absence = (
            db.query(Absence)
            .filter(
                and_(
                    Absence.user_id == user_id,
                    Absence.start_at <= period_start,
                    Absence.end_at >= period_start,
                )
            )
            .first()
        )
        return absence is not None

    def calculate_weekly_awards(self, db: Session, last_week_start: Optional[date] = None) -> int:
        """
        Calculate Player of the Week awards for all active seasons.

        Args:
            db: Database session
            last_week_start: Start date of the week to calculate (default: last week)

        Returns:
            Number of awards created
        """
        if last_week_start is None:
            # Calculate last Monday
            today = datetime.now().date()
            days_since_monday = today.weekday()
            last_week_start = today - timedelta(days=days_since_monday + 7)

        logger.info(f"Calculating weekly awards for week starting {last_week_start}")

        active_seasons = db.query(Season).filter(Season.status == SeasonStatus.ACTIVE).all()
        awards_created = 0

        for season in active_seasons:
            # Get top player by impact score for the week
            top_stats = (
                db.query(PlayerPeriodStats, User)
                .join(User, PlayerPeriodStats.user_id == User.id)
                .filter(
                    and_(
                        PlayerPeriodStats.season_id == season.id,
                        PlayerPeriodStats.period_type == "week",
                        PlayerPeriodStats.period_start == last_week_start,
                    )
                )
                .order_by(
                    desc(PlayerPeriodStats.impact_score),
                    desc(PlayerPeriodStats.commits),
                    User.email.asc(),  # Tiebreaker
                )
                .first()
            )

            if not top_stats:
                logger.info(f"No stats found for season {season.name}, week {last_week_start}")
                continue

            stats, user = top_stats

            # Check if user is absent
            if self._is_user_absent(user.id, last_week_start, db):
                logger.info(f"User {user.email} is absent, skipping award")
                continue

            # Create or update award
            existing_award = (
                db.query(Award)
                .filter(
                    and_(
                        Award.season_id == season.id,
                        Award.period_type == "week",
                        Award.period_start == last_week_start,
                        Award.award_type == AwardType.PLAYER_OF_WEEK,
                    )
                )
                .first()
            )

            if existing_award:
                logger.info(f"Award already exists for season {season.name}, week {last_week_start}")
                continue

            award = Award(
                season_id=season.id,
                period_type="week",
                period_start=last_week_start,
                award_type=AwardType.PLAYER_OF_WEEK,
                user_id=user.id,
                score=stats.impact_score,
                metadata_json={
                    "pts": stats.pts,
                    "reb": stats.reb,
                    "ast": stats.ast,
                    "blk": stats.blk,
                    "tov": stats.tov,
                    "commits": stats.commits,
                    "additions": stats.additions,
                    "deletions": stats.deletions,
                },
            )
            db.add(award)
            awards_created += 1
            logger.info(f"Created Player of Week award for {user.email} in season {season.name}")

        db.commit()
        return awards_created

    def calculate_monthly_awards(self, db: Session, last_month_start: Optional[date] = None) -> int:
        """
        Calculate Player of the Month awards for all active seasons.

        Args:
            db: Database session
            last_month_start: Start date of the month to calculate (default: last month)

        Returns:
            Number of awards created
        """
        if last_month_start is None:
            # First day of last month
            today = datetime.now().date()
            if today.month == 1:
                last_month_start = today.replace(year=today.year - 1, month=12, day=1)
            else:
                last_month_start = today.replace(month=today.month - 1, day=1)

        logger.info(f"Calculating monthly awards for month starting {last_month_start}")

        active_seasons = db.query(Season).filter(Season.status == SeasonStatus.ACTIVE).all()
        awards_created = 0

        for season in active_seasons:
            # Get top player by impact score for the month
            top_stats = (
                db.query(PlayerPeriodStats, User)
                .join(User, PlayerPeriodStats.user_id == User.id)
                .filter(
                    and_(
                        PlayerPeriodStats.season_id == season.id,
                        PlayerPeriodStats.period_type == "month",
                        PlayerPeriodStats.period_start == last_month_start,
                    )
                )
                .order_by(
                    desc(PlayerPeriodStats.impact_score),
                    desc(PlayerPeriodStats.commits),
                    User.email.asc(),
                )
                .first()
            )

            if not top_stats:
                logger.info(f"No stats found for season {season.name}, month {last_month_start}")
                continue

            stats, user = top_stats

            # Check if user is absent (check middle of month)
            mid_month = last_month_start + timedelta(days=15)
            if self._is_user_absent(user.id, mid_month, db):
                logger.info(f"User {user.email} is absent, skipping award")
                continue

            # Create or update award
            existing_award = (
                db.query(Award)
                .filter(
                    and_(
                        Award.season_id == season.id,
                        Award.period_type == "month",
                        Award.period_start == last_month_start,
                        Award.award_type == AwardType.PLAYER_OF_MONTH,
                    )
                )
                .first()
            )

            if existing_award:
                logger.info(f"Award already exists for season {season.name}, month {last_month_start}")
                continue

            award = Award(
                season_id=season.id,
                period_type="month",
                period_start=last_month_start,
                award_type=AwardType.PLAYER_OF_MONTH,
                user_id=user.id,
                score=stats.impact_score,
                metadata_json={
                    "pts": stats.pts,
                    "reb": stats.reb,
                    "ast": stats.ast,
                    "blk": stats.blk,
                    "tov": stats.tov,
                    "commits": stats.commits,
                    "additions": stats.additions,
                    "deletions": stats.deletions,
                },
            )
            db.add(award)
            awards_created += 1
            logger.info(f"Created Player of Month award for {user.email} in season {season.name}")

        db.commit()
        return awards_created

    def calculate_season_mvp(self, season_id: str, db: Session) -> Optional[Award]:
        """
        Calculate Season MVP award.

        Args:
            season_id: Season ID
            db: Database session

        Returns:
            Award or None
        """
        logger.info(f"Calculating MVP for season {season_id}")

        season = db.query(Season).filter(Season.id == season_id).first()
        if not season:
            logger.error(f"Season {season_id} not found")
            return None

        # Aggregate all period stats for the season
        top_player = (
            db.query(
                PlayerPeriodStats.user_id,
                User,
                func.sum(PlayerPeriodStats.impact_score).label("total_impact_score"),
                func.sum(PlayerPeriodStats.pts).label("total_pts"),
                func.sum(PlayerPeriodStats.reb).label("total_reb"),
                func.sum(PlayerPeriodStats.ast).label("total_ast"),
                func.sum(PlayerPeriodStats.blk).label("total_blk"),
                func.sum(PlayerPeriodStats.tov).label("total_tov"),
                func.sum(PlayerPeriodStats.commits).label("total_commits"),
                func.sum(PlayerPeriodStats.additions).label("total_additions"),
                func.sum(PlayerPeriodStats.deletions).label("total_deletions"),
            )
            .join(User, PlayerPeriodStats.user_id == User.id)
            .filter(PlayerPeriodStats.season_id == season_id)
            .group_by(PlayerPeriodStats.user_id, User.id, User.email)
            .order_by(
                desc(func.sum(PlayerPeriodStats.impact_score)),
                desc(func.sum(PlayerPeriodStats.commits)),
                User.email.asc(),
            )
            .first()
        )

        if not top_player:
            logger.info(f"No stats found for season {season_id}")
            return None

        user_id, user, total_impact, total_pts, total_reb, total_ast, total_blk, total_tov, total_commits, total_additions, total_deletions = top_player

        # Check existing award
        existing_award = (
            db.query(Award)
            .filter(
                and_(
                    Award.season_id == season_id,
                    Award.period_type == "season",
                    Award.award_type == AwardType.MVP,
                )
            )
            .first()
        )

        if existing_award:
            logger.info(f"MVP award already exists for season {season_id}")
            return existing_award

        award = Award(
            season_id=season_id,
            period_type="season",
            period_start=season.start_at.date(),
            award_type=AwardType.MVP,
            user_id=user_id,
            score=total_impact,
            metadata_json={
                "pts": total_pts,
                "reb": total_reb,
                "ast": total_ast,
                "blk": total_blk,
                "tov": total_tov,
                "commits": total_commits,
                "additions": total_additions,
                "deletions": total_deletions,
            },
        )
        db.add(award)
        db.commit()

        logger.info(f"Created MVP award for {user.email} in season {season.name}")
        return award

    def calculate_play_of_day(self, db: Session, target_date: Optional[date] = None) -> int:
        """
        Calculate Play of the Day for all active seasons.

        Args:
            db: Database session
            target_date: Date to calculate (default: yesterday)

        Returns:
            Number of plays created
        """
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).date()

        logger.info(f"Calculating Play of the Day for {target_date}")

        active_seasons = db.query(Season).filter(Season.status == SeasonStatus.ACTIVE).all()
        plays_created = 0

        for season in active_seasons:
            # Get all commits for the day
            commits = (
                db.query(Commit, Repository)
                .join(Repository, Commit.repo_id == Repository.id)
                .filter(
                    and_(
                        Repository.project_id == season.project_id,
                        func.date(Commit.commit_date) == target_date,
                        Commit.is_merge == False,  # Exclude merge commits
                    )
                )
                .all()
            )

            if not commits:
                logger.info(f"No commits found for season {season.name}, date {target_date}")
                continue

            # Get scoring coefficients
            coeffs = scoring_service.get_scoring_coefficients(season.project_id, db)

            # Score each commit
            scored_commits = []
            for commit, repo in commits:
                score = (
                    calculate_pts(commit, coeffs) * 1.0
                    + calculate_reb(commit, coeffs) * 0.6
                    + calculate_ast(commit, coeffs) * 0.8
                    + calculate_blk(commit, coeffs) * 1.2
                    - abs(calculate_tov(commit, coeffs)) * 0.7
                )
                scored_commits.append((commit, repo, score))

            if not scored_commits:
                continue

            # Select top commit
            best_commit, best_repo, best_score = max(scored_commits, key=lambda x: x[2])

            # Get author
            author = (
                db.query(User)
                .join(GitIdentity, User.id == GitIdentity.user_id)
                .filter(GitIdentity.git_email == best_commit.author_email)
                .first()
            )

            if not author:
                logger.warning(f"No user found for commit {best_commit.sha}")
                continue

            # Check existing play
            existing_play = (
                db.query(PlayOfTheDay)
                .filter(
                    and_(
                        PlayOfTheDay.season_id == season.id,
                        PlayOfTheDay.date == target_date,
                    )
                )
                .first()
            )

            if existing_play:
                logger.info(f"Play of Day already exists for season {season.name}, date {target_date}")
                continue

            play = PlayOfTheDay(
                season_id=season.id,
                date=target_date,
                commit_sha=best_commit.sha,
                user_id=author.id,
                score=best_score,
                metadata_json={
                    "repo_id": best_repo.id,
                    "repo_name": best_repo.name,
                    "message": best_commit.message_title,
                    "additions": best_commit.additions,
                    "deletions": best_commit.deletions,
                    "files_changed": best_commit.files_changed,
                },
            )
            db.add(play)
            plays_created += 1
            logger.info(f"Created Play of Day for {author.email} in season {season.name}")

        db.commit()
        return plays_created

    def get_awards(
        self,
        db: Session,
        season_id: Optional[str] = None,
        user_id: Optional[str] = None,
        award_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Award]:
        """
        Get awards with optional filters.

        Args:
            db: Database session
            season_id: Filter by season
            user_id: Filter by user
            award_type: Filter by award type
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of Awards
        """
        query = db.query(Award)

        if season_id:
            query = query.filter(Award.season_id == season_id)
        if user_id:
            query = query.filter(Award.user_id == user_id)
        if award_type:
            query = query.filter(Award.award_type == award_type)

        return query.order_by(desc(Award.created_at)).offset(skip).limit(limit).all()

    def get_plays_of_day(
        self,
        db: Session,
        season_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PlayOfTheDay]:
        """
        Get plays of the day with optional filters.

        Args:
            db: Database session
            season_id: Filter by season
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of PlayOfTheDay
        """
        query = db.query(PlayOfTheDay)

        if season_id:
            query = query.filter(PlayOfTheDay.season_id == season_id)

        return query.order_by(desc(PlayOfTheDay.date)).offset(skip).limit(limit).all()


# Create singleton instance
award_service = AwardService()
