"""API dependencies."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User, UserRole
from app.services.auth import auth_service
from app.services.api_key import api_key_service

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


def get_current_user_from_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> Optional[User]:
    """
    Authenticate user via API key.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        request: FastAPI request (for IP tracking)

    Returns:
        User if API key valid, None otherwise
    """
    api_key = credentials.credentials

    # Extract IP address
    ip_address = request.client.host if request.client else None

    # Verify API key
    user = api_key_service.verify_api_key(api_key, db, ip_address)

    return user


def get_current_user_hybrid(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> User:
    """
    Hybrid authentication: Try JWT first, then API key.

    This allows both JWT tokens and API keys to work with the same endpoints.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        request: FastAPI request

    Returns:
        Authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    # Try JWT authentication first
    try:
        return auth_service.get_current_user(token, db)
    except HTTPException:
        pass  # JWT failed, try API key

    # Try API key authentication
    user = get_current_user_from_api_key(credentials, db, request)
    if user:
        return user

    # Both failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


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
