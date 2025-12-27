"""Security utilities for authentication and authorization."""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT algorithm
ALGORITHM = "HS256"


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_magic_link_token(
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a magic link token.

    Args:
        email: User email
        expires_delta: Optional expiration time delta

    Returns:
        Magic link token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.MAGIC_LINK_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": email,
        "type": "magic_link",
        "exp": expire,
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify

    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_random_token(length: int = 32) -> str:
    """
    Generate a random URL-safe token.

    Args:
        length: Token length

    Returns:
        Random token string
    """
    return secrets.token_urlsafe(length)


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_fernet_cipher() -> Fernet:
    """
    Get Fernet cipher for encryption/decryption.

    Returns:
        Fernet cipher instance
    """
    if not settings.FERNET_KEY:
        raise ValueError("FERNET_KEY not configured")

    return Fernet(settings.FERNET_KEY.encode())


def encrypt_credentials(data: str) -> str:
    """
    Encrypt sensitive data (like repository credentials).

    Args:
        data: Plain text data to encrypt

    Returns:
        Encrypted data (base64 encoded)
    """
    cipher = get_fernet_cipher()
    encrypted = cipher.encrypt(data.encode())
    return encrypted.decode()


def decrypt_credentials(encrypted_data: str) -> str:
    """
    Decrypt sensitive data.

    Args:
        encrypted_data: Encrypted data (base64 encoded)

    Returns:
        Decrypted plain text data
    """
    cipher = get_fernet_cipher()
    decrypted = cipher.decrypt(encrypted_data.encode())
    return decrypted.decode()
