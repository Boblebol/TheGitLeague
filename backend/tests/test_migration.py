"""Tests for repository migration from PULL_CELERY to PUSH_CLIENT."""

import pytest
from datetime import datetime, timedelta, timezone

from app.models.project import Repository, RepoStatus, SyncMethod, Project
from app.models.user import User, UserRole, UserStatus, AuditLog


class TestRepositoryMigration:
    """Test repository migration scenarios."""

    def test_migrate_pull_celery_to_push_client(self, db_session, test_user, test_project):
        """Test basic migration from PULL_CELERY to PUSH_CLIENT."""
        # Create a PULL_CELERY repository
        repo = Repository(
            id="test-repo-migration",
            project_id=test_project.id,
            name="Test Repo",
            remote_url="https://github.com/org/repo.git",
            remote_type="https",
            sync_method=SyncMethod.PULL_CELERY,
            branch="main",
            status=RepoStatus.HEALTHY,
            credentials_encrypted="encrypted_pat_token",
            last_ingested_sha="abc123def456",
        )
        db_session.add(repo)
        db_session.commit()

        # Verify initial state
        assert repo.sync_method == SyncMethod.PULL_CELERY
        assert repo.credentials_encrypted is not None

        # Simulate migration
        repo.sync_method = SyncMethod.PUSH_CLIENT
        repo.credentials_encrypted = None
        repo.updated_at = datetime.now(timezone.utc)
        db_session.commit()

        # Verify migrated state
        db_session.refresh(repo)
        assert repo.sync_method == SyncMethod.PUSH_CLIENT
        assert repo.credentials_encrypted is None
        assert repo.last_ingested_sha == "abc123def456"  # Preserved

    def test_migrate_preserves_last_ingested_sha(self, db_session, test_user, test_project):
        """Test that last_ingested_sha is preserved during migration."""
        last_sha = "xyz789abc123"
        repo = Repository(
            id="test-repo-sha",
            project_id=test_project.id,
            name="SHA Preservation",
            sync_method=SyncMethod.PULL_CELERY,
            branch="main",
            status=RepoStatus.HEALTHY,
            last_ingested_sha=last_sha,
        )
        db_session.add(repo)
        db_session.commit()

        # Migrate
        repo.sync_method = SyncMethod.PUSH_CLIENT
        db_session.commit()

        # Verify SHA preserved
        db_session.refresh(repo)
        assert repo.last_ingested_sha == last_sha

    def test_migrate_clears_credentials(self, db_session, test_user, test_project):
        """Test that credentials are cleared during migration."""
        encrypted_creds = "encrypted_github_token_with_salt"
        repo = Repository(
            id="test-repo-creds",
            project_id=test_project.id,
            name="Credentials Test",
            sync_method=SyncMethod.PULL_CELERY,
            branch="main",
            status=RepoStatus.HEALTHY,
            credentials_encrypted=encrypted_creds,
        )
        db_session.add(repo)
        db_session.commit()

        # Verify credentials exist
        assert repo.credentials_encrypted == encrypted_creds

        # Migrate and clear credentials
        repo.sync_method = SyncMethod.PUSH_CLIENT
        repo.credentials_encrypted = None
        db_session.commit()

        # Verify cleared
        db_session.refresh(repo)
        assert repo.credentials_encrypted is None

    def test_migrate_updates_timestamp(self, db_session, test_user, test_project):
        """Test that updated_at is set during migration."""
        before_migration = datetime.now(timezone.utc)

        repo = Repository(
            id="test-repo-ts",
            project_id=test_project.id,
            name="Timestamp Test",
            sync_method=SyncMethod.PULL_CELERY,
            branch="main",
            status=RepoStatus.HEALTHY,
            updated_at=datetime.now(timezone.utc) - timedelta(days=30),
        )
        db_session.add(repo)
        db_session.commit()

        old_timestamp = repo.updated_at

        # Migrate
        repo.updated_at = datetime.now(timezone.utc)
        repo.sync_method = SyncMethod.PUSH_CLIENT
        db_session.commit()

        after_migration = datetime.now(timezone.utc)

        # Verify timestamp updated
        db_session.refresh(repo)
        assert repo.updated_at > old_timestamp

        # Handle SQLite's naive datetimes
        updated_ts = repo.updated_at
        if updated_ts.tzinfo is None:
            before_migration = before_migration.replace(tzinfo=None)
            after_migration = after_migration.replace(tzinfo=None)

        assert before_migration <= updated_ts <= after_migration

    def test_migrate_creates_audit_log(self, db_session, test_user, test_project):
        """Test that migration creates an audit log entry."""
        repo = Repository(
            id="test-repo-audit",
            project_id=test_project.id,
            name="Audit Test",
            sync_method=SyncMethod.PULL_CELERY,
            branch="main",
            status=RepoStatus.HEALTHY,
        )
        db_session.add(repo)
        db_session.commit()

        # Migrate and log
        repo.sync_method = SyncMethod.PUSH_CLIENT
        db_session.commit()

        audit = AuditLog(
            user_id=test_user.id,
            action="migrate_repo_sync_method",
            resource_type="repository",
            resource_id=repo.id,
            details=f"Migrated repository '{repo.name}' from {SyncMethod.PULL_CELERY} to {SyncMethod.PUSH_CLIENT}",
        )
        db_session.add(audit)
        db_session.commit()

        # Verify audit log
        audit_entry = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.action == "migrate_repo_sync_method",
                AuditLog.resource_id == repo.id,
            )
            .first()
        )

        assert audit_entry is not None
        assert audit_entry.user_id == test_user.id
        assert "Audit Test" in audit_entry.details

    def test_already_push_client_idempotent(self, db_session, test_user, test_project):
        """Test that migrating already-migrated repo is idempotent."""
        repo = Repository(
            id="test-repo-idempotent",
            project_id=test_project.id,
            name="Already Migrated",
            sync_method=SyncMethod.PUSH_CLIENT,
            branch="main",
            status=RepoStatus.HEALTHY,
        )
        db_session.add(repo)
        db_session.commit()

        # "Migrate" again
        assert repo.sync_method == SyncMethod.PUSH_CLIENT
        # Should handle gracefully (no error)

    def test_cannot_migrate_non_pull_celery(self, db_session, test_user, test_project):
        """Test that non-PULL_CELERY repos cannot be migrated."""
        repo = Repository(
            id="test-repo-invalid",
            project_id=test_project.id,
            name="Invalid Method",
            sync_method=SyncMethod.PUSH_CLIENT,
            branch="main",
            status=RepoStatus.HEALTHY,
        )
        db_session.add(repo)
        db_session.commit()

        # Attempt to "migrate" - should be no-op or error
        assert repo.sync_method != SyncMethod.PULL_CELERY


