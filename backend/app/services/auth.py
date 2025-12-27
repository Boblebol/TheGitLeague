"""Authentication service."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, GitIdentity, MagicLinkToken, UserRole, UserStatus
from app.core.security import (
    create_access_token,
    create_magic_link_token,
    verify_token,
)
from app.core.config import settings
from app.services.email import email_service


class AuthService:
    """Service for authentication operations."""

    async def request_magic_link(
        self,
        email: str,
        db: Session,
        base_url: str = "http://localhost:3000",
    ) -> dict:
        """
        Request a magic link for passwordless authentication.

        Args:
            email: User email
            db: Database session
            base_url: Base URL for the magic link

        Returns:
            Dictionary with message and expiration info
        """
        # Normalize email
        email = email.lower().strip()

        # Check if user exists, create if not
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create new user (pending approval if spectator)
            user = User(
                email=email,
                role=UserRole.PLAYER,
                status=UserStatus.PENDING,
                display_name=email.split("@")[0],
            )
            db.add(user)
            db.flush()

            # Auto-approve first user as Commissioner
            if db.query(User).count() == 1:
                user.role = UserRole.COMMISSIONER
                user.status = UserStatus.APPROVED

        # Generate magic link token
        token = create_magic_link_token(email)
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.MAGIC_LINK_EXPIRE_MINUTES
        )

        # Store token in database
        magic_link = MagicLinkToken(
            email=email,
            token=token,
            expires_at=expires_at,
        )
        db.add(magic_link)
        db.commit()

        # Send magic link email
        magic_link_url = f"{base_url}/auth/verify?token={token}"
        await email_service.send_magic_link(
            to_email=email,
            magic_link=magic_link_url,
            expires_in_minutes=settings.MAGIC_LINK_EXPIRE_MINUTES,
        )

        return {
            "message": f"Magic link sent to {email}",
            "expires_in": settings.MAGIC_LINK_EXPIRE_MINUTES * 60,  # Convert to seconds
        }

    async def verify_magic_link(
        self,
        token: str,
        db: Session,
    ) -> dict:
        """
        Verify a magic link token and return access token.

        Args:
            token: Magic link token
            db: Database session

        Returns:
            Dictionary with access token and user info

        Raises:
            HTTPException: If token is invalid or expired
        """
        # Verify token structure
        payload = verify_token(token)
        if not payload or payload.get("type") != "magic_link":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Check token in database
        magic_link = (
            db.query(MagicLinkToken)
            .filter(
                MagicLinkToken.token == token,
                MagicLinkToken.email == email,
                MagicLinkToken.used == False,
            )
            .first()
        )

        if not magic_link:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token already used or invalid",
            )

        # Check expiration
        if magic_link.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )

        # Mark token as used
        magic_link.used = True
        db.commit()

        # Get user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Check if user is approved
        if user.status != UserStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is pending approval",
            )

        # Create access token
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "role": user.role,
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user,
        }

    def get_current_user(
        self,
        token: str,
        db: Session,
    ) -> User:
        """
        Get current authenticated user from token.

        Args:
            token: JWT access token
            db: Database session

        Returns:
            Current user

        Raises:
            HTTPException: If token is invalid or user not found
        """
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    def auto_associate_git_identity(
        self,
        user: User,
        db: Session,
    ) -> None:
        """
        Auto-associate Git identity based on user email.

        Args:
            user: User to associate identity with
            db: Database session
        """
        # Check if identity already exists
        existing = (
            db.query(GitIdentity)
            .filter(
                GitIdentity.user_id == user.id,
                GitIdentity.git_email == user.email,
            )
            .first()
        )

        if not existing:
            git_identity = GitIdentity(
                user_id=user.id,
                git_email=user.email,
                git_name=user.display_name,
            )
            db.add(git_identity)
            db.commit()


# Singleton instance
auth_service = AuthService()
