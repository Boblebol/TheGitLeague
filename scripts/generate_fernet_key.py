#!/usr/bin/env python3
"""Generate a Fernet key for encrypting repository credentials."""

from cryptography.fernet import Fernet

if __name__ == "__main__":
    fernet_key = Fernet.generate_key().decode()
    print("Generated FERNET_KEY:")
    print(fernet_key)
    print("\nAdd this to your .env file:")
    print(f"FERNET_KEY={fernet_key}")
