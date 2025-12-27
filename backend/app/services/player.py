"""Player profile service."""

import logging
from datetime import datetime
from typing import List, Literal, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session

from app.models.commit import Commit
from app.models.leaderboard import PlayerPeriodStats
from app.models.project import Repository
from app.models.season import Season, SeasonStatus
from app.models.user import User, GitIdentity
from app.schemas.player import (
    PlayerSeasonStats,
    PlayerCareerStats,
    RepoContribution,
    PlayerCommitSummary,
    TrendDataPoint,
)

logger = logging.getLogger(__name__)


class PlayerService:
    """Service for player profile operations."""

    def get_player_by_id(self, player_id: str, db: Session) -> User:
        """
        Get player by ID.

        Args:
            player_id: Player ID
            db: Database session

        Returns:
            User object

        Raises:
            HTTPException: If player not found
        """
        user = db.query(User).filter(User.id == player_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found",
            )
        return user

    def get_player_season_stats(
        self,
        player_id: str,
        season_id: Optional[str],
        db: Session,
    ) -> Optional[PlayerSeasonStats]:
        """
        Get player statistics for a specific season.

        Args:
            player_id: Player ID
            season_id: Season ID (if None, uses active season)
            db: Database session

        Returns:
            PlayerSeasonStats or None if no data
        """
        # If no season_id provided, try to get active season
        if not season_id:
            active_season = (
                db.query(Season)
                .filter(Season.status == SeasonStatus.ACTIVE)
                .first()
            )
            if not active_season:
                return None
            season_id = active_season.id
        else:
            active_season = db.query(Season).filter(Season.id == season_id).first()
            if not active_season:
                return None

        # Aggregate stats for the season
        stats = (
            db.query(
                func.sum(PlayerPeriodStats.commits).label("commits"),
                func.sum(PlayerPeriodStats.additions).label("additions"),
                func.sum(PlayerPeriodStats.deletions).label("deletions"),
                func.sum(PlayerPeriodStats.files_changed).label("files_changed"),
                func.sum(PlayerPeriodStats.pts).label("pts"),
                func.sum(PlayerPeriodStats.reb).label("reb"),
                func.sum(PlayerPeriodStats.ast).label("ast"),
                func.sum(PlayerPeriodStats.blk).label("blk"),
                func.sum(PlayerPeriodStats.tov).label("tov"),
                func.sum(PlayerPeriodStats.impact_score).label("impact_score"),
            )
            .filter(
                and_(
                    PlayerPeriodStats.user_id == player_id,
                    PlayerPeriodStats.season_id == season_id,
                )
            )
            .first()
        )

        if not stats or stats.commits is None or stats.commits == 0:
            return None

        return PlayerSeasonStats(
            season_id=season_id,
            season_name=active_season.name,
            commits=int(stats.commits or 0),
            additions=int(stats.additions or 0),
            deletions=int(stats.deletions or 0),
            files_changed=int(stats.files_changed or 0),
            pts=int(stats.pts or 0),
            reb=int(stats.reb or 0),
            ast=int(stats.ast or 0),
            blk=int(stats.blk or 0),
            tov=int(stats.tov or 0),
            impact_score=float(stats.impact_score or 0.0),
        )

    def get_player_career_stats(
        self,
        player_id: str,
        db: Session,
    ) -> PlayerCareerStats:
        """
        Get player all-time career statistics.

        Args:
            player_id: Player ID
            db: Database session

        Returns:
            PlayerCareerStats
        """
        # Get user's git identities
        git_emails = (
            db.query(GitIdentity.git_email)
            .filter(GitIdentity.user_id == player_id)
            .all()
        )
        email_list = [email[0] for email in git_emails]

        # Aggregate all-time stats from commits
        commit_stats = (
            db.query(
                func.count(Commit.id).label("total_commits"),
                func.sum(Commit.additions).label("total_additions"),
                func.sum(Commit.deletions).label("total_deletions"),
                func.sum(Commit.files_changed).label("total_files_changed"),
                func.min(Commit.commit_date).label("first_commit"),
                func.max(Commit.commit_date).label("last_commit"),
            )
            .filter(Commit.author_email.in_(email_list))
            .first()
        )

        # Aggregate all-time NBA metrics from period stats
        period_stats = (
            db.query(
                func.sum(PlayerPeriodStats.pts).label("total_pts"),
                func.sum(PlayerPeriodStats.reb).label("total_reb"),
                func.sum(PlayerPeriodStats.ast).label("total_ast"),
                func.sum(PlayerPeriodStats.blk).label("total_blk"),
                func.sum(PlayerPeriodStats.tov).label("total_tov"),
                func.sum(PlayerPeriodStats.impact_score).label("total_impact_score"),
                func.count(func.distinct(PlayerPeriodStats.season_id)).label("seasons_played"),
            )
            .filter(PlayerPeriodStats.user_id == player_id)
            .first()
        )

        return PlayerCareerStats(
            total_commits=int(commit_stats.total_commits or 0),
            total_additions=int(commit_stats.total_additions or 0),
            total_deletions=int(commit_stats.total_deletions or 0),
            total_files_changed=int(commit_stats.total_files_changed or 0),
            total_pts=int(period_stats.total_pts or 0),
            total_reb=int(period_stats.total_reb or 0),
            total_ast=int(period_stats.total_ast or 0),
            total_blk=int(period_stats.total_blk or 0),
            total_tov=int(period_stats.total_tov or 0),
            total_impact_score=float(period_stats.total_impact_score or 0.0),
            seasons_played=int(period_stats.seasons_played or 0),
            first_commit_date=commit_stats.first_commit.date() if commit_stats.first_commit else None,
            last_commit_date=commit_stats.last_commit.date() if commit_stats.last_commit else None,
        )

    def get_repo_contributions(
        self,
        player_id: str,
        season_id: Optional[str],
        db: Session,
    ) -> List[RepoContribution]:
        """
        Get player's contributions broken down by repository.

        Args:
            player_id: Player ID
            season_id: Season ID (optional, filters by season)
            db: Database session

        Returns:
            List of RepoContribution
        """
        # Get user's git identities
        git_emails = (
            db.query(GitIdentity.git_email)
            .filter(GitIdentity.user_id == player_id)
            .all()
        )
        email_list = [email[0] for email in git_emails]

        # Build query
        query = (
            db.query(
                Repository.id.label("repo_id"),
                Repository.name.label("repo_name"),
                func.count(Commit.id).label("commits"),
                func.sum(Commit.additions).label("additions"),
                func.sum(Commit.deletions).label("deletions"),
            )
            .join(Commit, Commit.repo_id == Repository.id)
            .filter(Commit.author_email.in_(email_list))
            .group_by(Repository.id, Repository.name)
            .order_by(desc(func.count(Commit.id)))
        )

        # Filter by season if provided
        if season_id:
            season = db.query(Season).filter(Season.id == season_id).first()
            if season:
                query = query.filter(
                    and_(
                        Commit.commit_date >= season.start_at,
                        Commit.commit_date <= season.end_at,
                    )
                )

        results = query.all()

        # Calculate impact scores (simplified - using additions + deletions)
        contributions = []
        for result in results:
            impact_score = (result.additions or 0) + (result.deletions or 0) * 0.6
            contributions.append(
                RepoContribution(
                    repo_id=result.repo_id,
                    repo_name=result.repo_name,
                    commits=result.commits or 0,
                    additions=result.additions or 0,
                    deletions=result.deletions or 0,
                    impact_score=impact_score,
                )
            )

        return contributions

    def get_recent_commits(
        self,
        player_id: str,
        db: Session,
        limit: int = 50,
    ) -> List[PlayerCommitSummary]:
        """
        Get player's recent commits.

        Args:
            player_id: Player ID
            db: Database session
            limit: Number of commits to return

        Returns:
            List of PlayerCommitSummary
        """
        # Get user's git identities
        git_emails = (
            db.query(GitIdentity.git_email)
            .filter(GitIdentity.user_id == player_id)
            .all()
        )
        email_list = [email[0] for email in git_emails]

        # Get recent commits
        commits = (
            db.query(
                Commit.sha,
                Commit.repo_id,
                Repository.name.label("repo_name"),
                Commit.message_title,
                Commit.commit_date,
                Commit.additions,
                Commit.deletions,
                Commit.files_changed,
            )
            .join(Repository, Commit.repo_id == Repository.id)
            .filter(Commit.author_email.in_(email_list))
            .order_by(desc(Commit.commit_date))
            .limit(limit)
            .all()
        )

        return [
            PlayerCommitSummary(
                sha=c.sha,
                repo_id=c.repo_id,
                repo_name=c.repo_name,
                message_title=c.message_title,
                commit_date=c.commit_date.date() if isinstance(c.commit_date, datetime) else c.commit_date,
                additions=c.additions,
                deletions=c.deletions,
                files_changed=c.files_changed,
            )
            for c in commits
        ]

    def get_player_trend(
        self,
        player_id: str,
        season_id: str,
        period_type: Literal["day", "week", "month", "season"],
        db: Session,
        limit: int = 12,
    ) -> List[TrendDataPoint]:
        """
        Get player trend data for visualization.

        Args:
            player_id: Player ID
            season_id: Season ID
            period_type: Type of period
            db: Database session
            limit: Number of periods to return

        Returns:
            List of TrendDataPoint
        """
        stats = (
            db.query(PlayerPeriodStats)
            .filter(
                and_(
                    PlayerPeriodStats.user_id == player_id,
                    PlayerPeriodStats.season_id == season_id,
                    PlayerPeriodStats.period_type == period_type,
                )
            )
            .order_by(desc(PlayerPeriodStats.period_start))
            .limit(limit)
            .all()
        )

        # Reverse to get chronological order
        stats.reverse()

        return [
            TrendDataPoint(
                period_start=s.period_start,
                period_type=s.period_type,
                commits=s.commits,
                pts=s.pts,
                impact_score=s.impact_score,
            )
            for s in stats
        ]


# Create singleton instance
player_service = PlayerService()
