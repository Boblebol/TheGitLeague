"""Tests for push-based Git synchronization."""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from app.models.project import Repository, RepoStatus, SyncMethod
from app.schemas.sync import CommitMetadata, SyncCommitsRequest
from app.services.sync import sync_service


class TestCommitMetadataSchema:
    """Test CommitMetadata schema validation."""

    def test_valid_commit_metadata(self):
        """Test creating valid commit metadata."""
        commit = CommitMetadata(
            sha="a" * 40,
            author_name="Alice",
            author_email="alice@example.com",
            committer_name="Bob",
            committer_email="bob@example.com",
            commit_date=datetime.now(timezone.utc),
            message_title="Test commit",
            message_body="Detailed message",
            additions=10,
            deletions=5,
            files_changed=3,
            is_merge=False,
            parent_count=1,
        )

        assert commit.sha == "a" * 40
        assert commit.author_email == "alice@example.com"

    def test_commit_email_normalization(self):
        """Test that emails are normalized to lowercase."""
        commit = CommitMetadata(
            sha="a" * 40,
            author_name="Alice",
            author_email="ALICE@EXAMPLE.COM",
            committer_name="Bob",
            committer_email="BOB@EXAMPLE.COM",
            commit_date=datetime.now(timezone.utc),
            message_title="Test",
            additions=0,
            deletions=0,
            files_changed=0,
        )

        assert commit.author_email == "alice@example.com"
        assert commit.committer_email == "bob@example.com"

    def test_commit_sha_validation_invalid_length(self):
        """Test that invalid SHA length is rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CommitMetadata(
                sha="a" * 39,  # Too short
                author_name="Alice",
                author_email="alice@example.com",
                committer_name="Bob",
                committer_email="bob@example.com",
                commit_date=datetime.now(timezone.utc),
                message_title="Test",
                additions=0,
                deletions=0,
                files_changed=0,
            )

    def test_commit_sha_validation_invalid_chars(self):
        """Test that non-hex characters in SHA are rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CommitMetadata(
                sha="z" * 40,  # 'z' is not hex
                author_name="Alice",
                author_email="alice@example.com",
                committer_name="Bob",
                committer_email="bob@example.com",
                commit_date=datetime.now(timezone.utc),
                message_title="Test",
                additions=0,
                deletions=0,
                files_changed=0,
            )

    def test_commit_sha_lowercase_conversion(self):
        """Test that uppercase SHA is converted to lowercase."""
        commit = CommitMetadata(
            sha="A" * 40,
            author_name="Alice",
            author_email="alice@example.com",
            committer_name="Bob",
            committer_email="bob@example.com",
            commit_date=datetime.now(timezone.utc),
            message_title="Test",
            additions=0,
            deletions=0,
            files_changed=0,
        )

        assert commit.sha == "a" * 40


class TestSyncCommitsRequestSchema:
    """Test SyncCommitsRequest schema validation."""

    def test_valid_request(self):
        """Test creating valid sync request."""
        commit = CommitMetadata(
            sha="a" * 40,
            author_name="Alice",
            author_email="alice@example.com",
            committer_name="Bob",
            committer_email="bob@example.com",
            commit_date=datetime.now(timezone.utc),
            message_title="Test",
            additions=0,
            deletions=0,
            files_changed=0,
        )

        request = SyncCommitsRequest(commits=[commit])

        assert len(request.commits) == 1
        assert request.commits[0].sha == "a" * 40

    def test_max_commits(self):
        """Test that up to 1000 commits are allowed."""
        commits = [
            CommitMetadata(
                sha=f"{i:040x}",
                author_name="Alice",
                author_email="alice@example.com",
                committer_name="Bob",
                committer_email="bob@example.com",
                commit_date=datetime.now(timezone.utc),
                message_title=f"Commit {i}",
                additions=0,
                deletions=0,
                files_changed=0,
            )
            for i in range(1000)
        ]

        request = SyncCommitsRequest(commits=commits)
        assert len(request.commits) == 1000

    def test_too_many_commits(self):
        """Test that more than 1000 commits are rejected."""
        from pydantic import ValidationError

        commits = [
            CommitMetadata(
                sha=f"{i:040x}",
                author_name="Alice",
                author_email="alice@example.com",
                committer_name="Bob",
                committer_email="bob@example.com",
                commit_date=datetime.now(timezone.utc),
                message_title=f"Commit {i}",
                additions=0,
                deletions=0,
                files_changed=0,
            )
            for i in range(1001)
        ]

        with pytest.raises(ValidationError):
            SyncCommitsRequest(commits=commits)

    def test_duplicate_shas_rejected(self):
        """Test that duplicate SHAs in batch are rejected."""
        from pydantic import ValidationError

        commit1 = CommitMetadata(
            sha="a" * 40,
            author_name="Alice",
            author_email="alice@example.com",
            committer_name="Bob",
            committer_email="bob@example.com",
            commit_date=datetime.now(timezone.utc),
            message_title="Commit 1",
            additions=0,
            deletions=0,
            files_changed=0,
        )

        commit2 = CommitMetadata(
            sha="a" * 40,  # Same SHA
            author_name="Charlie",
            author_email="charlie@example.com",
            committer_name="Dave",
            committer_email="dave@example.com",
            commit_date=datetime.now(timezone.utc),
            message_title="Commit 2",
            additions=0,
            deletions=0,
            files_changed=0,
        )

        with pytest.raises(ValidationError, match="Duplicate SHAs"):
            SyncCommitsRequest(commits=[commit1, commit2])


