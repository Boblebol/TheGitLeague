"""Season service."""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.season import Season, Absence, SeasonStatus
from app.models.project import Project
from app.models.user import User, AuditLog
from app.schemas.season import SeasonCreate, SeasonUpdate, AbsenceCreate, AbsenceUpdate


class SeasonService:
    """Service for season operations."""

    def get_seasons(
        self,
        project_id: str,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[SeasonStatus] = None,
    ) -> Tuple[List[Season], int]:
        """Get list of seasons for a project."""
        query = db.query(Season).filter(Season.project_id == project_id)

        if status_filter:
            query = query.filter(Season.status == status_filter)

        total = query.count()
        seasons = query.order_by(Season.start_at.desc()).offset(skip).limit(limit).all()

        return seasons, total

    def get_season_by_id(
        self,
        season_id: str,
        db: Session,
    ) -> Optional[Season]:
        """Get season by ID."""
        return db.query(Season).filter(Season.id == season_id).first()

    def create_season(
        self,
        project_id: str,
        season_data: SeasonCreate,
        db: Session,
        current_user: User,
    ) -> Season:
        """Create a new season."""
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Check if season name already exists in this project
        existing = (
            db.query(Season)
            .filter(
                Season.project_id == project_id,
                Season.name == season_data.name,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Season with name '{season_data.name}' already exists in this project",
            )

        # Create season
        season = Season(
            project_id=project_id,
            name=season_data.name,
            start_at=season_data.start_at,
            end_at=season_data.end_at,
            status=SeasonStatus.DRAFT,
        )

        db.add(season)
        db.commit()
        db.refresh(season)

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="create_season",
            resource_type="season",
            resource_id=season.id,
            details=f"Created season {season.name}",
        )
        db.add(audit)
        db.commit()

        return season

    def update_season(
        self,
        season_id: str,
        season_update: SeasonUpdate,
        db: Session,
        current_user: User,
    ) -> Season:
        """Update a season."""
        season = self.get_season_by_id(season_id, db)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )

        # Update fields
        update_data = season_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(season, field, value)

        db.commit()
        db.refresh(season)

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="update_season",
            resource_type="season",
            resource_id=season_id,
            details=f"Updated season {season.name}",
        )
        db.add(audit)
        db.commit()

        return season

    def delete_season(
        self,
        season_id: str,
        db: Session,
        current_user: User,
    ) -> None:
        """Delete a season."""
        season = self.get_season_by_id(season_id, db)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )

        season_name = season.name

        # Create audit log before deletion
        audit = AuditLog(
            user_id=current_user.id,
            action="delete_season",
            resource_type="season",
            resource_id=season_id,
            details=f"Deleted season {season_name}",
        )
        db.add(audit)

        # Delete season
        db.delete(season)
        db.commit()

    def activate_season(
        self,
        season_id: str,
        db: Session,
        current_user: User,
    ) -> Season:
        """Activate a season (deactivates other active seasons in the project)."""
        season = self.get_season_by_id(season_id, db)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )

        # Deactivate other active seasons in this project
        db.query(Season).filter(
            Season.project_id == season.project_id,
            Season.status == SeasonStatus.ACTIVE,
            Season.id != season_id,
        ).update({"status": SeasonStatus.CLOSED})

        # Activate this season
        season.status = SeasonStatus.ACTIVE
        db.commit()
        db.refresh(season)

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="activate_season",
            resource_type="season",
            resource_id=season_id,
            details=f"Activated season {season.name}",
        )
        db.add(audit)
        db.commit()

        return season

    # Absence methods

    def get_absences(
        self,
        season_id: str,
        db: Session,
        user_id: Optional[str] = None,
    ) -> List[Absence]:
        """Get absences for a season, optionally filtered by user."""
        query = db.query(Absence).filter(Absence.season_id == season_id)

        if user_id:
            query = query.filter(Absence.user_id == user_id)

        return query.order_by(Absence.start_at).all()

    def create_absence(
        self,
        absence_data: AbsenceCreate,
        db: Session,
        current_user: User,
    ) -> Absence:
        """Create a new absence."""
        # Verify season exists
        season = self.get_season_by_id(absence_data.season_id, db)
        if not season:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Season not found",
            )

        # Verify user exists
        user = db.query(User).filter(User.id == absence_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Create absence
        absence = Absence(
            user_id=absence_data.user_id,
            season_id=absence_data.season_id,
            start_at=absence_data.start_at,
            end_at=absence_data.end_at,
            reason=absence_data.reason,
        )

        db.add(absence)
        db.commit()
        db.refresh(absence)

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="create_absence",
            resource_type="absence",
            resource_id=absence.id,
            details=f"Created absence for user {user.email} from {absence.start_at} to {absence.end_at}",
        )
        db.add(audit)
        db.commit()

        return absence

    def delete_absence(
        self,
        absence_id: str,
        db: Session,
        current_user: User,
    ) -> None:
        """Delete an absence."""
        absence = db.query(Absence).filter(Absence.id == absence_id).first()
        if not absence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Absence not found",
            )

        # Create audit log before deletion
        audit = AuditLog(
            user_id=current_user.id,
            action="delete_absence",
            resource_type="absence",
            resource_id=absence_id,
            details=f"Deleted absence for user {absence.user_id}",
        )
        db.add(audit)

        # Delete absence
        db.delete(absence)
        db.commit()


# Singleton instance
season_service = SeasonService()
