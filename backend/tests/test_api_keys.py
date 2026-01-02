"""Tests for API key functionality."""

import pytest
from datetime import datetime, timedelta, timezone

from app.services.api_key import api_key_service
from app.models.api_key import APIKey, APIKeyStatus, APIKeyScope
from app.models.user import User
from app.core.security import verify_password


class TestAPIKeyGeneration:
    """Test API key generation."""

    def test_generate_api_key(self):
        """Test API key generation format."""
        full_key, prefix, secret = api_key_service.generate_api_key()

        # Check format
        assert full_key.startswith("tgl_")
        assert len(prefix) == 12  # tgl_xxxxxxxx
        assert len(secret) >= 30
        assert full_key == f"{prefix}_{secret}"

    def test_generate_api_key_unique(self):
        """Test that generated keys are unique."""
        key1, _, _ = api_key_service.generate_api_key()
        key2, _, _ = api_key_service.generate_api_key()

        assert key1 != key2


class TestAPIKeyCreation:
    """Test API key creation."""

    def test_create_api_key(self, db_session, test_user):
        """Test creating an API key."""
        api_key, full_key = api_key_service.create_api_key(
            name="Test Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        assert api_key.name == "Test Key"
        assert api_key.user_id == test_user.id
        assert api_key.status == APIKeyStatus.ACTIVE
        assert api_key.prefix.startswith("tgl_")
        assert full_key.startswith("tgl_")
        assert api_key.key_hash != full_key
        assert verify_password(full_key, api_key.key_hash)

    def test_create_api_key_with_expiration(self, db_session, test_user):
        """Test creating an API key with expiration."""
        before = datetime.now(timezone.utc)

        api_key, _ = api_key_service.create_api_key(
            name="Expiring Key",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
            expires_in_days=30,
        )

        after = datetime.now(timezone.utc)

        # Note: SQLite returns naive datetimes, so we need to handle timezone
        # For testing, we'll just check the delta is reasonable
        assert api_key.expires_at is not None
        # Should be approximately 30 days in the future
        delta = (api_key.expires_at - before.replace(tzinfo=None)).total_seconds()
        assert 29.9 * 86400 < delta < 30.1 * 86400  # ~30 days in seconds

    def test_create_api_key_no_expiration(self, db_session, test_user):
        """Test creating an API key without expiration."""
        api_key, _ = api_key_service.create_api_key(
            name="Permanent Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        assert api_key.expires_at is None

    def test_create_api_key_audit_log(self, db_session, test_user):
        """Test that API key creation is audited."""
        from app.models.user import AuditLog

        api_key, _ = api_key_service.create_api_key(
            name="Audited Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        # Check audit log
        audit = (
            db_session.query(AuditLog)
            .filter(AuditLog.action == "create_api_key")
            .filter(AuditLog.resource_id == api_key.id)
            .first()
        )

        assert audit is not None
        assert audit.user_id == test_user.id
        assert "Audited Key" in audit.details


class TestAPIKeyVerification:
    """Test API key verification."""

    def test_verify_api_key_valid(self, db_session, test_user):
        """Test verifying a valid API key."""
        api_key, full_key = api_key_service.create_api_key(
            name="Test Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        # Verify key
        verified_user = api_key_service.verify_api_key(full_key, db_session)

        assert verified_user is not None
        assert verified_user.id == test_user.id

    def test_verify_api_key_invalid_format(self, db_session):
        """Test verifying an invalid API key format."""
        fake_key = "invalid_key_format"

        verified_user = api_key_service.verify_api_key(fake_key, db_session)

        assert verified_user is None

    def test_verify_api_key_invalid_secret(self, db_session, test_user):
        """Test verifying an API key with invalid secret."""
        api_key, full_key = api_key_service.create_api_key(
            name="Test Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        # Modify the secret part
        wrong_key = full_key[:-10] + "wrongsecret"

        verified_user = api_key_service.verify_api_key(wrong_key, db_session)

        assert verified_user is None

    def test_verify_api_key_revoked(self, db_session, test_user):
        """Test that revoked keys cannot be verified."""
        api_key, full_key = api_key_service.create_api_key(
            name="Test Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        # Revoke key
        api_key_service.revoke_api_key(api_key.id, test_user, db_session)

        # Try to verify
        verified_user = api_key_service.verify_api_key(full_key, db_session)

        assert verified_user is None

    def test_verify_api_key_expired(self, db_session, test_user):
        """Test that expired keys cannot be verified."""
        api_key, full_key = api_key_service.create_api_key(
            name="Test Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
            expires_in_days=1,
        )

        # Manually set expiration to past (SQLite returns naive datetimes)
        api_key.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        db_session.commit()

        # Try to verify
        verified_user = api_key_service.verify_api_key(full_key, db_session)

        assert verified_user is None

    def test_verify_api_key_updates_usage(self, db_session, test_user):
        """Test that verification updates usage tracking."""
        api_key, full_key = api_key_service.create_api_key(
            name="Test Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        initial_usage = api_key.usage_count
        assert initial_usage == 0

        # Verify key
        api_key_service.verify_api_key(full_key, db_session)

        # Refresh from DB
        db_session.refresh(api_key)

        assert api_key.usage_count == initial_usage + 1
        assert api_key.last_used_at is not None

    def test_verify_api_key_with_ip_tracking(self, db_session, test_user):
        """Test that verification tracks IP address."""
        api_key, full_key = api_key_service.create_api_key(
            name="Test Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        # Verify key with IP
        api_key_service.verify_api_key(full_key, db_session, ip_address="192.168.1.100")

        # Refresh from DB
        db_session.refresh(api_key)

        assert api_key.last_used_ip == "192.168.1.100"


class TestAPIKeyRevocation:
    """Test API key revocation."""

    def test_revoke_api_key(self, db_session, test_user):
        """Test revoking an API key."""
        api_key, _ = api_key_service.create_api_key(
            name="Test Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        assert api_key.status == APIKeyStatus.ACTIVE

        # Revoke
        revoked = api_key_service.revoke_api_key(api_key.id, test_user, db_session)

        assert revoked.status == APIKeyStatus.REVOKED
        assert revoked.revoked_at is not None

    def test_revoke_api_key_not_found(self, db_session, test_user):
        """Test revoking a non-existent API key."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            api_key_service.revoke_api_key("non-existent-id", test_user, db_session)

        assert exc_info.value.status_code == 404

    def test_revoke_api_key_already_revoked(self, db_session, test_user):
        """Test revoking an already revoked API key."""
        from fastapi import HTTPException

        api_key, _ = api_key_service.create_api_key(
            name="Test Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        # Revoke once
        api_key_service.revoke_api_key(api_key.id, test_user, db_session)

        # Try to revoke again
        with pytest.raises(HTTPException) as exc_info:
            api_key_service.revoke_api_key(api_key.id, test_user, db_session)

        assert exc_info.value.status_code == 400
        assert "already revoked" in exc_info.value.detail

    def test_revoke_api_key_audit_log(self, db_session, test_user):
        """Test that API key revocation is audited."""
        from app.models.user import AuditLog

        api_key, _ = api_key_service.create_api_key(
            name="Test Key",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        api_key_service.revoke_api_key(api_key.id, test_user, db_session)

        # Check audit log
        audit = (
            db_session.query(AuditLog)
            .filter(AuditLog.action == "revoke_api_key")
            .filter(AuditLog.resource_id == api_key.id)
            .first()
        )

        assert audit is not None
        assert audit.user_id == test_user.id
        assert "Test Key" in audit.details


class TestAPIKeyListing:
    """Test API key listing."""

    def test_list_api_keys(self, db_session, test_user):
        """Test listing API keys for a user."""
        # Create multiple keys
        key1, _ = api_key_service.create_api_key(
            name="Key 1",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )
        key2, _ = api_key_service.create_api_key(
            name="Key 2",
            scopes=APIKeyScope.READ_REPOS,
            user=test_user,
            db=db_session,
        )

        keys = api_key_service.list_api_keys(test_user, db_session)

        assert len(keys) == 2
        assert key1.id in [k.id for k in keys]
        assert key2.id in [k.id for k in keys]

    def test_list_api_keys_excludes_revoked_by_default(self, db_session, test_user):
        """Test that revoked keys are excluded by default."""
        key1, _ = api_key_service.create_api_key(
            name="Active Key",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )
        key2, _ = api_key_service.create_api_key(
            name="Revoked Key",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )

        # Revoke one
        api_key_service.revoke_api_key(key2.id, test_user, db_session)

        keys = api_key_service.list_api_keys(test_user, db_session)

        assert len(keys) == 1
        assert keys[0].id == key1.id

    def test_list_api_keys_includes_revoked_when_requested(self, db_session, test_user):
        """Test that revoked keys are included when requested."""
        key1, _ = api_key_service.create_api_key(
            name="Active Key",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )
        key2, _ = api_key_service.create_api_key(
            name="Revoked Key",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )

        # Revoke one
        api_key_service.revoke_api_key(key2.id, test_user, db_session)

        keys = api_key_service.list_api_keys(test_user, db_session, include_revoked=True)

        assert len(keys) == 2

    def test_list_api_keys_for_different_user_empty(self, db_session, test_user, test_player):
        """Test that listing keys for one user doesn't include another user's keys."""
        api_key_service.create_api_key(
            name="Commissioner Key",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )

        keys = api_key_service.list_api_keys(test_player, db_session)

        assert len(keys) == 0
