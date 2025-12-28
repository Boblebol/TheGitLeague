"""
Unit tests for encryption module.

Tests PAT token encryption/decryption and security features.
"""

import pytest
from cryptography.fernet import Fernet

from backend.core.encryption import EncryptionService, EncryptionError, mask_token


class TestEncryptionService:
    """Test suite for EncryptionService."""

    @pytest.fixture
    def master_key(self) -> str:
        """Generate a test master key."""
        return Fernet.generate_key().decode('utf-8')

    @pytest.fixture
    def encryption_service(self, master_key: str) -> EncryptionService:
        """Create encryption service with test key."""
        return EncryptionService(master_key=master_key, key_version="v1")

    def test_generate_master_key(self):
        """Test master key generation."""
        key = EncryptionService.generate_master_key()

        assert isinstance(key, str)
        assert len(key) == 44  # Fernet keys are 44 characters base64
        # Should be valid Fernet key
        Fernet(key.encode())

    def test_encrypt_decrypt_pat_token(self, encryption_service: EncryptionService):
        """Test PAT token encryption and decryption."""
        # Test data
        token = "ghp_test1234567890abcdefghijklmnopqrst"
        username = "git"

        # Encrypt
        encrypted_data = encryption_service.encrypt_pat_token(token, username)

        assert encrypted_data["type"] == "pat"
        assert encrypted_data["algorithm"] == "fernet"
        assert encrypted_data["key_version"] == "v1"
        assert "encrypted_data" in encrypted_data
        # Encrypted data should be different from plaintext
        assert encrypted_data["encrypted_data"] != token

        # Decrypt
        decrypted_token, decrypted_username = encryption_service.decrypt_pat_token(
            encrypted_data
        )

        assert decrypted_token == token
        assert decrypted_username == username

    def test_encrypt_credentials_generic(self, encryption_service: EncryptionService):
        """Test generic credential encryption."""
        credentials = {
            "token": "secret_token_123",
            "username": "testuser",
            "extra_field": "some_value"
        }

        # Encrypt
        encrypted_data = encryption_service.encrypt_credentials(
            credentials,
            credential_type="custom"
        )

        assert encrypted_data["type"] == "custom"
        assert "encrypted_data" in encrypted_data

        # Decrypt
        decrypted_creds = encryption_service.decrypt_credentials(encrypted_data)

        assert decrypted_creds == credentials

    def test_encryption_with_different_keys(self):
        """Test that different keys produce different encrypted data."""
        key1 = Fernet.generate_key().decode('utf-8')
        key2 = Fernet.generate_key().decode('utf-8')

        service1 = EncryptionService(master_key=key1)
        service2 = EncryptionService(master_key=key2)

        token = "ghp_test_token"

        encrypted1 = service1.encrypt_pat_token(token)
        encrypted2 = service2.encrypt_pat_token(token)

        # Different keys should produce different encrypted data
        assert encrypted1["encrypted_data"] != encrypted2["encrypted_data"]

    def test_decryption_with_wrong_key_fails(self):
        """Test that decryption fails with wrong key."""
        key1 = Fernet.generate_key().decode('utf-8')
        key2 = Fernet.generate_key().decode('utf-8')

        service1 = EncryptionService(master_key=key1)
        service2 = EncryptionService(master_key=key2)

        token = "ghp_test_token"

        # Encrypt with key1
        encrypted_data = service1.encrypt_pat_token(token)

        # Try to decrypt with key2 (should fail)
        with pytest.raises(EncryptionError) as exc_info:
            service2.decrypt_pat_token(encrypted_data)

        assert "invalid token" in str(exc_info.value).lower()

    def test_invalid_master_key(self):
        """Test that invalid master key raises error."""
        with pytest.raises(EncryptionError) as exc_info:
            EncryptionService(master_key="invalid_key")

        assert "invalid master key" in str(exc_info.value).lower()

    def test_empty_master_key(self):
        """Test that empty master key raises error."""
        with pytest.raises(EncryptionError) as exc_info:
            EncryptionService(master_key="")

        assert "required" in str(exc_info.value).lower()

    def test_key_rotation(self):
        """Test credential re-encryption for key rotation."""
        old_key = Fernet.generate_key().decode('utf-8')
        new_key = Fernet.generate_key().decode('utf-8')

        old_service = EncryptionService(master_key=old_key, key_version="v1")
        new_service = EncryptionService(master_key=new_key, key_version="v2")

        token = "ghp_original_token"

        # Encrypt with old key
        old_encrypted = old_service.encrypt_pat_token(token)
        assert old_encrypted["key_version"] == "v1"

        # Rotate to new key
        new_encrypted = old_service.rotate_credentials(old_encrypted, new_service)
        assert new_encrypted["key_version"] == "v2"

        # Decrypt with new key
        decrypted_token, _ = new_service.decrypt_pat_token(new_encrypted)
        assert decrypted_token == token

    def test_corrupted_data_decryption_fails(self, encryption_service: EncryptionService):
        """Test that corrupted encrypted data fails decryption."""
        token = "ghp_test_token"
        encrypted_data = encryption_service.encrypt_pat_token(token)

        # Corrupt the encrypted data
        corrupted_data = encrypted_data.copy()
        corrupted_data["encrypted_data"] = "corrupted_base64_data_xxx"

        # Should fail to decrypt
        with pytest.raises(EncryptionError):
            encryption_service.decrypt_pat_token(corrupted_data)

    def test_missing_encrypted_data_field(self, encryption_service: EncryptionService):
        """Test that missing encrypted_data field raises error."""
        invalid_data = {
            "type": "pat",
            "algorithm": "fernet",
            # Missing "encrypted_data"
        }

        with pytest.raises(EncryptionError) as exc_info:
            encryption_service.decrypt_credentials(invalid_data)

        assert "missing encrypted_data" in str(exc_info.value).lower()


class TestMaskToken:
    """Test suite for mask_token utility."""

    def test_mask_long_token(self):
        """Test masking a long token."""
        token = "ghp_1234567890abcdefghijklmnopqrst"
        masked = mask_token(token, visible_chars=4)

        assert masked == "ghp_****...****qrst"
        assert len(masked) < len(token)

    def test_mask_short_token(self):
        """Test masking a short token."""
        token = "short"
        masked = mask_token(token, visible_chars=4)

        # Too short to show any characters
        assert masked == "*" * len(token)

    def test_mask_token_custom_visible_chars(self):
        """Test masking with custom visible characters."""
        token = "ghp_1234567890abcdefghijklmnopqrst"
        masked = mask_token(token, visible_chars=8)

        assert masked.startswith("ghp_1234")
        assert masked.endswith("opqrst")
        assert "****...****" in masked


# Run tests with: pytest backend/tests/test_encryption.py -v