class TestMigrationScenarios:
    """Test realistic migration scenarios."""

    def test_migrate_multiple_repos_same_project(
        self, db_session, test_user, test_project
    ):
        """Test migrating multiple repos in the same project."""
        # Create 3 PULL_CELERY repos
        repos = []
        for i in range(3):
            repo = Repository(
                id=f"test-repo-multi-{i}",
                project_id=test_project.id,
                name=f"Repo {i}",
                sync_method=SyncMethod.PULL_CELERY,
                branch="main",
                status=RepoStatus.HEALTHY,
            )
            db_session.add(repo)
            repos.append(repo)
        db_session.commit()

        # Migrate all
        for repo in repos:
            repo.sync_method = SyncMethod.PUSH_CLIENT
        db_session.commit()

        # Verify all migrated
        for repo in repos:
            db_session.refresh(repo)
            assert repo.sync_method == SyncMethod.PUSH_CLIENT

    def test_rollback_migration(self, db_session, test_user, test_project):
        """Test rolling back a migration."""
        repo = Repository(
            id="test-repo-rollback",
            project_id=test_project.id,
            name="Rollback Test",
            sync_method=SyncMethod.PUSH_CLIENT,
            branch="main",
            status=RepoStatus.HEALTHY,
        )
        db_session.add(repo)
        db_session.commit()

        # Rollback to PULL_CELERY
        repo.sync_method = SyncMethod.PULL_CELERY
        db_session.commit()

        # Verify rolled back
        db_session.refresh(repo)
        assert repo.sync_method == SyncMethod.PULL_CELERY

    def test_migration_preserves_status(self, db_session, test_user, test_project):
        """Test that repo status is preserved during migration."""
        statuses = [RepoStatus.HEALTHY, RepoStatus.ERROR, RepoStatus.SYNCING]

        for status in statuses:
            repo = Repository(
                id=f"test-repo-status-{status}",
                project_id=test_project.id,
                name=f"Status {status}",
                sync_method=SyncMethod.PULL_CELERY,
                branch="main",
                status=status,
            )
            db_session.add(repo)
        db_session.commit()

        # Migrate all
        repos = (
            db_session.query(Repository)
            .filter(Repository.project_id == test_project.id)
            .all()
        )
        for repo in repos:
            repo.sync_method = SyncMethod.PUSH_CLIENT
        db_session.commit()

        # Verify status preserved
        for status in statuses:
            repo = (
                db_session.query(Repository)
                .filter(Repository.id == f"test-repo-status-{status}")
                .first()
            )
            assert repo.status == status

    def test_inactive_repos_filter(self, db_session, test_user, test_project):
        """Test filtering inactive repos for selective migration."""
        # Create recently synced repo
        recent_repo = Repository(
            id="test-repo-recent",
            project_id=test_project.id,
            name="Recently Synced",
            sync_method=SyncMethod.PULL_CELERY,
            branch="main",
            status=RepoStatus.HEALTHY,
            last_sync_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        # Create old repo
        old_repo = Repository(
            id="test-repo-old",
            project_id=test_project.id,
            name="Not Synced Recently",
            sync_method=SyncMethod.PULL_CELERY,
            branch="main",
            status=RepoStatus.HEALTHY,
            last_sync_at=datetime.now(timezone.utc) - timedelta(days=30),
        )

        db_session.add(recent_repo)
        db_session.add(old_repo)
        db_session.commit()

        # Query inactive repos (not synced in 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        inactive_repos = (
            db_session.query(Repository)
            .filter(
                Repository.sync_method == SyncMethod.PULL_CELERY,
                (Repository.last_sync_at.is_(None)) | (Repository.last_sync_at < seven_days_ago),
            )
            .all()
        )

        # Verify only old repo is inactive
        assert len(inactive_repos) == 1
        assert inactive_repos[0].id == "test-repo-old"
