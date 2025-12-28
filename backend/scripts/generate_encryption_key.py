#!/usr/bin/env python3
"""
Utility script to generate a Fernet encryption master key.

Usage:
    python backend/scripts/generate_encryption_key.py

This script generates a secure random Fernet key for encrypting repository credentials.
The generated key should be stored in the ENCRYPTION_MASTER_KEY environment variable.

⚠️  SECURITY WARNING:
    - NEVER commit the generated key to Git
    - Store it securely (environment variable, secret manager, or .env file with 600 permissions)
    - If you lose this key, all encrypted credentials will be irrecoverable
    - Backup the key in a secure location (Vault, 1Password, etc.)
"""

from cryptography.fernet import Fernet


def generate_master_key():
    """Generate and display a new Fernet master key."""
    key = Fernet.generate_key()
    key_str = key.decode('utf-8')

    print("=" * 80)
    print("🔑  ENCRYPTION MASTER KEY GENERATED")
    print("=" * 80)
    print()
    print(f"ENCRYPTION_MASTER_KEY={key_str}")
    print()
    print("=" * 80)
    print("⚠️   IMPORTANT SECURITY INSTRUCTIONS")
    print("=" * 80)
    print()
    print("1. Add this key to your .env file:")
    print(f"   echo 'ENCRYPTION_MASTER_KEY={key_str}' >> .env")
    print()
    print("2. Set file permissions to owner-only:")
    print("   chmod 600 .env")
    print()
    print("3. Ensure .env is in .gitignore:")
    print("   echo '.env' >> .gitignore")
    print()
    print("4. Backup the key securely:")
    print("   • Password manager (1Password, Bitwarden, etc.)")
    print("   • Secret manager (Vault, AWS Secrets Manager, etc.)")
    print("   • Offline backup in a secure location")
    print()
    print("5. NEVER:")
    print("   ❌ Commit this key to Git")
    print("   ❌ Share it in plain text (email, Slack, etc.)")
    print("   ❌ Log it in application logs")
    print("   ❌ Expose it in API responses")
    print()
    print("=" * 80)
    print("💡  KEY PROPERTIES")
    print("=" * 80)
    print()
    print(f"• Length: {len(key_str)} characters (base64-encoded)")
    print("• Algorithm: Fernet (AES-128-CBC + HMAC-SHA256)")
    print("• Use case: Encrypting PAT tokens and other repository credentials")
    print()
    print("If you lose this key, you will need to:")
    print("  1. Generate a new key")
    print("  2. Re-create all PAT tokens on GitHub/GitLab")
    print("  3. Re-configure all repositories with new credentials")
    print()
    print("=" * 80)


if __name__ == "__main__":
    generate_master_key()
