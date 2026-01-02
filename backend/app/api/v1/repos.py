"""Repositories API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_commissioner
from app.models.user import User
from app.models.project import RepoStatus
from app.schemas.project import (
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryResponse,
    RepositorySyncRequest,
    RepositorySyncResponse,
    RepositoryTestConnectionRequest,
    RepositoryTestConnectionResponse,
)
from app.services.repository import repository_service


router = APIRouter(prefix="/repos", tags=["repositories"])


@router.get("/projects/{project_id}/repos", response_model=List[RepositoryResponse])
def list_project_repos(
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all repositories in a project.

    Accessible by all authenticated users.
    """
    repos, total = repository_service.get_repositories(project_id, db, skip=skip, limit=limit)
    return [RepositoryResponse.model_validate(repo) for repo in repos]


@router.post("/projects/{project_id}/repos", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def create_repository(
    project_id: str,
    repo_data: RepositoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """
    Create a new repository in a project.

    Only accessible by Commissioners.
    """
    repo = repository_service.create_repository(project_id, repo_data, db, current_user)
    return RepositoryResponse.model_validate(repo)


@router.get("/{repo_id}", response_model=RepositoryResponse)
def get_repository(
    repo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get repository by ID.

    Accessible by all authenticated users.
    """
    from fastapi import HTTPException

    repo = repository_service.get_repository_by_id(repo_id, db)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    return RepositoryResponse.model_validate(repo)


@router.patch("/{repo_id}", response_model=RepositoryResponse)
def update_repository(
    repo_id: str,
    repo_update: RepositoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """
    Update a repository.

    Only accessible by Commissioners.
    """
    repo = repository_service.update_repository(repo_id, repo_update, db, current_user)
    return RepositoryResponse.model_validate(repo)


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(
    repo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """
    Delete a repository.

    Only accessible by Commissioners.
    """
    repository_service.delete_repository(repo_id, db, current_user)
    return None


@router.post("/{repo_id}/sync", response_model=RepositorySyncResponse)
def trigger_sync(
    repo_id: str,
    sync_request: RepositorySyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commissioner),
):
    """
    Trigger immediate sync for a repository.

    Only accessible by Commissioners.
    """
    message, task_id = repository_service.trigger_sync(
        repo_id,
        sync_request.force,
        db,
        current_user,
    )

    return RepositorySyncResponse(
        message=message,
        status=RepoStatus.SYNCING,
        task_id=task_id,
    )


@router.post("/test-connection", response_model=RepositoryTestConnectionResponse)
def test_connection(
    test_request: RepositoryTestConnectionRequest,
    current_user: User = Depends(require_commissioner),
):
    """
    Test connection to a Git repository.

    Only accessible by Commissioners.
    Validates credentials and checks if branch exists.
    """
    success, message, branches = repository_service.test_connection(
        test_request.remote_url,
        test_request.remote_type,
        test_request.branch,
        test_request.credentials,
    )

    return RepositoryTestConnectionResponse(
        success=success,
        message=message,
        available_branches=branches,
    )
