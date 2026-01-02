"""Service for push-based Git synchronization."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.commit import Commit
from app.models.project import Repository, RepoStatus, SyncMethod, Project
from app.models.user import User, AuditLog
from app.schemas.sync import CommitMetadata, CommitInsertResult


class SyncService:
    """Service for commit synchronization."""

    def validate_repo_for_sync(
        self, project_id: str, repo_id: str, user: User, db: Session
    ) -> Repository:
        """
        Validate that a repository exists and is configured for push-based sync.

        Args:
            project_id: Project ID
            repo_id: Repository ID
            user: User performing the sync
            db: Database session

        Returns:
            Repository object if valid

        Raises:
            HTTPException: If repo not found, not owned by user, or not configured for push
        """
        # Get project and verify user owns it
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.created_by == user.id,
        ).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Get repository and verify it belongs to the project
        repo = db.query(Repository).filter(
            Repository.id == repo_id,
            Repository.project_id == project_id,
        ).first()

        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found",
            )

        # Verify repo is configured for push-client sync
        if repo.sync_method != SyncMethod.PUSH_CLIENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Repository is not configured for push-based sync (current method: {repo.sync_method})",
            )

        return repo

    def ingest_commits(
        self,
        repo: Repository,
        commits_data: List[CommitMetadata],
        user: User,
        db: Session,
    ) -> Tuple[int, int, int, Optional[str], List[CommitInsertResult]]:
        """
        Ingest commits into a repository.

        Args:
            repo: Repository to ingest commits into
            commits_data: List of commit metadata
            user: User performing the sync
            db: Database session

        Returns:
            Tuple of (inserted_count, skipped_count, error_count, last_ingested_sha, details)
        """
        inserted = 0
        skipped = 0
        errors = 0
        last_ingested_sha: Optional[str] = None
        details: List[CommitInsertResult] = []

        # Update repo status to SYNCING
        repo.status = RepoStatus.SYNCING
        db.commit()

        try:
            for commit_data in commits_data:
                try:
                    # Check if commit already exists (by SHA)
                    existing = db.query(Commit).filter(
                        Commit.sha == commit_data.sha,
                    ).first()

                    if existing:
                        skipped += 1
                        details.append(
                            CommitInsertResult(
                                sha=commit_data.sha,
                                inserted=False,
                                error="Commit already exists",
                            )
                        )
                        continue

                    # Create new commit
                    commit = Commit(
                        sha=commit_data.sha,
                        repo_id=repo.id,
                        author_name=commit_data.author_name,
                        author_email=commit_data.author_email,
                        committer_name=commit_data.committer_name,
                        committer_email=commit_data.committer_email,
                        commit_date=commit_data.commit_date,
                        message_title=commit_data.message_title,
                        message_body=commit_data.message_body,
                        additions=commit_data.additions,
                        deletions=commit_data.deletions,
                        files_changed=commit_data.files_changed,
                        is_merge=commit_data.is_merge,
                        parent_count=commit_data.parent_count,
                        created_at=datetime.now(timezone.utc),
                    )

                    db.add(commit)
                    inserted += 1
                    last_ingested_sha = commit_data.sha
                    details.append(
                        CommitInsertResult(
                            sha=commit_data.sha,
                            inserted=True,
                        )
                    )

                except Exception as e:
                    errors += 1
                    details.append(
                        CommitInsertResult(
                            sha=commit_data.sha,
                            inserted=False,
                            error=str(e),
                        )
                    )

            # Commit all database changes
            db.commit()

            # Update repo metadata
            repo.last_sync_at = datetime.now(timezone.utc)
            if last_ingested_sha:
                repo.last_ingested_sha = last_ingested_sha

            # Set status based on results
            if errors > 0:
                repo.status = RepoStatus.ERROR
                repo.error_message = f"Failed to ingest {errors} commits"
            else:
                repo.status = RepoStatus.HEALTHY
                repo.error_message = None

            db.commit()

            # Audit log
            audit = AuditLog(
                user_id=user.id,
                action="sync_commits",
                resource_type="repository",
                resource_id=repo.id,
                details=f"Synced {len(commits_data)} commits: {inserted} inserted, {skipped} skipped, {errors} errors",
            )
            db.add(audit)
            db.commit()

            return inserted, skipped, errors, last_ingested_sha, details

        except Exception as e:
            # Update repo status to ERROR
            repo.status = RepoStatus.ERROR
            repo.error_message = str(e)
            db.commit()

            # Audit log failure
            audit = AuditLog(
                user_id=user.id,
                action="sync_commits",
                resource_type="repository",
                resource_id=repo.id,
                details=f"Sync failed: {str(e)}",
            )
            db.add(audit)
            db.commit()

            raise

    def get_sync_status(
        self, project_id: str, repo_id: str, user: User, db: Session
    ) -> dict:
        """
        Get sync status for a repository.

        Args:
            project_id: Project ID
            repo_id: Repository ID
            user: User requesting status
            db: Database session

        Returns:
            Sync status dict

        Raises:
            HTTPException: If repo not found or not owned by user
        """
        # Verify project ownership
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.created_by == user.id,
        ).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Get repository
        repo = db.query(Repository).filter(
            Repository.id == repo_id,
            Repository.project_id == project_id,
        ).first()

        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found",
            )

        # Count total commits
        total_commits = db.query(Commit).filter(
            Commit.repo_id == repo.id,
        ).count()

        return {
            "repo_id": repo.id,
            "status": repo.status,
            "last_sync_at": repo.last_sync_at,
            "last_ingested_sha": repo.last_ingested_sha,
            "total_commits": total_commits,
            "error_message": repo.error_message,
        }


# Singleton instance
sync_service = SyncService()
