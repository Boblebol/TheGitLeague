"""Database session utilities."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from app.db.base import SessionLocal


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions (for use in Celery workers).

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
