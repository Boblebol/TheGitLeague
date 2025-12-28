"""
Repository model with encrypted credentials support.

Handles secure storage of PAT tokens and other authentication methods
for accessing remote Git repositories.
"""

from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.project import Project


class AccessType(str, PyEnum):
    """Repository access method."""
    LOCAL_BARE = "local_bare"  # Local bare clone on server
    SSH = "ssh"  # SSH with key
    HTTPS_PAT = "https_pat"  # HTTPS with Personal Access Token


class RepoStatus(str, PyEnum):
    """Repository sync status."""
    PENDING = "pending"  # Not yet synced
    HEALTHY = "healthy"  # Last sync successful
    SYNCING = "syncing"  # Sync in progress
    ERROR = "error"  # Last sync failed


class Repository(Base):
    """
    Repository model with secure credential management.

    Stores encrypted PAT tokens in `encrypted_credentials` (JSONB).
    Never exposes decrypted credentials via API.
    """

    __tablename__ = "repos"

    # Foreign keys
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Repository metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    remote_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="URL without credentials (e.g., https://github.com/owner/repo.git)"
    )

    # Access configuration
    access_type: Mapped[AccessType] = mapped_column(
        Enum(AccessType),
        nullable=False,
        default=AccessType.HTTPS_PAT
    )

    # CRITICAL: Encrypted credentials (JSONB)
    # Structure: {"type": "pat", "encrypted_data": "...", "algorithm": "fernet", "key_version": "v1"}
    encrypted_credentials: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Encrypted credentials (PAT, SSH key, etc.) - NEVER exposed in API"
    )

    encryption_key_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="v1",
        comment="Key version for rotation support"
    )

    # Sync configuration
    branch: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="main"
    )

    # Sync status
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_ingested_sha: Mapped[Optional[str]] = mapped_column(
        String(40),
        nullable=True,
        comment="Last commit SHA ingested"
    )
    status: Mapped[RepoStatus] = mapped_column(
        Enum(RepoStatus),
        nullable=False,
        default=RepoStatus.PENDING,
        index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error details if status=ERROR"
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="repositories")

    def __repr__(self) -> str:
        return (
            f"<Repository(id={self.id}, name={self.name}, "
            f"project_id={self.project_id}, status={self.status.value})>"
        )

    @property
    def has_credentials(self) -> bool:
        """Check if repository has encrypted credentials configured."""
        return self.encrypted_credentials is not None

    @property
    def requires_credentials(self) -> bool:
        """Check if repository access type requires credentials."""
        return self.access_type in [AccessType.HTTPS_PAT, AccessType.SSH]

    @property
    def is_healthy(self) -> bool:
        """Check if repository is in healthy state."""
        return self.status == RepoStatus.HEALTHY

    def to_dict_safe(self) -> dict:
        """
        Convert to dictionary WITHOUT exposing encrypted credentials.

        This is the ONLY method that should be used for API responses.
        Never expose `encrypted_credentials` to clients.
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "remote_url": self.remote_url,
            "access_type": self.access_type.value,
            "has_credentials": self.has_credentials,  # Boolean, not actual creds
            "encryption_key_id": self.encryption_key_id,
            "branch": self.branch,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_ingested_sha": self.last_ingested_sha,
            "status": self.status.value,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
