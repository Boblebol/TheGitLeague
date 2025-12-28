"""
Audit log model for tracking security-sensitive operations.

Logs all access to credentials, configuration changes, and RBAC events.
"""

from sqlalchemy import String, Text, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from backend.models.base import Base


class AuditLog(Base):
    """
    Audit log for security and compliance tracking.

    Records all sensitive operations:
    - Credential access (for Git sync)
    - Repository creation/modification/deletion
    - User approvals
    - Configuration changes
    - Failed authentication attempts
    """

    __tablename__ = "audit_logs"

    # Event classification
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Event type (e.g., 'repo.credentials.accessed', 'repo.created')"
    )

    # Actor (nullable for system/worker actions)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Resource affected
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Type of resource (repo, project, season, user)"
    )
    resource_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="ID of affected resource"
    )

    # Event details (JSONB) - NEVER include secrets here
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Event details WITHOUT sensitive data"
    )

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="Client IP address"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Client user agent"
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, event_type={self.event_type}, "
            f"user_id={self.user_id}, resource={self.resource_type}:{self.resource_id})>"
        )

    @classmethod
    def create_event(
        cls,
        event_type: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "AuditLog":
        """
        Factory method for creating audit log entries.

        Args:
            event_type: Type of event (e.g., "repo.credentials.accessed")
            user_id: User who performed the action (None for system actions)
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            metadata: Additional context (MUST NOT contain secrets)
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            AuditLog instance (not yet saved to DB)

        Security:
            NEVER include sensitive data in metadata:
            - ❌ Tokens, passwords, keys
            - ❌ Full credential payloads
            - ✅ Resource names, actions, outcomes
        """
        return cls(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )


# Common event types (constants for consistency)
class AuditEventType:
    """Common audit event types."""

    # Repository events
    REPO_CREATED = "repo.created"
    REPO_UPDATED = "repo.updated"
    REPO_DELETED = "repo.deleted"
    REPO_CREDENTIALS_ACCESSED = "repo.credentials.accessed"
    REPO_SYNC_STARTED = "repo.sync.started"
    REPO_SYNC_COMPLETED = "repo.sync.completed"
    REPO_SYNC_FAILED = "repo.sync.failed"

    # User events
    USER_LOGIN = "user.login"
    USER_LOGIN_FAILED = "user.login.failed"
    USER_APPROVED = "user.approved"
    USER_SUSPENDED = "user.suspended"

    # Configuration events
    CONFIG_RULES_UPDATED = "config.rules.updated"
    CONFIG_SEASON_CREATED = "config.season.created"
