"""User and GitIdentity models."""

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, Enum, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""

    COMMISSIONER = "commissioner"
    PLAYER = "player"
    SPECTATOR = "spectator"


class UserStatus(str, enum.Enum):
    """User status enumeration."""

    APPROVED = "approved"
    PENDING = "pending"
    RETIRED = "retired"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(
        Enum(UserRole, native_enum=False),
        nullable=False,
        default=UserRole.PLAYER,
    )
    status: Mapped[str] = mapped_column(
        Enum(UserStatus, native_enum=False),
        nullable=False,
        default=UserStatus.PENDING,
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    git_identities: Mapped[List["GitIdentity"]] = relationship(
        "GitIdentity",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="creator",
    )
    absences: Mapped[List["Absence"]] = relationship(
        "Absence",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    period_stats: Mapped[List["PlayerPeriodStats"]] = relationship(
        "PlayerPeriodStats",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class GitIdentity(Base):
    """Git identity model for mapping Git commits to users."""

    __tablename__ = "git_identities"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    git_name: Mapped[str] = mapped_column(String(255), nullable=True)
    git_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="git_identities")

    def __repr__(self) -> str:
        return f"<GitIdentity(id={self.id}, git_email={self.git_email})>"


class MagicLinkToken(Base):
    """Magic link token model for passwordless authentication."""

    __tablename__ = "magic_link_tokens"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<MagicLinkToken(email={self.email}, used={self.used})>"


class AuditLog(Base):
    """Audit log for tracking sensitive operations."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=True)
    details: Mapped[str] = mapped_column(String(1000), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action}, user_id={self.user_id})>"
