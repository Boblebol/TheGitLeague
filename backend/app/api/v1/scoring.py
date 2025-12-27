"""Scoring API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_commissioner
from app.models.user import User
from app.schemas.scoring import (
    ProjectConfigResponse,
    ProjectConfigUpdate,
    CommitMetricsBreakdown,
    ScoringCoefficientsSchema,
)
from app.services.scoring import scoring_service
import json


router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.get("/projects/{project_id}/config", response_model=ProjectConfigResponse)
def get_project_config(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get scoring configuration for a project.

    Creates default config if it doesn't exist.
    Accessible by all authenticated users.
    """
    config = scoring_service.get_or_create_project_config(project_id, db)
    
    # Parse JSON string to dict for response
    coeffs_dict = json.loads(config.scoring_coefficients)
    coeffs_schema = ScoringCoefficientsSchema(**coeffs_dict)
    
    return ProjectConfigResponse(
        project_id=config.project_id,
        scoring_coefficients=coeffs_schema,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.put("/projects/{project_id}/config", response_model=ProjectConfigResponse)
def update_project_config(
    project_id: str,
    config_update: ProjectConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """
    Update scoring configuration for a project.

    Only accessible by Commissioners.
    """
    config = scoring_service.update_project_config(
        project_id,
        config_update,
        db,
        current_user,
    )
    
    # Parse JSON string to dict for response
    coeffs_dict = json.loads(config.scoring_coefficients)
    coeffs_schema = ScoringCoefficientsSchema(**coeffs_dict)
    
    return ProjectConfigResponse(
        project_id=config.project_id,
        scoring_coefficients=coeffs_schema,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/commits/{commit_id}/metrics", response_model=CommitMetricsBreakdown)
def get_commit_metrics(
    commit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate and return NBA metrics for a specific commit.

    Includes detailed breakdown of how each metric was calculated.
    Accessible by all authenticated users.
    """
    metrics = scoring_service.calculate_commit_metrics(commit_id, db)
    return CommitMetricsBreakdown(**metrics)
