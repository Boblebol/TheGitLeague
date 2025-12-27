"""Repository service."""

import json
import os
import tempfile
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import git

from app.models.project import Project, Repository, RepoStatus, RemoteType
from app.models.user import User, AuditLog
from app.schemas.project import RepositoryCreate, RepositoryUpdate
from app.core.security import encrypt_credentials, decrypt_credentials


class RepositoryService:
    """Service for repository operations."""

    def get_repositories(
        self,
        project_id: str,
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Repository], int]:
        """
        Get list of repositories for a project.

        Args:
            project_id: Project ID
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (repositories list, total count)
        """
        query = db.query(Repository).filter(Repository.project_id == project_id)

        total = query.count()
        repos = query.order_by(Repository.created_at.desc()).offset(skip).limit(limit).all()

        return repos, total

    def get_repository_by_id(
        self,
        repo_id: str,
        db: Session,
    ) -> Optional[Repository]:
        """
        Get repository by ID.

        Args:
            repo_id: Repository ID
            db: Database session

        Returns:
            Repository or None if not found
        """
        return db.query(Repository).filter(Repository.id == repo_id).first()

    def create_repository(
        self,
        project_id: str,
        repo_data: RepositoryCreate,
        db: Session,
        current_user: User,
    ) -> Repository:
        """
        Create a new repository.

        Args:
            project_id: Project ID
            repo_data: Repository creation data
            db: Database session
            current_user: Current authenticated user

        Returns:
            Created repository

        Raises:
            HTTPException: If project not found or repo name exists
        """
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Check if repo name already exists in this project
        existing = (
            db.query(Repository)
            .filter(
                Repository.project_id == project_id,
                Repository.name == repo_data.name,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Repository with name '{repo_data.name}' already exists in this project",
            )

        # Encrypt credentials if provided
        credentials_encrypted = None
        if repo_data.credentials:
            credentials_encrypted = encrypt_credentials(json.dumps(repo_data.credentials))

        # Create repository
        repo = Repository(
            project_id=project_id,
            name=repo_data.name,
            remote_url=repo_data.remote_url,
            remote_type=repo_data.remote_type,
            branch=repo_data.branch,
            sync_frequency=repo_data.sync_frequency,
            credentials_encrypted=credentials_encrypted,
            status=RepoStatus.PENDING,
        )

        db.add(repo)
        db.commit()
        db.refresh(repo)

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="create_repository",
            resource_type="repository",
            resource_id=repo.id,
            details=f"Created repository {repo.name} in project {project.name}",
        )
        db.add(audit)
        db.commit()

        return repo

    def update_repository(
        self,
        repo_id: str,
        repo_update: RepositoryUpdate,
        db: Session,
        current_user: User,
    ) -> Repository:
        """
        Update a repository.

        Args:
            repo_id: Repository ID
            repo_update: Update data
            db: Database session
            current_user: Current authenticated user

        Returns:
            Updated repository

        Raises:
            HTTPException: If repository not found
        """
        repo = self.get_repository_by_id(repo_id, db)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found",
            )

        # Update fields
        update_data = repo_update.model_dump(exclude_unset=True, exclude={"credentials"})
        for field, value in update_data.items():
            setattr(repo, field, value)

        # Update credentials if provided
        if repo_update.credentials is not None:
            if repo_update.credentials:
                repo.credentials_encrypted = encrypt_credentials(json.dumps(repo_update.credentials))
            else:
                repo.credentials_encrypted = None

        db.commit()
        db.refresh(repo)

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="update_repository",
            resource_type="repository",
            resource_id=repo_id,
            details=f"Updated repository {repo.name}",
        )
        db.add(audit)
        db.commit()

        return repo

    def delete_repository(
        self,
        repo_id: str,
        db: Session,
        current_user: User,
    ) -> None:
        """
        Delete a repository.

        Args:
            repo_id: Repository ID
            db: Database session
            current_user: Current authenticated user

        Raises:
            HTTPException: If repository not found
        """
        repo = self.get_repository_by_id(repo_id, db)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found",
            )

        repo_name = repo.name

        # Create audit log before deletion
        audit = AuditLog(
            user_id=current_user.id,
            action="delete_repository",
            resource_type="repository",
            resource_id=repo_id,
            details=f"Deleted repository {repo_name}",
        )
        db.add(audit)

        # Delete repository
        db.delete(repo)
        db.commit()

    def test_connection(
        self,
        remote_url: str,
        remote_type: RemoteType,
        branch: str = "main",
        credentials: Optional[dict] = None,
    ) -> tuple[bool, str, Optional[List[str]]]:
        """
        Test connection to a Git repository.

        Args:
            remote_url: Remote Git URL
            remote_type: Type of remote (local, ssh, https)
            branch: Branch to test
            credentials: Optional credentials

        Returns:
            Tuple of (success, message, available_branches)
        """
        if remote_type == RemoteType.LOCAL:
            # Check if local path exists
            if not os.path.exists(remote_url):
                return False, f"Local path does not exist: {remote_url}", None

            try:
                repo = git.Repo(remote_url)
                branches = [str(ref.name) for ref in repo.branches]

                if branch not in branches:
                    return False, f"Branch '{branch}' not found. Available: {', '.join(branches)}", branches

                return True, "Connection successful", branches
            except git.InvalidGitRepositoryError:
                return False, "Not a valid Git repository", None
            except Exception as e:
                return False, f"Error accessing repository: {str(e)}", None

        else:
            # For remote repos, try cloning to temp directory
            temp_dir = None
            try:
                temp_dir = tempfile.mkdtemp()

                # Prepare git command with credentials if provided
                env = os.environ.copy()

                if remote_type == RemoteType.HTTPS and credentials:
                    # For HTTPS, use token or username/password
                    token = credentials.get("token")
                    if token:
                        # Inject token into URL
                        if "://" in remote_url:
                            protocol, rest = remote_url.split("://", 1)
                            remote_url = f"{protocol}://{token}@{rest}"

                elif remote_type == RemoteType.SSH and credentials:
                    # For SSH, write private key to temp file
                    private_key = credentials.get("private_key")
                    if private_key:
                        key_file = os.path.join(temp_dir, "id_rsa")
                        with open(key_file, "w") as f:
                            f.write(private_key)
                        os.chmod(key_file, 0o600)

                        # Set SSH command to use this key
                        env["GIT_SSH_COMMAND"] = f"ssh -i {key_file} -o StrictHostKeyChecking=no"

                # Clone repository (shallow clone for speed)
                repo = git.Repo.clone_from(
                    remote_url,
                    temp_dir,
                    depth=1,
                    env=env,
                )

                # Get available branches
                branches = [str(ref.name) for ref in repo.remote().refs]
                branches = [b.replace("origin/", "") for b in branches if "/" in b]

                if branch not in branches:
                    return False, f"Branch '{branch}' not found. Available: {', '.join(branches)}", branches

                return True, "Connection successful", branches

            except git.GitCommandError as e:
                if "Authentication failed" in str(e) or "denied" in str(e).lower():
                    return False, "Authentication failed. Please check your credentials.", None
                elif "not found" in str(e).lower():
                    return False, "Repository not found. Please check the URL.", None
                else:
                    return False, f"Git error: {str(e)}", None

            except Exception as e:
                return False, f"Connection error: {str(e)}", None

            finally:
                # Clean up temp directory
                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)

    def trigger_sync(
        self,
        repo_id: str,
        force: bool,
        db: Session,
        current_user: User,
    ) -> tuple[str, str]:
        """
        Trigger manual sync for a repository.

        Args:
            repo_id: Repository ID
            force: Force re-sync from beginning
            db: Database session
            current_user: Current authenticated user

        Returns:
            Tuple of (message, task_id)

        Raises:
            HTTPException: If repository not found
        """
        repo = self.get_repository_by_id(repo_id, db)
        if not repo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found",
            )

        # Update status to syncing
        repo.status = RepoStatus.SYNCING
        repo.error_message = None

        if force:
            repo.last_ingested_sha = None

        db.commit()

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="trigger_sync",
            resource_type="repository",
            resource_id=repo_id,
            details=f"Triggered {'force ' if force else ''}sync for repository {repo.name}",
        )
        db.add(audit)
        db.commit()

        # TODO: Trigger Celery task here (Feature C)
        # task = sync_repo_task.delay(repo_id)
        # return f"Sync triggered for {repo.name}", task.id

        return f"Sync triggered for {repo.name} (worker not yet implemented)", None


# Singleton instance
repository_service = RepositoryService()
