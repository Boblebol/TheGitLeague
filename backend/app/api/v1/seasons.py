"""Seasons API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_commissioner
from app.models.user import User
from app.models.season import SeasonStatus
from app.schemas.season import (
    SeasonCreate,
    SeasonUpdate,
    SeasonResponse,
    SeasonActivateRequest,
    AbsenceCreate,
    AbsenceResponse,
)
from app.services.season import season_service


router = APIRouter(prefix="/seasons", tags=["seasons"])


@router.get("/projects/{project_id}/seasons", response_model=List[SeasonResponse])
def list_project_seasons(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[SeasonStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all seasons for a project."""
    seasons, total = season_service.get_seasons(
        project_id, db, skip=skip, limit=limit, status_filter=status_filter
    )
    return [SeasonResponse.model_validate(s) for s in seasons]


@router.post("/projects/{project_id}/seasons", response_model=SeasonResponse, status_code=status.HTTP_201_CREATED)
def create_season(
    project_id: str,
    season_data: SeasonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """Create a new season (Commissioner only)."""
    season = season_service.create_season(project_id, season_data, db, current_user)
    return SeasonResponse.model_validate(season)


@router.get("/{season_id}", response_model=SeasonResponse)
def get_season(
    season_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get season by ID."""
    from fastapi import HTTPException

    season = season_service.get_season_by_id(season_id, db)
    if not season:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found",
        )

    return SeasonResponse.model_validate(season)


@router.patch("/{season_id}", response_model=SeasonResponse)
def update_season(
    season_id: str,
    season_update: SeasonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """Update a season (Commissioner only)."""
    season = season_service.update_season(season_id, season_update, db, current_user)
    return SeasonResponse.model_validate(season)


@router.delete("/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_season(
    season_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """Delete a season (Commissioner only)."""
    season_service.delete_season(season_id, db, current_user)
    return None


@router.post("/{season_id}/activate", response_model=SeasonResponse)
def activate_season(
    season_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """Activate a season (Commissioner only). Deactivates other active seasons in the project."""
    season = season_service.activate_season(season_id, db, current_user)
    return SeasonResponse.model_validate(season)


# Absence endpoints


@router.get("/{season_id}/absences", response_model=List[AbsenceResponse])
def list_season_absences(
    season_id: str,
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List absences for a season, optionally filtered by user."""
    absences = season_service.get_absences(season_id, db, user_id=user_id)
    return [AbsenceResponse.model_validate(a) for a in absences]


@router.post("/absences", response_model=AbsenceResponse, status_code=status.HTTP_201_CREATED)
def create_absence(
    absence_data: AbsenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """Create a new absence (Commissioner only)."""
    absence = season_service.create_absence(absence_data, db, current_user)
    return AbsenceResponse.model_validate(absence)


@router.delete("/absences/{absence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_absence(
    absence_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """Delete an absence (Commissioner only)."""
    season_service.delete_absence(absence_id, db, current_user)
    return None
