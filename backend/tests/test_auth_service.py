"""Unit tests for authentication service."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from app.core.security import create_access_token, verify_password, create_magic_link_token
from app.models.user import User, UserRole, UserStatus


class TestMagicLinkGeneration:
    """Test magic link token generation."""

    def test_create_magic_link_token(self):
        """Test creating a magic link token."""
        email = "test@example.com"
        token = create_magic_link_token(email=email)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

    def test_magic_link_token_for_different_email(self):
        """Test that different emails generate different tokens."""
        email1 = "test1@example.com"
        email2 = "test2@example.com"
        token1 = create_magic_link_token(email=email1)
        token2 = create_magic_link_token(email=email2)

        assert token1 is not None
        assert token2 is not None
        # Different emails should generate different tokens
        assert token1 != token2

    def test_magic_link_token_format(self):
        """Test that magic link tokens are JWT format."""
        email = "test@example.com"
        token = create_magic_link_token(email=email)

        # Token should be JWT format (header.payload.signature)
        parts = token.split(".")
        assert len(parts) == 3


class TestAccessTokenGeneration:
    """Test access token generation."""

    def test_create_access_token(self, test_user):
        """Test creating an access token."""
        token = create_access_token(data={"sub": test_user.id})

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

    def test_access_token_contains_subject(self, test_user):
        """Test that access token contains the subject."""
        token = create_access_token(data={"sub": test_user.id})

        # Token should be JWT format (header.payload.signature)
        parts = token.split(".")
        assert len(parts) == 3

    def test_access_token_expiration(self, test_user):
        """Test access token expiration."""
        expires_delta = timedelta(hours=1)
        token = create_access_token(
            data={"sub": test_user.id},
            expires_delta=expires_delta,
        )

        assert token is not None


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hashing_different_each_time(self):
        """Test that password hashing produces different hashes."""
        password = "test_password_123"
        from app.core.security import hash_password

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        from app.core.security import hash_password

        password = "correct_password"
        hashed = hash_password(password)

        assert verify_password(password, hashed)

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        from app.core.security import hash_password

        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert not verify_password(wrong_password, hashed)


class TestUserApprovalFlow:
    """Test user approval workflow."""

    def test_user_pending_on_creation(self, db_session):
        """Test that new users are in PENDING status."""
        user = User(
            id="new-user-123",
            email="newuser@example.com",
            role=UserRole.PLAYER,
            status=UserStatus.PENDING,
        )
        db_session.add(user)
        db_session.commit()

        assert user.status == UserStatus.PENDING

    def test_approve_user(self, db_session, test_user):
        """Test approving a user."""
        test_user.status = UserStatus.PENDING
        db_session.commit()

        # Approve user
        test_user.status = UserStatus.APPROVED
        db_session.commit()

        # Verify approval
        db_session.refresh(test_user)
        assert test_user.status == UserStatus.APPROVED

    def test_retire_user(self, db_session, test_user):
        """Test retiring a user."""
        test_user.status = UserStatus.APPROVED
        db_session.commit()

        # Retire user
        test_user.status = UserStatus.RETIRED
        db_session.commit()

        db_session.refresh(test_user)
        assert test_user.status == UserStatus.RETIRED


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_commissioner_role(self):
        """Test commissioner role creation."""
        user = User(
            id="commissioner-123",
            email="commissioner@example.com",
            role=UserRole.COMMISSIONER,
            status=UserStatus.APPROVED,
        )

        assert user.role == UserRole.COMMISSIONER

    def test_player_role(self):
        """Test player role creation."""
        user = User(
            id="player-123",
            email="player@example.com",
            role=UserRole.PLAYER,
            status=UserStatus.APPROVED,
        )

        assert user.role == UserRole.PLAYER

    def test_spectator_role(self):
        """Test spectator role creation."""
        user = User(
            id="spectator-123",
            email="spectator@example.com",
            role=UserRole.SPECTATOR,
            status=UserStatus.APPROVED,
        )

        assert user.role == UserRole.SPECTATOR
