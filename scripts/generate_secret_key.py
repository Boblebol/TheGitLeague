#!/usr/bin/env python3
"""Generate a secure secret key for JWT tokens."""

import secrets

if __name__ == "__main__":
    secret_key = secrets.token_urlsafe(32)
    print("Generated SECRET_KEY:")
    print(secret_key)
    print("\nAdd this to your .env file:")
    print(f"SECRET_KEY={secret_key}")