class TestSyncServiceValidation:
    """Test sync service validation methods."""

    def test_validate_repo_for_sync_push_client(self, db_session, test_user, test_project):
        """Test validating a push_client repository."""
        # Create a push_client repository
        repo = Repository(
            id="test-repo-id",
            project_id=test_project.id,
            name="Test Repo",
            sync_method=SyncMethod.PUSH_CLIENT,
            branch="main",
            status=RepoStatus.PENDING,
        )
        db_session.add(repo)
        db_session.commit()

        # Validate
        validated_repo = sync_service.validate_repo_for_sync(
            test_project.id, repo.id, test_user, db_session
        )

        assert validated_repo.id == repo.id
        assert validated_repo.sync_method == SyncMethod.PUSH_CLIENT

    def test_validate_repo_pull_celery_rejected(self, db_session, test_user, test_project):
        """Test that pull_celery repositories are rejected."""
        # Create a pull_celery repository
        repo = Repository(
            id="test-repo-id",
            project_id=test_project.id,
            name="Test Repo",
            sync_method=SyncMethod.PULL_CELERY,
            remote_url="https://github.com/org/repo.git",
            branch="main",
            status=RepoStatus.PENDING,
        )
        db_session.add(repo)
        db_session.commit()

        # Try to validate - should fail
        with pytest.raises(HTTPException) as exc_info:
            sync_service.validate_repo_for_sync(
                test_project.id, repo.id, test_user, db_session
            )

        assert exc_info.value.status_code == 400
        assert "not configured for push-based sync" in exc_info.value.detail

    def test_validate_repo_not_found(self, db_session, test_user, test_project):
        """Test validating a non-existent repository."""
        with pytest.raises(HTTPException) as exc_info:
            sync_service.validate_repo_for_sync(
                test_project.id, "nonexistent-repo-id", test_user, db_session
            )

        assert exc_info.value.status_code == 404

    def test_validate_project_not_found(self, db_session, test_user):
        """Test with non-existent project."""
        with pytest.raises(HTTPException) as exc_info:
            sync_service.validate_repo_for_sync(
                "nonexistent-project-id", "nonexistent-repo-id", test_user, db_session
            )

        assert exc_info.value.status_code == 404

    def test_validate_project_not_owned_by_user(self, db_session, test_user, test_player, test_project):
        """Test that user can't validate repos in projects they don't own."""
        repo = Repository(
            id="test-repo-id",
            project_id=test_project.id,
            name="Test Repo",
            sync_method=SyncMethod.PUSH_CLIENT,
            branch="main",
            status=RepoStatus.PENDING,
        )
        db_session.add(repo)
        db_session.commit()

        # Try to validate as different user
        with pytest.raises(HTTPException) as exc_info:
            sync_service.validate_repo_for_sync(
                test_project.id, repo.id, test_player, db_session
            )

        assert exc_info.value.status_code == 404


