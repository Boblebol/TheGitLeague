"""Celery tasks for repository synchronization."""

import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.db.session import get_db_context
from app.models.commit import Commit
from app.models.project import Repository, RepoStatus
from app.models.user import MagicLinkToken
from app.utils.git import (
    clone_or_fetch_repo,
    extract_commit_metadata,
    get_commits_since_sha,
    get_latest_commit_sha,
    get_repo_path,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def sync_repo_task(self, repo_id: str) -> dict:
    """
    Sync a repository: fetch commits and store metadata.

    Args:
        self: Celery task instance (for retry)
        repo_id: Repository ID to sync

    Returns:
        Dictionary with sync results
    """
    with get_db_context() as db:
        # Get repository
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            logger.error(f"Repository {repo_id} not found")
            return {"success": False, "error": "Repository not found"}

        logger.info(f"Starting sync for repository: {repo.name} ({repo_id})")

        # Update status to syncing
        repo.status = RepoStatus.SYNCING
        repo.error_message = None
        db.commit()

        try:
            # Get bare repository path
            bare_path = get_repo_path(repo_id)

            # Clone or fetch repository
            git_repo = clone_or_fetch_repo(
                repo.remote_url or bare_path,
                bare_path,
                repo.credentials_encrypted,
            )

            # Get commits since last sync
            commits = get_commits_since_sha(
                git_repo,
                repo.branch,
                repo.last_ingested_sha,
            )

            logger.info(f"Found {len(commits)} new commits for {repo.name}")

            # Extract and store commits in batches
            batch_size = 1000
            batch = []
            total_inserted = 0

            for git_commit in reversed(commits):  # Process oldest first
                metadata = extract_commit_metadata(git_commit)
                batch.append(metadata)

                if len(batch) >= batch_size:
                    inserted = bulk_insert_commits(batch, repo_id, db)
                    total_inserted += inserted
                    logger.info(f"Inserted batch of {inserted} commits for {repo.name}")
                    batch = []

            # Insert remaining commits
            if batch:
                inserted = bulk_insert_commits(batch, repo_id, db)
                total_inserted += inserted
                logger.info(f"Inserted final batch of {inserted} commits for {repo.name}")

            # Update repository status
            repo.status = RepoStatus.HEALTHY
            repo.last_sync_at = datetime.utcnow()
            repo.last_ingested_sha = get_latest_commit_sha(git_repo, repo.branch)
            db.commit()

            logger.info(f"Sync completed for {repo.name}: {total_inserted} commits inserted")

            return {
                "success": True,
                "repo_id": repo_id,
                "commits_inserted": total_inserted,
                "last_sha": repo.last_ingested_sha,
            }

        except Exception as e:
            logger.error(f"Error syncing repository {repo.name}: {str(e)}", exc_info=True)

            # Update repo status
            repo.status = RepoStatus.ERROR
            repo.error_message = str(e)[:1000]  # Cap error message
            db.commit()

            # Retry with exponential backoff
            retry_countdown = 2 ** self.request.retries
            raise self.retry(exc=e, countdown=retry_countdown)


def bulk_insert_commits(commits_data: List[dict], repo_id: str, db: Session) -> int:
    """
    Insert commits in bulk with idempotent handling (ON CONFLICT DO NOTHING).

    Args:
        commits_data: List of commit metadata dictionaries
        repo_id: Repository ID
        db: Database session

    Returns:
        Number of commits inserted
    """
    if not commits_data:
        return 0

    inserted = 0

    for commit_data in commits_data:
        # Check if commit already exists (by SHA)
        existing = db.query(Commit).filter(Commit.sha == commit_data["sha"]).first()

        if not existing:
            # Create new commit
            commit = Commit(
                repo_id=repo_id,
                **commit_data,
            )
            db.add(commit)
            inserted += 1

    # Commit all inserts
    db.commit()

    return inserted


@celery_app.task
def cleanup_old_magic_links() -> dict:
    """
    Clean up expired magic link tokens.

    This task runs periodically to remove old tokens from the database.

    Returns:
        Dictionary with cleanup results
    """
    with get_db_context() as db:
        # Delete magic link tokens that expired more than 24 hours ago
        cutoff = datetime.utcnow() - timedelta(hours=24)

        deleted = (
            db.query(MagicLinkToken)
            .filter(MagicLinkToken.expires_at < cutoff)
            .delete()
        )

        db.commit()

        logger.info(f"Cleaned up {deleted} expired magic link tokens")

        return {"success": True, "deleted": deleted}


from datetime import timedelta
