"""Scoring service."""

import json
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project import Project, ProjectConfig
from app.models.commit import Commit
from app.models.user import User, AuditLog
from app.schemas.scoring import (
    ProjectConfigUpdate,
    ScoringCoefficientsSchema,
)
from app.utils.scoring import (
    ScoringCoefficients,
    calculate_all_metrics,
)


class ScoringService:
    """Service for scoring operations."""

    def get_project_config(
        self,
        project_id: str,
        db: Session,
    ) -> Optional[ProjectConfig]:
        """
        Get project configuration.

        Args:
            project_id: Project ID
            db: Database session

        Returns:
            ProjectConfig or None if not found
        """
        return db.query(ProjectConfig).filter(ProjectConfig.project_id == project_id).first()

    def get_or_create_project_config(
        self,
        project_id: str,
        db: Session,
    ) -> ProjectConfig:
        """
        Get or create project configuration with default values.

        Args:
            project_id: Project ID
            db: Database session

        Returns:
            ProjectConfig

        Raises:
            HTTPException: If project not found
        """
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Get or create config
        config = self.get_project_config(project_id, db)
        if not config:
            # Create with default coefficients
            default_coeffs = ScoringCoefficients()
            config = ProjectConfig(
                project_id=project_id,
                scoring_coefficients=json.dumps(default_coeffs.to_dict()),
            )
            db.add(config)
            db.commit()
            db.refresh(config)

        return config

    def update_project_config(
        self,
        project_id: str,
        config_update: ProjectConfigUpdate,
        db: Session,
        current_user: User,
    ) -> ProjectConfig:
        """
        Update project configuration.

        Args:
            project_id: Project ID
            config_update: Update data
            db: Database session
            current_user: Current authenticated user (for audit)

        Returns:
            Updated ProjectConfig

        Raises:
            HTTPException: If project not found
        """
        # Get or create config
        config = self.get_or_create_project_config(project_id, db)

        # Update coefficients
        coeffs_dict = config_update.scoring_coefficients.model_dump()
        config.scoring_coefficients = json.dumps(coeffs_dict)

        db.commit()
        db.refresh(config)

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="update_project_config",
            resource_type="project_config",
            resource_id=project_id,
            details=f"Updated scoring coefficients for project {project_id}",
        )
        db.add(audit)
        db.commit()

        return config

    def get_scoring_coefficients(
        self,
        project_id: str,
        db: Session,
    ) -> ScoringCoefficients:
        """
        Get scoring coefficients for a project.

        Args:
            project_id: Project ID
            db: Database session

        Returns:
            ScoringCoefficients
        """
        config = self.get_or_create_project_config(project_id, db)
        return ScoringCoefficients.from_json(config.scoring_coefficients)

    def calculate_commit_metrics(
        self,
        commit_id: str,
        db: Session,
    ) -> dict:
        """
        Calculate NBA metrics for a specific commit.

        Args:
            commit_id: Commit ID
            db: Database session

        Returns:
            Dictionary with metrics

        Raises:
            HTTPException: If commit not found
        """
        # Get commit
        commit = db.query(Commit).filter(Commit.id == commit_id).first()
        if not commit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commit not found",
            )

        # Get project ID through repository
        project_id = commit.repository.project_id

        # Get coefficients
        coeffs = self.get_scoring_coefficients(project_id, db)

        # Calculate metrics
        metrics = calculate_all_metrics(commit, coeffs)

        # Add breakdown explanation
        breakdown = {
            "pts": f"Base ({coeffs.commit_base}) + min({commit.additions}, {coeffs.max_additions_cap}) × {coeffs.additions_weight} = {metrics['pts']}",
            "reb": f"min({commit.deletions}, {coeffs.max_deletions_cap}) × {coeffs.deletions_weight} = {metrics['reb']}",
            "ast": f"{'Multi-file bonus' if commit.files_changed > 3 else 'No bonus'} = {metrics['ast']}",
            "blk": f"{'Fix commit bonus' if metrics['blk'] > 0 else 'No bonus'} = {metrics['blk']}",
            "tov": f"{'WIP commit penalty' if metrics['tov'] < 0 else 'No penalty'} = {metrics['tov']}",
            "impact_score": f"PTS×1.0 + REB×0.6 + AST×0.8 + BLK×1.2 + TOV×0.7 = {metrics['impact_score']:.2f}",
        }

        return {
            "commit_id": commit.id,
            "commit_sha": commit.sha,
            "author_email": commit.author_email,
            "commit_date": commit.commit_date,
            "message_title": commit.message_title,
            "additions": commit.additions,
            "deletions": commit.deletions,
            "files_changed": commit.files_changed,
            "is_merge": commit.is_merge,
            **metrics,
            "breakdown": breakdown,
        }


# Singleton instance
scoring_service = ScoringService()
