"""
User model for authentication and RBAC.

Supports three roles:
- commissioner: Full access (can manage repos, projects, settings)
- player: Developer/contributor (can view their stats)
- spectator: Read-only (requires approval)
"""

from enum import Enum as PyEnum
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class UserRole(str, PyEnum):
    """User roles for RBAC."""
    COMMISSIONER = "commissioner"
    PLAYER = "player"
    SPECTATOR = "spectator"


class UserStatus(str, PyEnum):
    """User account status."""
    PENDING = "pending"  # Awaiting approval (for spectators)
    APPROVED = "approved"  # Active account
    SUSPENDED = "suspended"  # Temporarily disabled
    RETIRED = "retired"  # Hall of Fame (no longer active)


class User(Base):
    """
    User account model.

    Players are automatically associated with Git commits via git_identities.
    Spectators require commissioner approval before accessing the league.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.PLAYER
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        nullable=False,
        default=UserStatus.PENDING
    )

    # Optional: password hash if not using magic links only
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    # git_identities: Mapped[list["GitIdentity"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"

    @property
    def is_commissioner(self) -> bool:
        """Check if user has commissioner privileges."""
        return self.role == UserRole.COMMISSIONER

    @property
    def is_approved(self) -> bool:
        """Check if user is approved and active."""
        return self.status == UserStatus.APPROVED

    @property
    def can_access(self) -> bool:
        """Check if user can access the application."""
        # Commissioners always have access
        if self.is_commissioner:
            return True

        # Others need to be approved
        return self.is_approved
