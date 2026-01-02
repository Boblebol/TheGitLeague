"""Test configuration and fixtures."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User, UserRole, UserStatus
from app.models.api_key import APIKey
from app.models.project import Project

# Use in-memory SQLite for tests
DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(engine):
    """Create test database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user."""
    user = User(
        id="test-user-123",
        email="test@example.com",
        role=UserRole.COMMISSIONER,
        status=UserStatus.APPROVED,
        display_name="Test User",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def test_player(db_session):
    """Create a test player."""
    player = User(
        id="test-player-456",
        email="player@example.com",
        role=UserRole.PLAYER,
        status=UserStatus.APPROVED,
        display_name="Test Player",
    )
    db_session.add(player)
    db_session.commit()
    return player


@pytest.fixture(scope="function")
def test_project(db_session, test_user):
    """Create a test project."""
    project = Project(
        id="test-project-789",
        name="Test Project",
        slug="test-project",
        created_by=test_user.id,
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client."""
    from fastapi.testclient import TestClient
    from app.api.deps import get_db
    from app.main import app as fastapi_app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    return TestClient(fastapi_app)
