"""Authentication API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.user import (
    MagicLinkRequest,
    MagicLinkResponse,
    TokenVerifyRequest,
    TokenResponse,
    CurrentUser,
)
from app.services.auth import auth_service
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(
    request_data: MagicLinkRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Request a magic link for passwordless authentication.

    - **email**: User email address

    Returns a message confirming the email was sent and expiration time.

    If the user doesn't exist, they will be created with PLAYER role.
    The first user in the system is automatically promoted to COMMISSIONER.
    """
    # Get base URL from request
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    result = await auth_service.request_magic_link(
        email=request_data.email,
        db=db,
        base_url=base_url,
    )

    return result


@router.get("/verify", response_model=TokenResponse)
async def verify_magic_link(
    token: str,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Verify a magic link token and return an access token.

    - **token**: Magic link token from email

    Returns an access token and user information.

    The token must be:
    - Valid and not expired (15 minutes)
    - Not previously used
    - Associated with an approved user
    """
    result = await auth_service.verify_magic_link(token=token, db=db)

    # Auto-associate git identity on first login
    auth_service.auto_associate_git_identity(result["user"], db)

    return result


@router.get("/me", response_model=CurrentUser)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get current authenticated user information.

    Requires valid access token in Authorization header:
    `Authorization: Bearer <token>`

    Returns user details including:
    - Basic info (email, display name, role, status)
    - Git identities associated with the user
    """
    return current_user
