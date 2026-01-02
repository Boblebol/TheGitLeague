"""API Keys endpoints."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeyRevokeResponse,
)
from app.services.api_key import api_key_service


router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("/", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new API key.

    The full API key is returned only once. Save it securely.

    Accessible by all authenticated users.
    """
    api_key, full_key = api_key_service.create_api_key(
        name=api_key_data.name,
        scopes=api_key_data.scopes,
        user=current_user,
        db=db,
        expires_in_days=api_key_data.expires_in_days,
    )

    return APIKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        scopes=api_key.scopes,
        status=api_key.status,
        last_used_at=api_key.last_used_at,
        last_used_ip=api_key.last_used_ip,
        usage_count=api_key.usage_count,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        revoked_at=api_key.revoked_at,
        full_key=full_key,
    )


@router.get("/", response_model=List[APIKeyResponse])
def list_api_keys(
    include_revoked: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List API keys for current user.

    Accessible by all authenticated users.
    """
    keys = api_key_service.list_api_keys(
        user=current_user,
        db=db,
        include_revoked=include_revoked,
    )

    return [APIKeyResponse.model_validate(key) for key in keys]


@router.delete("/{api_key_id}", response_model=APIKeyRevokeResponse)
def revoke_api_key(
    api_key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Revoke an API key.

    Once revoked, the key cannot be used anymore.

    Accessible by all authenticated users (own keys only).
    """
    revoked_key = api_key_service.revoke_api_key(
        api_key_id=api_key_id,
        user=current_user,
        db=db,
    )

    return APIKeyRevokeResponse(
        message=f"API key '{revoked_key.name}' has been revoked",
        revoked_key=APIKeyResponse.model_validate(revoked_key),
    )
