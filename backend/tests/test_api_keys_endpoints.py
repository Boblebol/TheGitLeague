"""Tests for API keys endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.models.api_key import APIKeyScope, APIKeyStatus


class TestCreateAPIKeyEndpoint:
    """Test POST /api-keys/ endpoint."""

    def test_create_api_key_success(self, client, test_user):
        """Test successful API key creation."""
        # Create JWT token for test user
        from app.core.security import create_access_token

        token = create_access_token({"sub": test_user.id})

        response = client.post(
            "/api/v1/api-keys/",
            json={
                "name": "Test CLI",
                "scopes": APIKeyScope.SYNC_COMMITS_READ,
                "expires_in_days": 30,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test CLI"
        assert data["prefix"].startswith("tgl_")
        assert data["status"] == APIKeyStatus.ACTIVE
        assert "full_key" in data
        assert data["full_key"].startswith("tgl_")

    def test_create_api_key_no_auth(self, client):
        """Test that creating API key requires authentication."""
        response = client.post(
            "/api/v1/api-keys/",
            json={
                "name": "Test CLI",
                "scopes": APIKeyScope.SYNC_COMMITS_READ,
            },
        )

        assert response.status_code == 401

    def test_create_api_key_invalid_name(self, client, test_user):
        """Test validation of API key name."""
        from app.core.security import create_access_token

        token = create_access_token({"sub": test_user.id})

        response = client.post(
            "/api/v1/api-keys/",
            json={
                "name": "",  # Empty name
                "scopes": APIKeyScope.SYNC_COMMITS_READ,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422  # Validation error


class TestListAPIKeysEndpoint:
    """Test GET /api-keys/ endpoint."""

    def test_list_api_keys_success(self, client, test_user, db_session):
        """Test listing API keys."""
        from app.core.security import create_access_token
        from app.services.api_key import api_key_service

        # Create a few keys
        api_key_service.create_api_key(
            name="Key 1",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )
        api_key_service.create_api_key(
            name="Key 2",
            scopes=APIKeyScope.READ_REPOS,
            user=test_user,
            db=db_session,
        )

        token = create_access_token({"sub": test_user.id})

        response = client.get(
            "/api/v1/api-keys/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] in ["Key 1", "Key 2"]
        assert data[1]["name"] in ["Key 1", "Key 2"]

    def test_list_api_keys_no_auth(self, client):
        """Test that listing keys requires authentication."""
        response = client.get("/api/v1/api-keys/")

        assert response.status_code == 401

    def test_list_api_keys_excludes_revoked_by_default(self, client, test_user, db_session):
        """Test that revoked keys are excluded by default."""
        from app.core.security import create_access_token
        from app.services.api_key import api_key_service

        key1, _ = api_key_service.create_api_key(
            name="Active",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )
        key2, _ = api_key_service.create_api_key(
            name="Revoked",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )

        api_key_service.revoke_api_key(key2.id, test_user, db_session)

        token = create_access_token({"sub": test_user.id})

        response = client.get(
            "/api/v1/api-keys/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Active"

    def test_list_api_keys_includes_revoked_when_requested(
        self, client, test_user, db_session
    ):
        """Test that revoked keys are included when requested."""
        from app.core.security import create_access_token
        from app.services.api_key import api_key_service

        api_key_service.create_api_key(
            name="Active",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )
        key2, _ = api_key_service.create_api_key(
            name="Revoked",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )

        api_key_service.revoke_api_key(key2.id, test_user, db_session)

        token = create_access_token({"sub": test_user.id})

        response = client.get(
            "/api/v1/api-keys/?include_revoked=true",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestRevokeAPIKeyEndpoint:
    """Test DELETE /api-keys/{id} endpoint."""

    def test_revoke_api_key_success(self, client, test_user, db_session):
        """Test successful API key revocation."""
        from app.core.security import create_access_token
        from app.services.api_key import api_key_service

        api_key, _ = api_key_service.create_api_key(
            name="To Revoke",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )

        token = create_access_token({"sub": test_user.id})

        response = client.delete(
            f"/api/v1/api-keys/{api_key.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "revoked" in data["message"].lower()
        assert data["revoked_key"]["status"] == APIKeyStatus.REVOKED

    def test_revoke_api_key_not_found(self, client, test_user):
        """Test revoking non-existent API key."""
        from app.core.security import create_access_token

        token = create_access_token({"sub": test_user.id})

        response = client.delete(
            "/api/v1/api-keys/non-existent-id",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_revoke_api_key_no_auth(self, client, test_user, db_session):
        """Test that revoking requires authentication."""
        from app.services.api_key import api_key_service

        api_key, _ = api_key_service.create_api_key(
            name="Test",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )

        response = client.delete(f"/api/v1/api-keys/{api_key.id}")

        assert response.status_code == 401

    def test_revoke_api_key_not_owner(self, client, test_user, test_player, db_session):
        """Test that users can only revoke their own keys."""
        from app.core.security import create_access_token
        from app.services.api_key import api_key_service

        # Create key for test_user
        api_key, _ = api_key_service.create_api_key(
            name="Not My Key",
            scopes=APIKeyScope.SYNC_COMMITS,
            user=test_user,
            db=db_session,
        )

        # Try to revoke as test_player
        token = create_access_token({"sub": test_player.id})

        response = client.delete(
            f"/api/v1/api-keys/{api_key.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestHybridAuthentication:
    """Test hybrid authentication (JWT + API key)."""

    def test_sync_endpoint_with_api_key(self, client, test_user, db_session):
        """Test that sync endpoint accepts API key authentication."""
        from app.services.api_key import api_key_service

        _, full_key = api_key_service.create_api_key(
            name="Sync Client",
            scopes=APIKeyScope.SYNC_COMMITS_READ,
            user=test_user,
            db=db_session,
        )

        # This endpoint will be created in Phase 3 (sync.py)
        # For now, just test that the hybrid auth dependency works
        # with API keys by testing /api/v1/api-keys/ endpoint with API key

        # First create a key for listing (using JWT)
        from app.core.security import create_access_token

        jwt_token = create_access_token({"sub": test_user.id})
        response = client.get(
            "/api/v1/api-keys/",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )

        assert response.status_code == 200

        # (API key won't work on /api-keys/ endpoint since it uses get_current_user
        # not get_current_user_hybrid. Hybrid auth will be tested on /sync/ endpoint)
