"""Project and Repository models."""

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RemoteType(str, enum.Enum):
    """Repository remote type."""

    LOCAL = "local"
    SSH = "ssh"
    HTTPS = "https"


class RepoStatus(str, enum.Enum):
    """Repository sync status."""

    PENDING = "pending"
    HEALTHY = "healthy"
    SYNCING = "syncing"
    ERROR = "error"


class Project(Base):
    """Project model - collection of repositories."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="projects")  # type: ignore
    repos: Mapped[List["Repository"]] = relationship(
        "Repository", back_populates="project", cascade="all, delete-orphan"
    )
    config: Mapped[Optional["ProjectConfig"]] = relationship(
        "ProjectConfig", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project {self.name} ({self.slug})>"


class Repository(Base):
    """Repository model - Git repositories to ingest."""

    __tablename__ = "repos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    remote_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remote_type: Mapped[str] = mapped_column(
        Enum(RemoteType, native_enum=False, length=20), nullable=False, default=RemoteType.LOCAL
    )
    branch: Mapped[str] = mapped_column(String(255), nullable=False, default="main")
    sync_frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Cron syntax
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_ingested_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(RepoStatus, native_enum=False, length=20), nullable=False, default=RepoStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    credentials_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="repos")
    commits: Mapped[List["Commit"]] = relationship(
        "Commit", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository {self.name} ({self.status})>"


class ProjectConfig(Base):
    """Project configuration model - scoring coefficients and settings."""

    __tablename__ = "project_configs"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )

    # Scoring coefficients (stored as JSON)
    scoring_coefficients: Mapped[dict] = mapped_column(
        Text,
        nullable=False,
        default=lambda: str({
            "additions_weight": 1.0,
            "deletions_weight": 0.6,
            "commit_base": 10,
            "multi_file_bonus": 5,
            "fix_bonus": 15,
            "wip_penalty": -10,
            "max_additions_cap": 1000,
            "max_deletions_cap": 1000,
        })
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="config")

    def __repr__(self) -> str:
        return f"<ProjectConfig for project {self.project_id}>"
