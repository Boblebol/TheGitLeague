"""SQLAlchemy models."""

from app.models.user import (
    User,
    GitIdentity,
    MagicLinkToken,
    AuditLog,
    UserRole,
    UserStatus,
)
from app.models.api_key import (
    APIKey,
    APIKeyStatus,
    APIKeyScope,
)
from app.models.project import (
    Project,
    Repository,
    ProjectConfig,
    RemoteType,
    RepoStatus,
    SyncMethod,
)
from app.models.commit import Commit
from app.models.season import (
    Season,
    Absence,
    SeasonStatus,
)
from app.models.leaderboard import PlayerPeriodStats
from app.models.award import Award, PlayOfTheDay, AwardType
from app.models.fantasy import (
    FantasyLeague,
    FantasyParticipant,
    FantasyRoster,
    FantasyRosterPick,
)

__all__ = [
    "User",
    "GitIdentity",
    "MagicLinkToken",
    "AuditLog",
    "UserRole",
    "UserStatus",
    "APIKey",
    "APIKeyStatus",
    "APIKeyScope",
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
    "FantasyLeague",
    "FantasyParticipant",
    "FantasyRoster",
    "FantasyRosterPick",
]
