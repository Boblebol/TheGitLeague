"""Users API endpoints."""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.user import (
    UserResponse,
    UserListResponse,
    UserUpdate,
    GitIdentityCreate,
    GitIdentityResponse,
)
from app.services.user import user_service
from app.api.deps import get_current_user, require_commissioner
from app.models.user import User, UserRole, UserStatus

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_commissioner)],
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    status: Optional[UserStatus] = Query(None, description="Filter by status"),
):
    """
    List all users (Commissioner only).

    Supports pagination and filtering:
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 50, max: 100)
    - **role**: Filter by role (commissioner, player, spectator)
    - **status**: Filter by status (approved, pending, retired)
    """
    skip = (page - 1) * limit
    users, total = user_service.get_users(
        db=db,
        skip=skip,
        limit=limit,
        role=role,
        status=status,
    )

    pages = (total + limit - 1) // limit

    return {
        "items": users,
        "total": total,
        "page": page,
        "pages": pages,
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get user by ID.

    Any authenticated user can view user profiles.
    """
    from fastapi import HTTPException, status

    user = user_service.get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_commissioner)],
):
    """
    Update user (Commissioner only).

    Can update:
    - **role**: User role (commissioner, player, spectator)
    - **status**: User status (approved, pending, retired)
    - **display_name**: User display name
    """
    return user_service.update_user(
        user_id=user_id,
        user_update=user_update,
        db=db,
        current_user=current_user,
    )


@router.post("/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_commissioner)],
):
    """
    Approve a pending user (Commissioner only).

    Changes user status from 'pending' to 'approved'.
    Creates an audit log entry.
    """
    return user_service.approve_user(
        user_id=user_id,
        db=db,
        current_user=current_user,
    )


@router.post("/{user_id}/git-identities", response_model=GitIdentityResponse)
async def add_git_identity(
    user_id: str,
    git_identity: GitIdentityCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Add a Git identity to a user.

    Users can add identities to their own account.
    Commissioners can add identities to any user.

    - **git_name**: Name used in Git commits (optional)
    - **git_email**: Email used in Git commits (required)
    """
    from fastapi import HTTPException, status

    # Users can only add identities to themselves unless they're a Commissioner
    if current_user.id != user_id and current_user.role != UserRole.COMMISSIONER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add Git identities to your own account",
        )

    return user_service.add_git_identity(
        user_id=user_id,
        git_identity=git_identity,
        db=db,
    )
