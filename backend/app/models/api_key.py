"""API Key model for client authentication."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _get_utc_now():
    """Get current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class APIKeyStatus(str, enum.Enum):
    """API Key status."""

    ACTIVE = "active"
    REVOKED = "revoked"


class APIKeyScope(str, enum.Enum):
    """API Key scopes for fine-grained permissions."""

    SYNC_COMMITS = "sync:commits"  # Can push commits to repositories
    READ_REPOS = "read:repos"  # Can read repository information
    SYNC_COMMITS_READ = "sync:commits,read:repos"  # Both permissions combined


class APIKey(Base):
    """API Key model for external client authentication."""

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Key metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # User-friendly name
    prefix: Mapped[str] = mapped_column(
        String(12), nullable=False, unique=True, index=True
    )  # tgl_xxxxxxxx
    key_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Argon2 hash of full key

    # Permissions
    scopes: Mapped[str] = mapped_column(
        Enum(APIKeyScope, native_enum=False, length=50),
        nullable=False,
        default=APIKeyScope.SYNC_COMMITS_READ,
    )

    # Status
    status: Mapped[str] = mapped_column(
        Enum(APIKeyStatus, native_enum=False, length=20),
        nullable=False,
        default=APIKeyStatus.ACTIVE,
    )

    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_get_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_get_utc_now, onupdate=_get_utc_now, nullable=False
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<APIKey {self.prefix} ({self.status})>"
