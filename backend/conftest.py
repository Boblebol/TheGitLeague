"""Root conftest - sets up test environment before any imports."""

import os
import sys

# Set test database URL BEFORE any app imports
os.environ['DATABASE_URL'] = "sqlite:///:memory:"
os.environ['FERNET_KEY'] = "WFHffd2vqVEIFLvj9DlvkrqyYLTNjm3XZl3SqnPJzYQ="  # Valid test key
os.environ['SECRET_KEY'] = "test-secret-key-min-32-characters-long-12345"