class TestSyncServiceCommitIngestion:
    """Test commit ingestion logic."""

    def test_ingest_new_commits(self, db_session, test_user, test_project):
        """Test ingesting new commits."""
        # Create a push_client repository
        repo = Repository(
            id="test-repo-id",
            project_id=test_project.id,
            name="Test Repo",
            sync_method=SyncMethod.PUSH_CLIENT,
            branch="main",
            status=RepoStatus.PENDING,
        )
        db_session.add(repo)
        db_session.commit()

        # Create commits
        commits = [
            CommitMetadata(
                sha=f"{i:040x}",
                author_name="Alice",
                author_email="alice@example.com",
                committer_name="Bob",
                committer_email="bob@example.com",
                commit_date=datetime.now(timezone.utc),
                message_title=f"Commit {i}",
                additions=i * 10,
                deletions=i * 5,
                files_changed=i,
            )
            for i in range(5)
        ]

        # Ingest
        inserted, skipped, errors, last_sha, details = sync_service.ingest_commits(
            repo, commits, test_user, db_session
        )

        # Verify
        assert inserted == 5
        assert skipped == 0
        assert errors == 0
        assert last_sha is not None

        # Verify repo status updated
        db_session.refresh(repo)
        assert repo.status == RepoStatus.HEALTHY
        assert repo.last_ingested_sha == f"{4:040x}"
        assert repo.last_sync_at is not None

    def test_ingest_duplicate_commits_skipped(self, db_session, test_user, test_project):
        """Test that duplicate commits are skipped."""
        from app.models.commit import Commit

        # Create a push_client repository
        repo = Repository(
            id="test-repo-id",
            project_id=test_project.id,
            name="Test Repo",
            sync_method=SyncMethod.PUSH_CLIENT,
            branch="main",
            status=RepoStatus.PENDING,
        )
        db_session.add(repo)
        db_session.commit()

        # Create an existing commit
        existing_commit = Commit(
            sha="a" * 40,
            repo_id=repo.id,
            author_name="Alice",
            author_email="alice@example.com",
            committer_name="Bob",
            committer_email="bob@example.com",
            commit_date=datetime.now(timezone.utc),
            message_title="Existing commit",
            additions=0,
            deletions=0,
            files_changed=0,
        )
        db_session.add(existing_commit)
        db_session.commit()

        # Ingest with duplicate
        commits = [
            CommitMetadata(
                sha="a" * 40,  # Existing
                author_name="Alice",
                author_email="alice@example.com",
                committer_name="Bob",
                committer_email="bob@example.com",
                commit_date=datetime.now(timezone.utc),
                message_title="Existing commit",
                additions=0,
                deletions=0,
                files_changed=0,
            ),
            CommitMetadata(
                sha="b" * 40,  # New
                author_name="Alice",
                author_email="alice@example.com",
                committer_name="Bob",
                committer_email="bob@example.com",
                commit_date=datetime.now(timezone.utc),
                message_title="New commit",
                additions=10,
                deletions=5,
                files_changed=2,
            ),
        ]

        # Ingest
        inserted, skipped, errors, last_sha, details = sync_service.ingest_commits(
            repo, commits, test_user, db_session
        )

        # Verify
        assert inserted == 1
        assert skipped == 1
        assert errors == 0
        assert last_sha == "b" * 40

        # Check details
        assert len(details) == 2
        assert not details[0].inserted  # Skipped
        assert details[1].inserted  # New

    def test_get_sync_status(self, db_session, test_user, test_project):
        """Test getting sync status."""
        from app.models.commit import Commit

        # Create a push_client repository
        repo = Repository(
            id="test-repo-id",
            project_id=test_project.id,
            name="Test Repo",
            sync_method=SyncMethod.PUSH_CLIENT,
            branch="main",
            status=RepoStatus.HEALTHY,
            last_ingested_sha="a" * 40,
        )
        db_session.add(repo)
        db_session.commit()

        # Add some commits
        for i in range(5):
            commit = Commit(
                sha=f"{i:040x}",
                repo_id=repo.id,
                author_name="Alice",
                author_email="alice@example.com",
                committer_name="Bob",
                committer_email="bob@example.com",
                commit_date=datetime.now(timezone.utc),
                message_title=f"Commit {i}",
                additions=0,
                deletions=0,
                files_changed=0,
            )
            db_session.add(commit)
        db_session.commit()

        # Get status
        status_info = sync_service.get_sync_status(test_project.id, repo.id, test_user, db_session)

        # Verify
        assert status_info["repo_id"] == repo.id
        assert status_info["status"] == RepoStatus.HEALTHY
        assert status_info["total_commits"] == 5
        assert status_info["last_ingested_sha"] == "a" * 40
