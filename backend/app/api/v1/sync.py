"""Push-based Git synchronization endpoints."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_hybrid
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.sync import (
    SyncCommitsRequest,
    SyncCommitsResponse,
    CommitInsertResult,
    SyncStatusResponse,
)
from app.services.sync import sync_service


router = APIRouter(prefix="/sync", tags=["sync"])


@router.post(
    "/projects/{project_id}/repos/{repo_id}/commits",
    response_model=SyncCommitsResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("100/minute")
def sync_commits(
    request: Request,
    project_id: str,
    repo_id: str,
    request_data: SyncCommitsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_hybrid),
):
    """
    Push commits to a repository.

    This endpoint accepts a batch of commits from an external client and inserts them
    into the repository. Commits are deduplicated by SHA - if a commit already exists,
    it will be skipped.

    **Authentication**: Supports both JWT tokens and API keys via Bearer token.

    **Rate Limiting**: 100 requests per minute per IP address.

    **Request**:
    - `project_id`: UUID of the project
    - `repo_id`: UUID of the repository (must be configured with sync_method=push_client)
    - `commits`: List of commits (1-1000), with SHA, author, message, stats, etc.
    - `client_version`: Optional client version for tracking
    - `timestamp`: Optional client timestamp

    **Response**:
    - `total`: Total commits in request
    - `inserted`: Commits successfully inserted
    - `skipped`: Commits already in database (deduplicated)
    - `errors`: Commits with errors
    - `last_ingested_sha`: SHA of the latest ingested commit
    - `details`: Per-commit status

    **Errors**:
    - 401 Unauthorized: Invalid or missing credentials
    - 404 Not Found: Project or repository not found
    - 400 Bad Request: Repository not configured for push-based sync
    - 422 Unprocessable Entity: Invalid commit data

    **Examples**:
    ```bash
    curl -X POST https://api.thegitleague.com/api/v1/sync/projects/{project_id}/repos/{repo_id}/commits \\
      -H "Authorization: Bearer tgl_xxx_secret" \\
      -H "Content-Type: application/json" \\
      -d '{
        "commits": [
          {
            "sha": "abc123def456...",
            "author_name": "Alice",
            "author_email": "alice@example.com",
            ...
          }
        ]
      }'
    ```
    """
    # Validate repository and ensure it's configured for push-based sync
    repo = sync_service.validate_repo_for_sync(project_id, repo_id, current_user, db)

    # Ingest commits
    inserted, skipped, errors, last_ingested_sha, details = sync_service.ingest_commits(
        repo=repo,
        commits_data=request_data.commits,
        user=current_user,
        db=db,
    )

    return SyncCommitsResponse(
        total=len(request_data.commits),
        inserted=inserted,
        skipped=skipped,
        errors=errors,
        last_ingested_sha=last_ingested_sha,
        details=details,
    )


@router.get(
    "/projects/{project_id}/repos/{repo_id}/status",
    response_model=SyncStatusResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("100/minute")
def get_sync_status(
    request: Request,
    project_id: str,
    repo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_hybrid),
):
    """
    Get synchronization status for a repository.

    Returns current sync status, last sync time, and number of commits in the repository.

    **Authentication**: Supports both JWT tokens and API keys via Bearer token.

    **Rate Limiting**: 100 requests per minute per IP address.

    **Response**:
    - `repo_id`: Repository ID
    - `status`: Current status (pending, syncing, healthy, error)
    - `last_sync_at`: Timestamp of last successful sync
    - `last_ingested_sha`: SHA of the latest commit in the repository
    - `total_commits`: Total number of commits in the repository
    - `error_message`: Error message if status is "error"

    **Errors**:
    - 401 Unauthorized: Invalid or missing credentials
    - 404 Not Found: Project or repository not found
    """
    status_info = sync_service.get_sync_status(project_id, repo_id, current_user, db)

    return SyncStatusResponse(**status_info)
