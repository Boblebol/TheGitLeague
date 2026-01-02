"""Project service."""

from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project import Project, Repository
from app.models.user import User, AuditLog
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service for project operations."""

    def get_projects(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        created_by: Optional[str] = None,
    ) -> Tuple[List[Project], int]:
        """
        Get list of projects with optional filters.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            created_by: Optional filter by creator user ID

        Returns:
            Tuple of (projects list, total count)
        """
        query = db.query(Project)

        if created_by:
            query = query.filter(Project.created_by == created_by)

        total = query.count()

        # Join with repos to get count
        projects = (
            query
            .outerjoin(Repository)
            .group_by(Project.id)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return projects, total

    def get_project_by_id(
        self,
        project_id: str,
        db: Session,
    ) -> Optional[Project]:
        """
        Get project by ID.

        Args:
            project_id: Project ID
            db: Database session

        Returns:
            Project or None if not found
        """
        return db.query(Project).filter(Project.id == project_id).first()

    def get_project_by_slug(
        self,
        slug: str,
        db: Session,
    ) -> Optional[Project]:
        """
        Get project by slug.

        Args:
            slug: Project slug
            db: Database session

        Returns:
            Project or None if not found
        """
        return db.query(Project).filter(Project.slug == slug).first()

    def create_project(
        self,
        project_data: ProjectCreate,
        db: Session,
        current_user: User,
    ) -> Project:
        """
        Create a new project.

        Args:
            project_data: Project creation data
            db: Database session
            current_user: Current authenticated user

        Returns:
            Created project

        Raises:
            HTTPException: If slug already exists
        """
        # Check if slug already exists
        existing = self.get_project_by_slug(project_data.slug, db)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project with slug '{project_data.slug}' already exists",
            )

        # Create project
        project = Project(
            name=project_data.name,
            slug=project_data.slug,
            description=project_data.description,
            created_by=current_user.id,
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="create_project",
            resource_type="project",
            resource_id=project.id,
            details=f"Created project {project.name} ({project.slug})",
        )
        db.add(audit)
        db.commit()

        return project

    def update_project(
        self,
        project_id: str,
        project_update: ProjectUpdate,
        db: Session,
        current_user: User,
    ) -> Project:
        """
        Update a project.

        Args:
            project_id: Project ID to update
            project_update: Update data
            db: Database session
            current_user: Current authenticated user (for audit)

        Returns:
            Updated project

        Raises:
            HTTPException: If project not found
        """
        project = self.get_project_by_id(project_id, db)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Update fields
        update_data = project_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        db.commit()
        db.refresh(project)

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="update_project",
            resource_type="project",
            resource_id=project_id,
            details=f"Updated project {project.name}",
        )
        db.add(audit)
        db.commit()

        return project

    def delete_project(
        self,
        project_id: str,
        db: Session,
        current_user: User,
    ) -> None:
        """
        Delete a project and all its repositories (cascade).

        Args:
            project_id: Project ID to delete
            db: Database session
            current_user: Current authenticated user (for audit)

        Raises:
            HTTPException: If project not found
        """
        project = self.get_project_by_id(project_id, db)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        project_name = project.name

        # Create audit log before deletion
        audit = AuditLog(
            user_id=current_user.id,
            action="delete_project",
            resource_type="project",
            resource_id=project_id,
            details=f"Deleted project {project_name}",
        )
        db.add(audit)

        # Delete project (cascades to repos)
        db.delete(project)
        db.commit()

    def get_repos_count(
        self,
        project_id: str,
        db: Session,
    ) -> int:
        """
        Get count of repositories in a project.

        Args:
            project_id: Project ID
            db: Database session

        Returns:
            Number of repositories
        """
        return db.query(func.count(Repository.id)).filter(
            Repository.project_id == project_id
        ).scalar() or 0


# Singleton instance
project_service = ProjectService()
