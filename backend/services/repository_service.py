"""
Repository service for secure credential management.

Handles:
- Creating repositories with encrypted PAT tokens
- Updating repository credentials
- Decrypting credentials for Git sync (workers only)
- Audit logging of all credential access
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.encryption import EncryptionService, mask_token
from backend.models import Repository, AuditLog, AuditEventType, AccessType, RepoStatus
from backend.models.user import User

logger = logging.getLogger(__name__)


class RepositoryService:
    """Service for managing repositories with secure credential handling."""

    def __init__(self, db: Session):
        """
        Initialize repository service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.encryption_service = EncryptionService(
            master_key=settings.ENCRYPTION_MASTER_KEY,
            key_version=settings.ENCRYPTION_KEY_VERSION
        )

    def create_repository(
        self,
        project_id: int,
        name: str,
        remote_url: str,
        access_type: AccessType,
        branch: str = "main",
        pat_token: Optional[str] = None,
        pat_username: str = "git",
        user: Optional[User] = None,
        ip_address: Optional[str] = None,
    ) -> Repository:
        """
        Create a new repository with encrypted credentials.

        Args:
            project_id: ID of parent project
            name: Repository name
            remote_url: Git remote URL (without credentials)
            access_type: Access method (https_pat, ssh, local_bare)
            branch: Branch to track (default: main)
            pat_token: Personal Access Token (if access_type=https_pat)
            pat_username: Username for HTTPS auth (default: git)
            user: User creating the repo (for audit)
            ip_address: Client IP (for audit)

        Returns:
            Created Repository instance

        Raises:
            ValueError: If PAT is required but not provided
        """
        # Validate credentials
        if access_type == AccessType.HTTPS_PAT and not pat_token:
            raise ValueError("PAT token is required for HTTPS access")

        # Create repository instance
        repo = Repository(
            project_id=project_id,
            name=name,
            remote_url=remote_url,
            access_type=access_type,
            branch=branch,
            status=RepoStatus.PENDING,
        )

        # Encrypt credentials if provided
        if pat_token and access_type == AccessType.HTTPS_PAT:
            encrypted_creds = self.encryption_service.encrypt_pat_token(
                token=pat_token,
                username=pat_username
            )
            repo.encrypted_credentials = encrypted_creds
            repo.encryption_key_id = settings.ENCRYPTION_KEY_VERSION

            logger.info(
                f"Encrypted PAT for repository {name} (token: {mask_token(pat_token)})"
            )

        # Save to database
        self.db.add(repo)
        self.db.commit()
        self.db.refresh(repo)

        # Audit log
        audit_log = AuditLog.create_event(
            event_type=AuditEventType.REPO_CREATED,
            user_id=user.id if user else None,
            resource_type="repo",
            resource_id=repo.id,
            metadata={
                "repo_name": name,
                "project_id": project_id,
                "access_type": access_type.value,
                "has_credentials": repo.has_credentials,
            },
            ip_address=ip_address,
        )
        self.db.add(audit_log)
        self.db.commit()

        logger.info(f"Repository created: {repo.name} (id={repo.id})")
        return repo

    def update_repository_credentials(
        self,
        repo_id: int,
        pat_token: str,
        pat_username: str = "git",
        user: Optional[User] = None,
        ip_address: Optional[str] = None,
    ) -> Repository:
        """
        Update repository credentials (e.g., rotate PAT token).

        Args:
            repo_id: Repository ID
            pat_token: New PAT token
            pat_username: Username for HTTPS auth
            user: User updating credentials (for audit)
            ip_address: Client IP (for audit)

        Returns:
            Updated Repository instance

        Raises:
            ValueError: If repository not found or doesn't use PAT
        """
        repo = self.db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            raise ValueError(f"Repository {repo_id} not found")

        if repo.access_type != AccessType.HTTPS_PAT:
            raise ValueError(
                f"Cannot update PAT for repository with access_type={repo.access_type.value}"
            )

        # Encrypt new credentials
        encrypted_creds = self.encryption_service.encrypt_pat_token(
            token=pat_token,
            username=pat_username
        )
        repo.encrypted_credentials = encrypted_creds
        repo.encryption_key_id = settings.ENCRYPTION_KEY_VERSION

        # Update repository
        self.db.commit()
        self.db.refresh(repo)

        # Audit log
        audit_log = AuditLog.create_event(
            event_type=AuditEventType.REPO_UPDATED,
            user_id=user.id if user else None,
            resource_type="repo",
            resource_id=repo.id,
            metadata={
                "action": "credentials_updated",
                "repo_name": repo.name,
                "token_masked": mask_token(pat_token),
            },
            ip_address=ip_address,
        )
        self.db.add(audit_log)
        self.db.commit()

        logger.info(f"Repository credentials updated: {repo.name} (id={repo.id})")
        return repo

    def get_decrypted_credentials(
        self,
        repo_id: int,
        user_id: Optional[int] = None,
    ) -> tuple[str, str]:
        """
        Decrypt repository credentials for Git operations.

        ⚠️  SECURITY WARNING:
            - Only call this from workers/background jobs
            - NEVER expose decrypted credentials via API
            - Clear credentials from memory after use (caller's responsibility)
            - All access is audit logged

        Args:
            repo_id: Repository ID
            user_id: User/worker ID requesting access (for audit)

        Returns:
            Tuple of (token, username)

        Raises:
            ValueError: If repository not found or has no credentials
        """
        repo = self.db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            raise ValueError(f"Repository {repo_id} not found")

        if not repo.has_credentials:
            raise ValueError(
                f"Repository {repo.id} ({repo.name}) has no encrypted credentials"
            )

        # Decrypt credentials
        token, username = self.encryption_service.decrypt_pat_token(
            repo.encrypted_credentials
        )

        # Audit log (CRITICAL for security)
        audit_log = AuditLog.create_event(
            event_type=AuditEventType.REPO_CREDENTIALS_ACCESSED,
            user_id=user_id,  # Usually None (worker/system)
            resource_type="repo",
            resource_id=repo.id,
            metadata={
                "repo_name": repo.name,
                "access_type": repo.access_type.value,
                "action": "credentials_decrypted_for_sync",
                # NEVER log the actual token
                "token_masked": mask_token(token),
            },
        )
        self.db.add(audit_log)
        self.db.commit()

        logger.warning(
            f"Credentials decrypted for repo {repo.name} (id={repo.id}). "
            f"Ensure token is cleared from memory after use!"
        )

        return token, username

    def delete_repository(
        self,
        repo_id: int,
        user: Optional[User] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Delete a repository (and its encrypted credentials).

        Args:
            repo_id: Repository ID
            user: User deleting the repo (for audit)
            ip_address: Client IP (for audit)

        Raises:
            ValueError: If repository not found
        """
        repo = self.db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            raise ValueError(f"Repository {repo_id} not found")

        repo_name = repo.name
        repo_project_id = repo.project_id

        # Audit log BEFORE deletion
        audit_log = AuditLog.create_event(
            event_type=AuditEventType.REPO_DELETED,
            user_id=user.id if user else None,
            resource_type="repo",
            resource_id=repo.id,
            metadata={
                "repo_name": repo_name,
                "project_id": repo_project_id,
                "had_credentials": repo.has_credentials,
            },
            ip_address=ip_address,
        )
        self.db.add(audit_log)

        # Delete repository (cascade will handle related records)
        self.db.delete(repo)
        self.db.commit()

        logger.info(f"Repository deleted: {repo_name} (id={repo_id})")

    def list_repositories(
        self,
        project_id: Optional[int] = None,
        status: Optional[RepoStatus] = None,
    ) -> list[Repository]:
        """
        List repositories with optional filters.

        Args:
            project_id: Filter by project (optional)
            status: Filter by status (optional)

        Returns:
            List of Repository instances
        """
        query = self.db.query(Repository)

        if project_id is not None:
            query = query.filter(Repository.project_id == project_id)

        if status is not None:
            query = query.filter(Repository.status == status)

        return query.all()

    def get_repository_safe(self, repo_id: int) -> dict:
        """
        Get repository details WITHOUT exposing credentials (safe for API).

        Args:
            repo_id: Repository ID

        Returns:
            Repository dict (credentials excluded)

        Raises:
            ValueError: If repository not found
        """
        repo = self.db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            raise ValueError(f"Repository {repo_id} not found")

        return repo.to_dict_safe()
