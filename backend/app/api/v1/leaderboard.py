"""Leaderboard API endpoints."""

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.leaderboard import (
    LeaderboardResponse,
    LeaderboardEntry,
    PlayerInfo,
    PlayerPeriodStatsResponse,
)
from app.services.leaderboard import leaderboard_service


router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/seasons/{season_id}", response_model=LeaderboardResponse)
def get_season_leaderboard(
    season_id: str,
    period_type: Literal["day", "week", "month", "season"] = Query(
        "season", description="Type of period to display"
    ),
    period_start: Optional[date] = Query(
        None, description="Start date of the period (defaults to current period)"
    ),
    sort_by: str = Query(
        "impact_score",
        description="Column to sort by",
        pattern="^(impact_score|pts|reb|ast|blk|tov|commits|additions|deletions|files_changed)$",
    ),
    order: Literal["asc", "desc"] = Query("desc", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get leaderboard for a season.

    Supports filtering by period type and sorting by any metric.
    Results are paginated for performance.
    """
    items, total, period_start_used = leaderboard_service.get_leaderboard(
        season_id=season_id,
        db=db,
        period_type=period_type,
        period_start=period_start,
        sort_by=sort_by,
        order=order,
        page=page,
        limit=limit,
    )

    # Build response with ranks and trends
    entries = []
    for idx, (stats, user) in enumerate(items):
        rank = (page - 1) * limit + idx + 1

        # Calculate trend
        trend = leaderboard_service.calculate_trend(
            user_id=user.id,
            season_id=season_id,
            period_type=period_type,
            current_period_start=period_start_used,
            db=db,
        )

        entry = LeaderboardEntry(
            rank=rank,
            player=PlayerInfo(
                id=user.id,
                display_name=user.display_name,
                email=user.email,
                role=user.role,
                status=user.status,
            ),
            stats=PlayerPeriodStatsResponse.model_validate(stats),
            trend=trend,
        )
        entries.append(entry)

    # Calculate total pages
    pages = (total + limit - 1) // limit if total > 0 else 0

    return LeaderboardResponse(
        items=entries,
        total=total,
        page=page,
        pages=pages,
        period_type=period_type,
        period_start=period_start_used,
    )
