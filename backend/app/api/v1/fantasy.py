"""Fantasy league API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_commissioner
from app.models.user import User
from app.schemas.fantasy import (
    FantasyLeagueCreate,
    FantasyLeagueResponse,
    FantasyRosterResponse,
    RosterUpdateRequest,
    RosterPickResponse,
    FantasyLeaderboardResponse,
)
from app.services.fantasy import fantasy_service


router = APIRouter(prefix="/fantasy-leagues", tags=["fantasy"])


@router.post("", response_model=FantasyLeagueResponse, status_code=status.HTTP_201_CREATED)
def create_fantasy_league(
    league_data: FantasyLeagueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """
    Create a new fantasy league (Commissioner only).

    Defines roster rules and optional lock date.
    """
    league = fantasy_service.create_league(league_data, db, current_user)

    # Count participants
    participants_count = len(league.participants)
    is_locked = league.lock_at is not None and league.lock_at < league.created_at

    return FantasyLeagueResponse(
        id=league.id,
        name=league.name,
        season_id=league.season_id,
        season_name=league.season.name if league.season else None,
        roster_min=league.roster_min,
        roster_max=league.roster_max,
        lock_at=league.lock_at,
        created_at=league.created_at,
        participants_count=participants_count,
        is_locked=is_locked,
    )


@router.get("", response_model=List[FantasyLeagueResponse])
def list_fantasy_leagues(
    season_id: Optional[str] = Query(None, description="Filter by season"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=100, description="Pagination limit"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all fantasy leagues with optional filters.

    Supports filtering by season and pagination.
    """
    leagues = fantasy_service.list_leagues(db, season_id, skip, limit)

    return [
        FantasyLeagueResponse(
            id=league.id,
            name=league.name,
            season_id=league.season_id,
            season_name=league.season.name if league.season else None,
            roster_min=league.roster_min,
            roster_max=league.roster_max,
            lock_at=league.lock_at,
            created_at=league.created_at,
            participants_count=len(league.participants),
            is_locked=(
                league.lock_at is not None
                and league.lock_at < fantasy_service.get_league(league.id, db).created_at
            ),
        )
        for league in leagues
    ]


@router.get("/{league_id}", response_model=FantasyLeagueResponse)
def get_fantasy_league(
    league_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get fantasy league details.
    """
    league = fantasy_service.get_league(league_id, db)

    from datetime import datetime
    is_locked = league.lock_at is not None and datetime.utcnow() > league.lock_at

    return FantasyLeagueResponse(
        id=league.id,
        name=league.name,
        season_id=league.season_id,
        season_name=league.season.name if league.season else None,
        roster_min=league.roster_min,
        roster_max=league.roster_max,
        lock_at=league.lock_at,
        created_at=league.created_at,
        participants_count=len(league.participants),
        is_locked=is_locked,
    )


@router.post("/{league_id}/join", status_code=status.HTTP_201_CREATED)
def join_fantasy_league(
    league_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Join a fantasy league.

    Creates a participant entry. User can then create their roster.
    """
    fantasy_service.join_league(league_id, db, current_user)
    return {"message": "Successfully joined fantasy league"}


@router.put("/{league_id}/roster", response_model=FantasyRosterResponse)
def update_fantasy_roster(
    league_id: str,
    roster_data: RosterUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update fantasy roster.

    Validates:
    - League is not locked
    - Roster size is within min/max bounds
    - No duplicate picks
    - All picked users exist
    """
    roster = fantasy_service.update_roster(league_id, roster_data.picks, db, current_user)

    # Build pick responses
    picks = [
        RosterPickResponse(
            picked_user_id=pick.picked_user_id,
            display_name=pick.picked_user.display_name,
            email=pick.picked_user.email,
            position=pick.position,
        )
        for pick in roster.picks
    ]

    return FantasyRosterResponse(
        id=roster.id,
        league_id=roster.league_id,
        user_id=roster.user_id,
        locked_at=roster.locked_at,
        created_at=roster.created_at,
        picks=picks,
    )


@router.get("/{league_id}/roster", response_model=FantasyRosterResponse)
def get_my_fantasy_roster(
    league_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's fantasy roster for a league.

    Returns empty roster if no picks have been made yet.
    """
    roster = fantasy_service.get_my_roster(league_id, db, current_user)

    if not roster:
        # Return empty roster
        from app.models.fantasy import FantasyRoster
        return FantasyRosterResponse(
            id="",
            league_id=league_id,
            user_id=current_user.id,
            locked_at=None,
            created_at=fantasy_service.get_league(league_id, db).created_at,
            picks=[],
        )

    # Build pick responses
    picks = [
        RosterPickResponse(
            picked_user_id=pick.picked_user_id,
            display_name=pick.picked_user.display_name,
            email=pick.picked_user.email,
            position=pick.position,
        )
        for pick in roster.picks
    ]

    return FantasyRosterResponse(
        id=roster.id,
        league_id=roster.league_id,
        user_id=roster.user_id,
        locked_at=roster.locked_at,
        created_at=roster.created_at,
        picks=picks,
    )


@router.get("/{league_id}/leaderboard", response_model=FantasyLeaderboardResponse)
def get_fantasy_leaderboard(
    league_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get fantasy league leaderboard.

    Ranks participants by total score (sum of all picked players' impact scores).
    """
    league = fantasy_service.get_league(league_id, db)
    entries = fantasy_service.get_leaderboard(league_id, db)

    return FantasyLeaderboardResponse(
        league_id=league_id,
        league_name=league.name,
        entries=entries,
    )
