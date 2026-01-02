"""User schemas for API validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole, UserStatus


# GitIdentity schemas
class GitIdentityBase(BaseModel):
    """Base schema for Git identity."""

    git_name: Optional[str] = None
    git_email: str


class GitIdentityCreate(GitIdentityBase):
    """Schema for creating a Git identity."""

    pass


class GitIdentityResponse(GitIdentityBase):
    """Schema for Git identity response."""

    id: str
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# User schemas
class UserBase(BaseModel):
    """Base schema for user."""

    email: EmailStr
    display_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""

    role: UserRole = UserRole.PLAYER


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    display_name: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response."""

    id: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    git_identities: List[GitIdentityResponse] = []

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Schema for user list response."""

    items: List[UserResponse]
    total: int
    page: int
    pages: int


# Auth schemas
class MagicLinkRequest(BaseModel):
    """Schema for requesting a magic link."""

    email: EmailStr


class MagicLinkResponse(BaseModel):
    """Schema for magic link response."""

    message: str
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenVerifyRequest(BaseModel):
    """Schema for verifying a token."""

    token: str


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class CurrentUser(UserResponse):
    """Schema for current authenticated user."""

    pass
