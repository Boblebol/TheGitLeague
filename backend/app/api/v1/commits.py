"""Commits API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.commit import Commit
from app.models.project import Repository
from app.models.user import User
from app.schemas.commit import CommitListResponse, CommitResponse, CommitStatsResponse


router = APIRouter(prefix="/commits", tags=["commits"])


@router.get("/repos/{repo_id}/commits", response_model=CommitListResponse)
def list_repo_commits(
    repo_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    author_email: Optional[str] = Query(None, description="Filter by author email"),
    since: Optional[datetime] = Query(None, description="Filter commits after date"),
    until: Optional[datetime] = Query(None, description="Filter commits before date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List commits for a repository.

    Accessible by all authenticated users.
    """
    # Build query
    query = db.query(Commit).filter(Commit.repo_id == repo_id)

    if author_email:
        query = query.filter(Commit.author_email == author_email.lower())

    if since:
        query = query.filter(Commit.commit_date >= since)

    if until:
        query = query.filter(Commit.commit_date <= until)

    # Get total count
    total = query.count()

    # Paginate
    skip = (page - 1) * per_page
    commits = (
        query.order_by(Commit.commit_date.desc())
        .offset(skip)
        .limit(per_page)
        .all()
    )

    # Calculate total pages
    pages = (total + per_page - 1) // per_page

    return CommitListResponse(
        items=[CommitResponse.model_validate(c) for c in commits],
        total=total,
        page=page,
        pages=pages,
        per_page=per_page,
    )


@router.get("/repos/{repo_id}/commits/stats", response_model=CommitStatsResponse)
def get_repo_commit_stats(
    repo_id: str,
    author_email: Optional[str] = Query(None, description="Filter by author email"),
    since: Optional[datetime] = Query(None, description="Filter commits after date"),
    until: Optional[datetime] = Query(None, description="Filter commits before date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get commit statistics for a repository.

    Accessible by all authenticated users.
    """
    # Build query
    query = db.query(Commit).filter(Commit.repo_id == repo_id)

    if author_email:
        query = query.filter(Commit.author_email == author_email.lower())

    if since:
        query = query.filter(Commit.commit_date >= since)

    if until:
        query = query.filter(Commit.commit_date <= until)

    # Aggregate stats
    stats = query.with_entities(
        func.count(Commit.id).label("total_commits"),
        func.sum(Commit.additions).label("total_additions"),
        func.sum(Commit.deletions).label("total_deletions"),
        func.sum(Commit.files_changed).label("total_files_changed"),
        func.sum(func.cast(Commit.is_merge, db.Integer)).label("merge_commits"),
        func.count(func.distinct(Commit.author_email)).label("unique_authors"),
        func.min(Commit.commit_date).label("earliest_commit"),
        func.max(Commit.commit_date).label("latest_commit"),
    ).first()

    return CommitStatsResponse(
        total_commits=stats.total_commits or 0,
        total_additions=stats.total_additions or 0,
        total_deletions=stats.total_deletions or 0,
        total_files_changed=stats.total_files_changed or 0,
        merge_commits=stats.merge_commits or 0,
        unique_authors=stats.unique_authors or 0,
        date_range={
            "earliest": stats.earliest_commit,
            "latest": stats.latest_commit,
        },
    )


@router.get("/commits/{commit_id}", response_model=CommitResponse)
def get_commit(
    commit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get commit by ID.

    Accessible by all authenticated users.
    """
    from fastapi import HTTPException

    commit = db.query(Commit).filter(Commit.id == commit_id).first()
    if not commit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commit not found",
        )

    return CommitResponse.model_validate(commit)


@router.get("/commits/sha/{sha}", response_model=CommitResponse)
def get_commit_by_sha(
    sha: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get commit by SHA.

    Accessible by all authenticated users.
    """
    from fastapi import HTTPException

    commit = db.query(Commit).filter(Commit.sha == sha).first()
    if not commit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commit not found",
        )

    return CommitResponse.model_validate(commit)
