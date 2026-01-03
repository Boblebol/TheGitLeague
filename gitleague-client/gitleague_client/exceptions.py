"""Custom exceptions for GitLeague Client."""


class GitLeagueError(Exception):
    """Base exception for all GitLeague errors."""

    pass


class GitScanError(GitLeagueError):
    """Exception raised during Git repository operations."""

    pass


class APIError(GitLeagueError):
    """Exception raised during API communication."""

    pass


class AuthenticationError(APIError):
    """Exception raised when API authentication fails."""

    pass


class ConfigError(GitLeagueError):
    """Exception raised when configuration is invalid."""

    pass
