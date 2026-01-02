"""Player profile API endpoints."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.player import (
    PlayerProfileResponse,
    PlayerTrendResponse,
)
from app.services.player import player_service


router = APIRouter(prefix="/players", tags=["players"])


@router.get("/{player_id}", response_model=PlayerProfileResponse)
def get_player_profile(
    player_id: str,
    season_id: Optional[str] = Query(
        None, description="Season ID (defaults to active season)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive player profile.

    Includes:
    - Current season stats (or specified season)
    - Career stats (all-time)
    - Repository contributions breakdown
    - Recent commits (last 50)
    """
    # Get player
    player = player_service.get_player_by_id(player_id, db)

    # Get current season stats
    current_season_stats = player_service.get_player_season_stats(
        player_id, season_id, db
    )

    # Get career stats
    career_stats = player_service.get_player_career_stats(player_id, db)

    # Get repo contributions
    repo_contributions = player_service.get_repo_contributions(
        player_id, season_id, db
    )

    # Get recent commits
    recent_commits = player_service.get_recent_commits(player_id, db, limit=50)

    return PlayerProfileResponse(
        id=player.id,
        display_name=player.display_name,
        email=player.email,
        role=player.role,
        status=player.status,
        current_season_stats=current_season_stats,
        career_stats=career_stats,
        repo_contributions=repo_contributions,
        recent_commits=recent_commits,
    )


@router.get("/{player_id}/stats/trend", response_model=PlayerTrendResponse)
def get_player_trend(
    player_id: str,
    season_id: str = Query(..., description="Season ID"),
    period_type: Literal["day", "week", "month", "season"] = Query(
        "week", description="Period type for trend data"
    ),
    limit: int = Query(12, ge=1, le=52, description="Number of periods to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get player trend data for visualization.

    Returns historical data points for the specified period type.
    Default is last 12 weeks.
    """
    # Validate player exists
    player_service.get_player_by_id(player_id, db)

    # Get trend data
    data_points = player_service.get_player_trend(
        player_id, season_id, period_type, db, limit
    )

    return PlayerTrendResponse(
        player_id=player_id,
        season_id=season_id,
        period_type=period_type,
        data_points=data_points,
    )
