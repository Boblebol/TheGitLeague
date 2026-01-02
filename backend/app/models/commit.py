"""Commit model."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Commit(Base):
    """Commit model - stores Git commit metadata."""

    __tablename__ = "commits"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    sha: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        nullable=False,
        index=True,
    )
    repo_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Author information
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Committer information (can differ from author)
    committer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    committer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Commit metadata
    commit_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    message_title: Mapped[str] = mapped_column(String(500), nullable=False)
    message_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Git stats
    additions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deletions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_changed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Commit properties
    is_merge: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    parent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="commits")

    def __repr__(self) -> str:
        return f"<Commit {self.sha[:7]} by {self.author_name}>"

    __table_args__ = (
        # Composite index for common queries
        Index("ix_commits_repo_date", "repo_id", "commit_date"),
        Index("ix_commits_author_date", "author_email", "commit_date"),
    )
