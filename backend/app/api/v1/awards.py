"""Awards and Play of the Day API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.award import AwardResponse, PlayOfTheDayResponse
from app.services.award import award_service


router = APIRouter(prefix="/awards", tags=["awards"])


@router.get("", response_model=List[AwardResponse])
def list_awards(
    season_id: Optional[str] = Query(None, description="Filter by season"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    award_type: Optional[str] = Query(None, description="Filter by award type"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=100, description="Pagination limit"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all awards with optional filters.

    Supports filtering by season, user, and award type.
    Results are paginated.
    """
    awards = award_service.get_awards(
        db=db,
        season_id=season_id,
        user_id=user_id,
        award_type=award_type,
        skip=skip,
        limit=limit,
    )

    return [
        AwardResponse(
            id=award.id,
            season_id=award.season_id,
            period_type=award.period_type,
            period_start=award.period_start,
            award_type=award.award_type,
            user_id=award.user_id,
            user_display_name=award.user.display_name,
            user_email=award.user.email,
            score=award.score,
            metadata_json=award.metadata_json,
            created_at=award.created_at.date(),
        )
        for award in awards
    ]


@router.get("/plays-of-day", response_model=List[PlayOfTheDayResponse])
def list_plays_of_day(
    season_id: Optional[str] = Query(None, description="Filter by season"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=100, description="Pagination limit"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List Play of the Day highlights.

    Supports filtering by season.
    Results are paginated and ordered by date (newest first).
    """
    plays = award_service.get_plays_of_day(
        db=db,
        season_id=season_id,
        skip=skip,
        limit=limit,
    )

    return [
        PlayOfTheDayResponse(
            id=play.id,
            season_id=play.season_id,
            date=play.date,
            commit_sha=play.commit_sha,
            user_id=play.user_id,
            user_display_name=play.user.display_name,
            user_email=play.user.email,
            score=play.score,
            metadata_json=play.metadata_json,
            created_at=play.created_at.date(),
        )
        for play in plays
    ]
