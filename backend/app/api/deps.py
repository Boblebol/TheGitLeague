"""API dependencies."""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User, UserRole
from app.services.auth import auth_service

# Security scheme
security = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Get current authenticated user.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    return auth_service.get_current_user(token, db)


def require_role(allowed_roles: list[UserRole]):
    """
    Dependency factory for role-based access control.

    Args:
        allowed_roles: List of allowed roles

    Returns:
        Dependency function
    """

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        """Check if user has required role."""
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


# Common dependencies
require_commissioner = require_role([UserRole.COMMISSIONER])
require_player = require_role([UserRole.PLAYER, UserRole.COMMISSIONER])
