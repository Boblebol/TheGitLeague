"""API Key service."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.api_key import APIKey, APIKeyStatus, APIKeyScope
from app.models.user import User, AuditLog
from app.core.security import hash_password, verify_password


class APIKeyService:
    """Service for API key operations."""

    def generate_api_key(self) -> Tuple[str, str, str]:
        """
        Generate a new API key with format: tgl_{prefix_8chars}_{secret_32chars}

        Returns:
            Tuple of (full_key, prefix, secret)
        """
        prefix_random = secrets.token_urlsafe(6)[:8]  # 8 chars
        prefix = f"tgl_{prefix_random}"

        secret = secrets.token_urlsafe(24)  # ~32 chars base64
        full_key = f"{prefix}_{secret}"

        return full_key, prefix, secret

    def create_api_key(
        self,
        name: str,
        scopes: APIKeyScope,
        user: User,
        db: Session,
        expires_in_days: Optional[int] = None,
    ) -> Tuple[APIKey, str]:
        """
        Create a new API key.

        Args:
            name: User-friendly name for the key
            scopes: API key scopes
            user: User creating the key
            db: Database session
            expires_in_days: Optional expiration in days

        Returns:
            Tuple of (APIKey object, full_key_plaintext)

        Note:
            The full key is returned only once and must be saved by the client.
        """
        # Generate key
        full_key, prefix, secret = self.generate_api_key()

        # Hash the full key for storage
        key_hash = hash_password(full_key)

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        # Create API key record
        api_key = APIKey(
            user_id=user.id,
            name=name,
            prefix=prefix,
            key_hash=key_hash,
            scopes=scopes,
            status=APIKeyStatus.ACTIVE,
            expires_at=expires_at,
        )

        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action="create_api_key",
            resource_type="api_key",
            resource_id=api_key.id,
            details=f"Created API key '{name}' with prefix {prefix}",
        )
        db.add(audit)
        db.commit()

        return api_key, full_key

    def list_api_keys(
        self,
        user: User,
        db: Session,
        include_revoked: bool = False,
    ) -> List[APIKey]:
        """
        List API keys for a user.

        Args:
            user: User to list keys for
            db: Database session
            include_revoked: Include revoked keys

        Returns:
            List of APIKey objects
        """
        query = db.query(APIKey).filter(APIKey.user_id == user.id)

        if not include_revoked:
            query = query.filter(APIKey.status == APIKeyStatus.ACTIVE)

        return query.order_by(APIKey.created_at.desc()).all()

    def revoke_api_key(
        self,
        api_key_id: str,
        user: User,
        db: Session,
    ) -> APIKey:
        """
        Revoke an API key.

        Args:
            api_key_id: API key ID to revoke
            user: User revoking the key
            db: Database session

        Returns:
            Revoked APIKey object

        Raises:
            HTTPException: If key not found or not owned by user
        """
        api_key = db.query(APIKey).filter(
            APIKey.id == api_key_id,
            APIKey.user_id == user.id,
        ).first()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
            )

        if api_key.status == APIKeyStatus.REVOKED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key already revoked",
            )

        # Revoke key
        api_key.status = APIKeyStatus.REVOKED
        api_key.revoked_at = datetime.now(timezone.utc)
        db.commit()

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action="revoke_api_key",
            resource_type="api_key",
            resource_id=api_key.id,
            details=f"Revoked API key '{api_key.name}' ({api_key.prefix})",
        )
        db.add(audit)
        db.commit()

        return api_key

    def verify_api_key(
        self,
        full_key: str,
        db: Session,
        ip_address: Optional[str] = None,
    ) -> Optional[User]:
        """
        Verify an API key and return associated user.

        Args:
            full_key: Full API key (tgl_xxxxxxxx_yyyyyy...)
            db: Database session
            ip_address: Optional IP address for tracking

        Returns:
            User if valid, None otherwise
        """
        # Extract prefix
        parts = full_key.split("_", 2)
        if len(parts) != 3 or parts[0] != "tgl":
            return None

        prefix = f"tgl_{parts[1]}"

        # Find key by prefix
        api_key = db.query(APIKey).filter(
            APIKey.prefix == prefix,
            APIKey.status == APIKeyStatus.ACTIVE,
        ).first()

        if not api_key:
            return None

        # Check expiration
        # Note: Handle both aware and naive datetimes for DB compatibility
        if api_key.expires_at:
            now_utc = datetime.now(timezone.utc)
            # If expires_at is naive (e.g., from SQLite), compare without timezone
            if api_key.expires_at.tzinfo is None:
                now_utc = now_utc.replace(tzinfo=None)
            if api_key.expires_at < now_utc:
                return None

        # Verify hash
        if not verify_password(full_key, api_key.key_hash):
            return None

        # Update usage tracking
        api_key.last_used_at = datetime.now(timezone.utc)
        api_key.usage_count += 1
        if ip_address:
            api_key.last_used_ip = ip_address
        db.commit()

        # Return associated user
        return api_key.user


# Singleton instance
api_key_service = APIKeyService()
