"""User service."""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, GitIdentity, UserRole, UserStatus, AuditLog
from app.schemas.user import UserCreate, UserUpdate, GitIdentityCreate


class UserService:
    """Service for user operations."""

    def get_users(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
    ) -> tuple[List[User], int]:
        """
        Get list of users with optional filters.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Optional role filter
            status: Optional status filter

        Returns:
            Tuple of (users list, total count)
        """
        query = db.query(User)

        if role:
            query = query.filter(User.role == role)
        if status:
            query = query.filter(User.status == status)

        total = query.count()
        users = query.offset(skip).limit(limit).all()

        return users, total

    def get_user_by_id(
        self,
        user_id: str,
        db: Session,
    ) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            User or None if not found
        """
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(
        self,
        email: str,
        db: Session,
    ) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email
            db: Database session

        Returns:
            User or None if not found
        """
        return db.query(User).filter(User.email == email.lower()).first()

    def update_user(
        self,
        user_id: str,
        user_update: UserUpdate,
        db: Session,
        current_user: User,
    ) -> User:
        """
        Update user.

        Args:
            user_id: User ID to update
            user_update: Update data
            db: Database session
            current_user: Current authenticated user (for audit)

        Returns:
            Updated user

        Raises:
            HTTPException: If user not found
        """
        user = self.get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="update_user",
            resource_type="user",
            resource_id=user_id,
            details=f"Updated user {user.email}",
        )
        db.add(audit)
        db.commit()

        return user

    def add_git_identity(
        self,
        user_id: str,
        git_identity: GitIdentityCreate,
        db: Session,
    ) -> GitIdentity:
        """
        Add Git identity to user.

        Args:
            user_id: User ID
            git_identity: Git identity data
            db: Database session

        Returns:
            Created GitIdentity

        Raises:
            HTTPException: If user not found or identity already exists
        """
        user = self.get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Check if identity already exists
        existing = (
            db.query(GitIdentity)
            .filter(
                GitIdentity.user_id == user_id,
                GitIdentity.git_email == git_identity.git_email.lower(),
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Git identity already exists for this user",
            )

        # Create new identity
        new_identity = GitIdentity(
            user_id=user_id,
            git_name=git_identity.git_name,
            git_email=git_identity.git_email.lower(),
        )

        db.add(new_identity)
        db.commit()
        db.refresh(new_identity)

        return new_identity

    def approve_user(
        self,
        user_id: str,
        db: Session,
        current_user: User,
    ) -> User:
        """
        Approve a pending user (Commissioner only).

        Args:
            user_id: User ID to approve
            db: Database session
            current_user: Current authenticated user (must be Commissioner)

        Returns:
            Approved user

        Raises:
            HTTPException: If user not found or current user is not Commissioner
        """
        user = self.get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.status != UserStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not pending approval",
            )

        user.status = UserStatus.APPROVED
        db.commit()
        db.refresh(user)

        # Create audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="approve_user",
            resource_type="user",
            resource_id=user_id,
            details=f"Approved user {user.email}",
        )
        db.add(audit)
        db.commit()

        return user


# Singleton instance
user_service = UserService()
