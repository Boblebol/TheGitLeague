"""Tests for API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from gitleague_client.api_client import GitLeagueAPIClient
from gitleague_client.exceptions import APIError, AuthenticationError


class TestGitLeagueAPIClient:
    """Test API client."""

    def test_init(self):
        """Test client initialization."""
        client = GitLeagueAPIClient(
            api_url="https://api.example.com",
            api_key="tgl_test_key",
        )

        assert client.api_url == "https://api.example.com"
        assert client.api_key == "tgl_test_key"
        assert "tgl_test_key" in client.headers["Authorization"]

    def test_init_url_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = GitLeagueAPIClient(
            api_url="https://api.example.com/",
            api_key="tgl_key",
        )

        assert client.api_url == "https://api.example.com"

    @patch("gitleague_client.api_client.httpx.Client")
    def test_test_connection_success(self, mock_client_class):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GitLeagueAPIClient(
            api_url="https://api.example.com",
            api_key="tgl_key",
        )

        result = client.test_connection()

        assert result is True
        mock_client.get.assert_called_once_with("https://api.example.com/health")

    @patch("gitleague_client.api_client.httpx.Client")
    def test_test_connection_auth_failure(self, mock_client_class):
        """Test connection test with auth failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GitLeagueAPIClient(
            api_url="https://api.example.com",
            api_key="invalid_key",
        )

        with pytest.raises(AuthenticationError):
            client.test_connection()

    @patch("gitleague_client.api_client.httpx.Client")
    def test_test_connection_failure(self, mock_client_class):
        """Test connection test with network error."""
        import httpx

        mock_client_class.side_effect = httpx.RequestError("Connection failed")

        client = GitLeagueAPIClient(
            api_url="https://api.example.com",
            api_key="tgl_key",
        )

        with pytest.raises(APIError, match="Connection failed"):
            client.test_connection()

    @patch("gitleague_client.api_client.httpx.Client")
    def test_get_repo_status_success(self, mock_client_class):
        """Test getting repo status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "repo_id": "repo-123",
            "status": "healthy",
            "last_ingested_sha": "abc123def456",
            "total_commits": 42,
            "last_sync_at": "2026-01-01T12:00:00Z",
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GitLeagueAPIClient(
            api_url="https://api.example.com",
            api_key="tgl_key",
        )

        status = client.get_repo_status("proj-123", "repo-123")

        assert status["status"] == "healthy"
        assert status["last_ingested_sha"] == "abc123def456"
        assert status["total_commits"] == 42

    @patch("gitleague_client.api_client.httpx.Client")
    def test_get_repo_status_not_found(self, mock_client_class):
        """Test getting status for non-existent repo."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GitLeagueAPIClient(
            api_url="https://api.example.com",
            api_key="tgl_key",
        )

        with pytest.raises(APIError, match="not found"):
            client.get_repo_status("proj-123", "nonexistent")

    @patch("gitleague_client.api_client.httpx.Client")
    @patch("gitleague_client.api_client.time.sleep")
    def test_sync_commits_success(self, mock_sleep, mock_client_class):
        """Test successful commit sync."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "total": 5,
            "inserted": 5,
            "skipped": 0,
            "errors": 0,
            "last_ingested_sha": "xyz789",
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GitLeagueAPIClient(
            api_url="https://api.example.com",
            api_key="tgl_key",
        )

        commits = [
            {
                "sha": f"{'a' * 40}",
                "author_name": "Test",
                "author_email": "test@example.com",
                "committer_name": "Test",
                "committer_email": "test@example.com",
                "commit_date": "2026-01-01T12:00:00Z",
                "message_title": "Test commit",
                "additions": 10,
                "deletions": 5,
                "files_changed": 2,
            }
        ]

        result = client.sync_commits("proj-123", "repo-123", commits)

        assert result["inserted"] == 5
        assert result["errors"] == 0

    @patch("gitleague_client.api_client.httpx.Client")
    @patch("gitleague_client.api_client.time.sleep")
    def test_sync_commits_rate_limit_retry(self, mock_sleep, mock_client_class):
        """Test retry on rate limit."""
        # First call: rate limited, second call: success
        responses = [
            Mock(status_code=429),
            Mock(
                status_code=201,
                json=lambda: {
                    "total": 5,
                    "inserted": 5,
                    "skipped": 0,
                    "errors": 0,
                },
            ),
        ]

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.side_effect = responses
        mock_client_class.return_value = mock_client

        client = GitLeagueAPIClient(
            api_url="https://api.example.com",
            api_key="tgl_key",
            max_retries=2,
        )

        commits = [
            {
                "sha": f"{'a' * 40}",
                "author_name": "Test",
                "author_email": "test@example.com",
                "committer_name": "Test",
                "committer_email": "test@example.com",
                "commit_date": "2026-01-01T12:00:00Z",
                "message_title": "Test",
                "additions": 0,
                "deletions": 0,
                "files_changed": 0,
            }
        ]

        result = client.sync_commits("proj-123", "repo-123", commits)

        assert result["inserted"] == 5
        mock_sleep.assert_called()

    @patch("gitleague_client.api_client.httpx.Client")
    @patch("gitleague_client.api_client.time.sleep")
    def test_sync_commits_max_retries_exceeded(self, mock_sleep, mock_client_class):
        """Test failure after max retries."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GitLeagueAPIClient(
            api_url="https://api.example.com",
            api_key="tgl_key",
            max_retries=2,
        )

        commits = [
            {
                "sha": f"{'a' * 40}",
                "author_name": "Test",
                "author_email": "test@example.com",
                "committer_name": "Test",
                "committer_email": "test@example.com",
                "commit_date": "2026-01-01T12:00:00Z",
                "message_title": "Test",
                "additions": 0,
                "deletions": 0,
                "files_changed": 0,
            }
        ]

        with pytest.raises(APIError):
            client.sync_commits("proj-123", "repo-123", commits)
