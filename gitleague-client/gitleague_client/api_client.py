"""API client for GitLeague backend communication."""

import time
from typing import List, Optional

import httpx

from gitleague_client.exceptions import APIError, AuthenticationError


class GitLeagueAPIClient:
    """HTTP client for GitLeague API."""

    def __init__(
        self,
        api_url: str,
        api_key: str,
        max_retries: int = 3,
        timeout: float = 30.0,
    ):
        """
        Initialize API client.

        Args:
            api_url: Base URL of GitLeague API
            api_key: API key for authentication
            max_retries: Maximum retries on transient errors
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.max_retries = max_retries
        self.timeout = timeout

        # Build headers with auth
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def test_connection(self) -> bool:
        """
        Test API connection and authentication.

        Returns:
            True if connection successful

        Raises:
            AuthenticationError: If authentication fails
            APIError: If connection fails
        """
        try:
            with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
                response = client.get(f"{self.api_url}/health")

                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code != 200:
                    raise APIError(f"API returned status {response.status_code}")

            return True

        except httpx.RequestError as e:
            raise APIError(f"Connection failed: {e}")

    def get_repo_status(self, project_id: str, repo_id: str) -> dict:
        """
        Get synchronization status for a repository.

        Args:
            project_id: Project ID
            repo_id: Repository ID

        Returns:
            Status information including last_ingested_sha

        Raises:
            APIError: If request fails
            AuthenticationError: If authentication fails
        """
        url = f"{self.api_url}/api/v1/sync/projects/{project_id}/repos/{repo_id}/status"

        try:
            with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
                response = client.get(url)

                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 404:
                    raise APIError(f"Repository not found: {repo_id}")
                elif response.status_code != 200:
                    raise APIError(f"API returned status {response.status_code}")

                return response.json()

        except httpx.RequestError as e:
            raise APIError(f"Failed to get repo status: {e}")

    def sync_commits(
        self,
        project_id: str,
        repo_id: str,
        commits: List[dict],
        client_version: Optional[str] = None,
    ) -> dict:
        """
        Push commits to the API.

        Args:
            project_id: Project ID
            repo_id: Repository ID
            commits: List of commit dicts
            client_version: Optional client version

        Returns:
            Sync result with insertion statistics

        Raises:
            APIError: If request fails
            AuthenticationError: If authentication fails
        """
        url = f"{self.api_url}/api/v1/sync/projects/{project_id}/repos/{repo_id}/commits"

        payload = {
            "commits": commits,
            "client_version": client_version,
        }

        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
                    response = client.post(url, json=payload)

                    if response.status_code == 401:
                        raise AuthenticationError("Invalid API key")
                    elif response.status_code == 404:
                        raise APIError(f"Repository not found: {repo_id}")
                    elif response.status_code == 400:
                        # Bad request - don't retry
                        raise APIError(f"Bad request: {response.text}")
                    elif response.status_code == 429:
                        # Rate limited - retry with backoff
                        wait_time = 2 ** attempt
                        last_error = APIError("Rate limited")
                        if attempt < self.max_retries - 1:
                            time.sleep(wait_time)
                            continue
                        else:
                            raise last_error
                    elif response.status_code != 201:
                        # Server error - retry
                        last_error = APIError(f"API returned status {response.status_code}")
                        if attempt < self.max_retries - 1:
                            wait_time = 2 ** attempt
                            time.sleep(wait_time)
                            continue
                        else:
                            raise last_error

                    return response.json()

            except httpx.RequestError as e:
                last_error = APIError(f"Request failed: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    raise last_error

        # Should not reach here
        if last_error:
            raise last_error
        raise APIError("Sync failed")
