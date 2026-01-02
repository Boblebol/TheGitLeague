"""Projects API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_commissioner
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectWithRepos,
    RepositoryResponse,
)
from app.services.project import project_service


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all projects.

    Accessible by all authenticated users.
    """
    projects, total = project_service.get_projects(db, skip=skip, limit=limit)

    # Add repos count to each project
    result = []
    for project in projects:
        project_dict = ProjectResponse.model_validate(project).model_dump()
        project_dict["repos_count"] = project_service.get_repos_count(project.id, db)
        result.append(ProjectResponse(**project_dict))

    return result


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """
    Create a new project.

    Only accessible by Commissioners.
    """
    project = project_service.create_project(project_data, db, current_user)

    # Add repos count
    project_dict = ProjectResponse.model_validate(project).model_dump()
    project_dict["repos_count"] = 0

    return ProjectResponse(**project_dict)


@router.get("/{project_id}", response_model=ProjectWithRepos)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get project by ID with its repositories.

    Accessible by all authenticated users.
    """
    from fastapi import HTTPException

    project = project_service.get_project_by_id(project_id, db)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Convert to response with repos
    return ProjectWithRepos.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """
    Update a project.

    Only accessible by Commissioners.
    """
    project = project_service.update_project(project_id, project_update, db, current_user)

    # Add repos count
    project_dict = ProjectResponse.model_validate(project).model_dump()
    project_dict["repos_count"] = project_service.get_repos_count(project.id, db)

    return ProjectResponse(**project_dict)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """
    Delete a project and all its repositories.

    Only accessible by Commissioners.
    """
    project_service.delete_project(project_id, db, current_user)
    return None
