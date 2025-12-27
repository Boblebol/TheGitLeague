"""Hall of Fame API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_commissioner
from app.models.user import User
from app.schemas.user import UserResponse
from app.schemas.hall_of_fame import HallOfFameResponse
from app.services.hall_of_fame import hall_of_fame_service
from app.services.user import user_service


router = APIRouter(prefix="/hall-of-fame", tags=["hall-of-fame"])


@router.get("", response_model=HallOfFameResponse)
def get_hall_of_fame(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get Hall of Fame data including:
    - All-time top 10 leaders by total PTS
    - Various records (most commits, highest PTS, most awards, longest streak)
    - Retired players (legends)

    All users can view the Hall of Fame.
    """
    # Get all-time leaders
    all_time_leaders = hall_of_fame_service.get_all_time_leaders(db, limit=10)

    # Get records
    most_commits_record = hall_of_fame_service.get_most_commits_single_season(db)
    highest_pts_record = hall_of_fame_service.get_highest_pts_single_season(db)
    most_awarded_record = hall_of_fame_service.get_most_awarded_player(db)
    longest_streak_record = hall_of_fame_service.get_longest_streak(db)

    records = {
        "most_commits_single_season": most_commits_record.model_dump() if most_commits_record else None,
        "highest_pts_single_season": highest_pts_record.model_dump() if highest_pts_record else None,
        "most_awards": most_awarded_record.model_dump() if most_awarded_record else None,
        "longest_streak": longest_streak_record.model_dump() if longest_streak_record else None,
    }

    # Get retired players
    retired_players = hall_of_fame_service.get_retired_players(db)

    return HallOfFameResponse(
        all_time_leaders=all_time_leaders,
        records=records,
        retired_players=retired_players,
    )


@router.patch("/users/{user_id}/retire", response_model=UserResponse)
def retire_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """
    Retire a user (Commissioner only).

    Retired users:
    - Are excluded from active leaderboards
    - Appear in the Hall of Fame retired players section
    - Can still view their profile and historical data
    - Historical stats are preserved
    """
    user = user_service.retire_user(user_id, db, current_user)
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}/unretire", response_model=UserResponse)
def unretire_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """
    Reactivate a retired user (Commissioner only).

    The user will be reactivated with 'approved' status and will:
    - Appear in active leaderboards again
    - Be removed from the Hall of Fame retired players section
    - Be able to earn new awards
    """
    user = user_service.unretire_user(user_id, db, current_user)
    return UserResponse.model_validate(user)
