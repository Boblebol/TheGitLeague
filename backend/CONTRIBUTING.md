# Contributing to TheGitLeague Backend

We welcome and appreciate contributions! This document provides guidelines and instructions for contributing to the TheGitLeague Backend project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)
- [Project Structure](#project-structure)
- [Common Tasks](#common-tasks)
- [Questions & Support](#questions--support)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inclusive environment for all contributors.

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 12+ (for full testing) or SQLite (for quick testing)
- Git
- pip or poetry

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/tgitleague-backend.git
   cd tgitleague-backend
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/original-owner/tgitleague-backend.git
   ```

## Development Setup

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Install Development Dependencies

```bash
# Install package with dev dependencies
pip install -e ".[dev]"

# Or install individual dev tools
pip install pytest pytest-cov pytest-asyncio
pip install black ruff mypy
pip install pre-commit
```

### Setup Pre-commit Hooks

```bash
pre-commit install
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your local configuration
```

### Create Database (Development)

```bash
# For PostgreSQL
createdb tgitleague_dev
alembic upgrade head

# For SQLite (testing)
# No setup needed - uses in-memory database in tests
```

## Making Changes

### Create a Branch

Create a feature branch for your changes:

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

**Branch Naming Convention:**
- Features: `feature/add-api-endpoint`
- Bug fixes: `bugfix/fix-datetime-issue`
- Documentation: `docs/update-migration-guide`
- Security: `security/validate-api-key`
- Performance: `perf/optimize-database-queries`

### Code Style

#### Python Formatting

We use **Black** for code formatting:

```bash
# Format all code
black app/ tests/ scripts/

# Check formatting (CI runs this)
black --check app/ tests/ scripts/
```

#### Linting

We use **Ruff** for linting:

```bash
# Check for issues
ruff check app/ tests/ scripts/

# Fix issues automatically
ruff check --fix app/ tests/ scripts/
```

#### Type Checking

We use **mypy** for type checking:

```bash
# Check types
mypy app/

# Common issues:
# - Missing type hints on function parameters/returns
# - Incompatible type assignments
# - Optional type handling
```

### Code Standards

#### Type Hints

All code should include type hints:

```python
# Good
def create_api_key(
    name: str,
    scopes: str,
    user: User,
    db: Session,
    expires_in_days: Optional[int] = None
) -> tuple[APIKey, str]:
    """Create a new API key for the user."""
    ...

# Bad
def create_api_key(name, scopes, user, db, expires_in_days=None):
    ...
```

#### Docstrings

Use docstrings for modules, classes, and functions:

```python
"""Module docstring describing the purpose of this module."""

class APIKeyService:
    """Service for managing API keys."""

    def create_api_key(
        self,
        name: str,
        scopes: str,
        user: User,
        db: Session,
        expires_in_days: Optional[int] = None
    ) -> tuple[APIKey, str]:
        """Create a new API key for the user.

        Args:
            name: Human-readable name for the API key
            scopes: Comma-separated list of scopes (e.g., "sync:commits,read:repos")
            user: User object creating the key
            db: Database session
            expires_in_days: Optional expiration in days

        Returns:
            Tuple of (APIKey object, full_key string)

        Raises:
            ValueError: If scopes are invalid
        """
        ...
```

#### Error Handling

Use specific exception types:

```python
# Good
if not user.is_commissioner:
    raise ValueError("Only commissioners can create API keys")

# Bad
if not user.is_commissioner:
    raise Exception("Error")
```

#### Imports

- Group imports: standard library, third-party, local
- Use absolute imports
- Keep imports alphabetical within groups

```python
# Good
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.api_key import APIKey
from app.services.api_key import APIKeyService
```

## Testing

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_api_keys.py

# Specific test class
pytest tests/test_api_keys.py::TestAPIKeyService

# Specific test function
pytest tests/test_api_keys.py::TestAPIKeyService::test_create_api_key

# With verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Writing Tests

Test structure:

```python
"""Tests for API key service."""

import pytest
from datetime import datetime, timezone

from app.models.api_key import APIKey
from app.services.api_key import APIKeyService


class TestAPIKeyService:
    """Test cases for APIKeyService."""

    def test_create_api_key_success(self, db_session, test_user):
        """Test successful API key creation."""
        # Arrange
        service = APIKeyService()

        # Act
        api_key, full_key = service.create_api_key(
            name="Test Key",
            scopes="sync:commits,read:repos",
            user=test_user,
            db=db_session
        )

        # Assert
        assert api_key.name == "Test Key"
        assert api_key.prefix.startswith("tgl_")
        assert len(full_key) > 40  # Format: tgl_xxxxxxxx_secret
        assert api_key.user_id == test_user.id

    def test_create_api_key_invalid_scope(self, db_session, test_user):
        """Test API key creation with invalid scope."""
        service = APIKeyService()

        with pytest.raises(ValueError, match="Invalid scopes"):
            service.create_api_key(
                name="Bad Key",
                scopes="invalid:scope",
                user=test_user,
                db=db_session
            )
```

### Test Coverage

Aim for high coverage, especially for:
- Critical paths (authentication, data validation)
- Error conditions
- Edge cases

Target: **80%+ coverage**

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=term-missing
```

### Fixtures

Use pytest fixtures for common test setup:

```python
# conftest.py
@pytest.fixture
def test_user(db_session) -> User:
    """Create a test user."""
    user = User(
        id="test-user-123",
        email="test@example.com",
        username="testuser",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user

# In test files
def test_something(test_user):
    assert test_user.email == "test@example.com"
```

## Code Quality

### Pre-commit Checks

Run these before committing:

```bash
# Format code
black app/ tests/ scripts/

# Lint code
ruff check --fix app/ tests/ scripts/

# Type check
mypy app/

# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=app --cov-report=term-missing
```

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration. All checks must pass:

- ✅ Black formatting
- ✅ Ruff linting
- ✅ mypy type checking
- ✅ pytest test suite
- ✅ Coverage thresholds

## Commit Messages

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without feature changes
- **perf**: Performance improvements
- **test**: Adding/updating tests
- **chore**: Build, dependencies, etc.
- **security**: Security fixes or improvements

### Scope

Scope of the change:

- `api-keys` - API key functionality
- `sync` - Commit synchronization
- `client` - Python client
- `migration` - Repository migration
- `db` - Database changes
- `auth` - Authentication
- `docs` - Documentation

### Subject

- Use imperative mood ("add", not "added" or "adds")
- Don't capitalize first letter
- No period at the end
- Max 50 characters

### Body

- Explain *what* and *why*, not *how*
- Wrap at 72 characters
- Reference issues and pull requests

### Examples

```
feat(api-keys): add API key expiration support

Add optional expires_at field to API keys. Expired keys are automatically
rejected during verification. Includes validation and audit logging.

Fixes #123
```

```
fix(sync): handle duplicate commits correctly

Skip commits with duplicate SHA instead of throwing error. Return
per-commit status in response indicating whether each commit was
inserted, skipped, or had an error.

Closes #456
```

```
docs: update migration guide with troubleshooting section

Add common issues and solutions for the migration process including
API key problems, connection timeouts, and sync failures.
```

## Pull Requests

### Before Submitting

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run quality checks**:
   ```bash
   black app/ tests/ scripts/
   ruff check --fix app/ tests/ scripts/
   mypy app/
   pytest tests/ --cov=app
   ```

3. **Test locally**:
   ```bash
   pytest tests/ -v
   ```

### Creating a Pull Request

1. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open PR on GitHub with:
   - Clear title (follow commit message conventions)
   - Description of changes
   - Reference related issues
   - Screenshots/examples if applicable

### PR Template

```markdown
## Description

Brief description of the changes.

## Type of Change

- [ ] New feature
- [ ] Bug fix
- [ ] Breaking change
- [ ] Documentation update

## Related Issues

Fixes #123

## Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Black formatting applied
- [ ] Ruff linting passed
- [ ] mypy type checking passed
- [ ] All tests passing
- [ ] Commit messages follow conventions

## Screenshots (if applicable)

Add screenshots or examples here.
```

### PR Review Process

1. At least one maintainer review required
2. All CI checks must pass
3. Code coverage must not decrease
4. Any discussion points must be resolved
5. Squash and merge to main

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── api_keys.py      # API key endpoints
│   │   │   ├── sync.py          # Sync endpoints
│   │   │   └── ...
│   │   └── deps.py              # Dependencies
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Business logic
│   ├── core/                    # Configuration
│   ├── db/                      # Database utilities
│   └── main.py                  # FastAPI app
├── tests/                       # Test suite
├── scripts/                     # Utility scripts
├── docs/                        # Documentation
└── alembic/                     # Database migrations
```

### Adding New Features

1. **Create database model** (if needed):
   - `app/models/new_feature.py`
   - Add relationships to existing models
   - Update `app/models/__init__.py`

2. **Create Alembic migration**:
   ```bash
   alembic revision --autogenerate -m "add new feature"
   ```

3. **Create Pydantic schemas**:
   - `app/schemas/new_feature.py`
   - Create, Read, Update, Delete schemas

4. **Create service layer**:
   - `app/services/new_feature.py`
   - Business logic and validation

5. **Create API endpoints**:
   - `app/api/v1/new_feature.py`
   - Request/response handling

6. **Write tests**:
   - `tests/test_new_feature.py`
   - Unit and integration tests

7. **Update documentation**:
   - Add to README.md
   - Update API documentation
   - Add to CHANGELOG.md

## Common Tasks

### Adding a Database Migration

```bash
# Create migration
alembic revision --autogenerate -m "add new_field to users"

# Review generated migration
vim alembic/versions/2026_01_02_1234_add_new_field_to_users.py

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Adding a New Endpoint

```python
# app/api/v1/new_feature.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.new_feature import ItemCreate, ItemResponse
from app.services.new_feature import NewFeatureService

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.post("/", response_model=ItemResponse)
def create_item(
    item: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItemResponse:
    """Create a new item."""
    service = NewFeatureService()
    return service.create_item(item, current_user, db)
```

### Running Tests with Coverage

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html

# Open report
open htmlcov/index.html

# Check specific file
pytest tests/ --cov=app.services --cov-report=term-missing
```

### Debugging Tests

```bash
# Run with print statements
pytest tests/ -v -s

# Run specific test with pdb
pytest tests/test_api_keys.py::TestAPIKeyService::test_create_api_key -v --pdb

# Run with detailed output
pytest tests/ -vv --tb=long
```

## Questions & Support

- **Documentation**: See `/docs` directory
- **Issues**: [GitHub Issues](https://github.com/yourusername/tgitleague-backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/tgitleague-backend/discussions)
- **Email**: hello@thegitleague.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to TheGitLeague Backend! 🚀
