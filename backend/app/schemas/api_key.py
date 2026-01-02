"""API Key Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.api_key import APIKeyStatus, APIKeyScope


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="User-friendly name"
    )
    scopes: APIKeyScope = Field(
        APIKeyScope.SYNC_COMMITS_READ, description="API key scopes"
    )
    expires_in_days: Optional[int] = Field(
        None, gt=0, le=365, description="Expiration in days (max 365)"
    )


class APIKeyResponse(BaseModel):
    """Schema for API key response (without secret)."""

    id: str
    name: str
    prefix: str  # Only show prefix, not full key
    scopes: APIKeyScope
    status: APIKeyStatus
    last_used_at: Optional[datetime] = None
    last_used_ip: Optional[str] = None
    usage_count: int
    expires_at: Optional[datetime] = None
    created_at: datetime
    revoked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APIKeyCreateResponse(APIKeyResponse):
    """Schema for API key creation response (includes full key ONCE)."""

    full_key: str = Field(
        ..., description="Full API key (save this, it won't be shown again)"
    )


class APIKeyRevokeResponse(BaseModel):
    """Schema for API key revocation response."""

    message: str
    revoked_key: APIKeyResponse
