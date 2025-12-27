"""Pydantic schemas for API validation."""

from app.schemas.user import (
    GitIdentityCreate,
    GitIdentityResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    MagicLinkRequest,
    MagicLinkResponse,
    TokenVerifyRequest,
    TokenResponse,
    CurrentUser,
)

__all__ = [
    "GitIdentityCreate",
    "GitIdentityResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "MagicLinkRequest",
    "MagicLinkResponse",
    "TokenVerifyRequest",
    "TokenResponse",
    "CurrentUser",
]
