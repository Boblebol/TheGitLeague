"""GitLeague Client - Push commits to GitLeague from your local repositories."""

__version__ = "0.1.0"
__author__ = "GitLeague Team"

from gitleague_client.exceptions import (
    GitLeagueError,
    GitScanError,
    APIError,
    AuthenticationError,
    ConfigError,
)

__all__ = [
    "GitLeagueError",
    "GitScanError",
    "APIError",
    "AuthenticationError",
    "ConfigError",
]
