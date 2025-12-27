"""SQLAlchemy models."""

from app.models.user import (
    User,
    GitIdentity,
    MagicLinkToken,
    AuditLog,
    UserRole,
    UserStatus,
)
from app.models.project import (
    Project,
    Repository,
    ProjectConfig,
    RemoteType,
    RepoStatus,
)
from app.models.commit import Commit
from app.models.season import (
    Season,
    Absence,
    SeasonStatus,
)
from app.models.leaderboard import PlayerPeriodStats
from app.models.award import Award, PlayOfTheDay, AwardType

__all__ = [
    "User",
    "GitIdentity",
    "MagicLinkToken",
    "AuditLog",
    "UserRole",
    "UserStatus",
    "Project",
    "Repository",
    "ProjectConfig",
    "RemoteType",
    "RepoStatus",
    "Commit",
    "Season",
    "Absence",
    "SeasonStatus",
    "PlayerPeriodStats",
    "Award",
    "PlayOfTheDay",
    "AwardType",
]
