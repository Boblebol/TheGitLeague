"""
Encryption module for secure credential management.

Uses Fernet (AES-128-CBC + HMAC-SHA256) for symmetric encryption of sensitive data
like Personal Access Tokens (PAT), SSH keys, and other repository credentials.

Security principles:
- Encryption at-rest for all credentials
- Master key stored in environment variables
- No credentials logged or exposed in API responses
- Memory cleared after decryption use
"""

import json
import logging
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption/decryption operations fail."""
    pass


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive credentials.

    Uses Fernet symmetric encryption with a master key from environment.
    Supports key rotation via encryption_key_id versioning.
    """

    def __init__(self, master_key: str, key_version: str = "v1"):
        """
        Initialize the encryption service.

        Args:
            master_key: Base64-encoded Fernet key from ENCRYPTION_MASTER_KEY env var
            key_version: Version identifier for key rotation (default: "v1")

        Raises:
            EncryptionError: If master_key is invalid or missing
        """
        if not master_key:
            raise EncryptionError("Master encryption key is required")

        try:
            # Validate and create Fernet cipher
            self.cipher = Fernet(master_key.encode())
            self.key_version = key_version
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise EncryptionError(f"Invalid master key: {e}")

    def encrypt_credentials(
        self,
        credentials: Dict[str, Any],
        credential_type: str = "pat"
    ) -> Dict[str, Any]:
        """
        Encrypt credentials for storage in database.

        Args:
            credentials: Dictionary containing sensitive data (token, username, etc.)
            credential_type: Type of credential ("pat", "ssh", etc.)

        Returns:
            Dictionary with encrypted_data, algorithm, and key_version

        Example:
            Input:  {"token": "ghp_xxx...", "username": "git"}
            Output: {
                "type": "pat",
                "encrypted_data": "gAAAAABl...",
                "algorithm": "fernet",
                "key_version": "v1"
            }
        """
        try:
            # Serialize credentials to JSON
            plaintext = json.dumps(credentials).encode('utf-8')

            # Encrypt
            encrypted_bytes = self.cipher.encrypt(plaintext)
            encrypted_b64 = encrypted_bytes.decode('utf-8')

            # Return structured encrypted data
            return {
                "type": credential_type,
                "encrypted_data": encrypted_b64,
                "algorithm": "fernet",
                "key_version": self.key_version
            }

        except Exception as e:
            logger.error(f"Encryption failed: {e}", exc_info=True)
            raise EncryptionError(f"Failed to encrypt credentials: {e}")

    def decrypt_credentials(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt credentials from database storage.

        Args:
            encrypted_data: Dictionary with encrypted_data, algorithm, key_version

        Returns:
            Decrypted credentials dictionary

        Raises:
            EncryptionError: If decryption fails or data is corrupted

        Security notes:
            - Only call this when credentials are needed (e.g., Git sync)
            - Clear decrypted data from memory after use (caller's responsibility)
            - Never log or expose decrypted credentials
        """
        try:
            # Validate structure
            if "encrypted_data" not in encrypted_data:
                raise EncryptionError("Missing encrypted_data field")

            # Check key version for rotation support
            stored_version = encrypted_data.get("key_version", "v1")
            if stored_version != self.key_version:
                logger.warning(
                    f"Key version mismatch: stored={stored_version}, current={self.key_version}"
                )
                # In V1, we only support one key. In phase 2, lookup the right key here.

            # Decrypt
            encrypted_b64 = encrypted_data["encrypted_data"]
            encrypted_bytes = encrypted_b64.encode('utf-8')
            plaintext_bytes = self.cipher.decrypt(encrypted_bytes)

            # Deserialize
            credentials = json.loads(plaintext_bytes.decode('utf-8'))

            return credentials

        except InvalidToken:
            logger.error("Invalid token: data may be corrupted or key is wrong")
            raise EncryptionError("Failed to decrypt: invalid token or corrupted data")
        except json.JSONDecodeError as e:
            logger.error(f"Decrypted data is not valid JSON: {e}")
            raise EncryptionError("Decrypted data is corrupted")
        except Exception as e:
            logger.error(f"Decryption failed: {e}", exc_info=True)
            raise EncryptionError(f"Failed to decrypt credentials: {e}")

    def encrypt_pat_token(self, token: str, username: str = "git") -> Dict[str, Any]:
        """
        Convenience method for encrypting a Personal Access Token.

        Args:
            token: PAT token (e.g., "ghp_xxx...")
            username: Username for HTTPS auth (default: "git")

        Returns:
            Encrypted credentials ready for database storage
        """
        credentials = {
            "token": token,
            "username": username
        }
        return self.encrypt_credentials(credentials, credential_type="pat")

    def decrypt_pat_token(self, encrypted_data: Dict[str, Any]) -> tuple[str, str]:
        """
        Convenience method for decrypting a Personal Access Token.

        Args:
            encrypted_data: Encrypted credentials from database

        Returns:
            Tuple of (token, username)

        Security warning:
            Clear the returned token from memory after use!
            Use: `del token` when done.
        """
        credentials = self.decrypt_credentials(encrypted_data)
        token = credentials.get("token", "")
        username = credentials.get("username", "git")
        return token, username

    @staticmethod
    def generate_master_key() -> str:
        """
        Generate a new Fernet master key.

        Returns:
            Base64-encoded key string

        Note:
            This should only be used during initial setup.
            Store the generated key securely in ENCRYPTION_MASTER_KEY env var.
        """
        return Fernet.generate_key().decode('utf-8')

    def rotate_credentials(
        self,
        old_encrypted_data: Dict[str, Any],
        new_encryption_service: 'EncryptionService'
    ) -> Dict[str, Any]:
        """
        Re-encrypt credentials with a new key (for key rotation).

        Args:
            old_encrypted_data: Credentials encrypted with old key
            new_encryption_service: New EncryptionService with new master key

        Returns:
            Credentials re-encrypted with new key

        Usage:
            old_service = EncryptionService(old_key, "v1")
            new_service = EncryptionService(new_key, "v2")
            new_data = old_service.rotate_credentials(old_data, new_service)
        """
        # Decrypt with old key
        plaintext_creds = self.decrypt_credentials(old_encrypted_data)

        # Re-encrypt with new key
        credential_type = old_encrypted_data.get("type", "pat")
        new_encrypted_data = new_encryption_service.encrypt_credentials(
            plaintext_creds,
            credential_type=credential_type
        )

        # Clear plaintext from memory
        plaintext_creds.clear()

        return new_encrypted_data


def mask_token(token: str, visible_chars: int = 4) -> str:
    """
    Mask a token for safe logging/display.

    Args:
        token: Full token string
        visible_chars: Number of characters to show at start and end

    Returns:
        Masked token (e.g., "ghp_****...****abc")
    """
    if len(token) <= visible_chars * 2:
        return "*" * len(token)

    start = token[:visible_chars]
    end = token[-visible_chars:]
    return f"{start}****...****{end}"
