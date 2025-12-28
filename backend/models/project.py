"""
Project model - collection of repositories for a league.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.repository import Repository


class Project(Base):
    """
    Project represents a collection of repositories for a league.

    A project groups multiple repos together (e.g., "Backend Team 2024").
    Each project has its own seasons, leaderboards, and awards.
    """

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    repositories: Mapped[list["Repository"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, slug={self.slug})>"
