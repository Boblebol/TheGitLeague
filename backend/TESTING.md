# 🧪 Backend Testing Guide — The Git League

Comprehensive testing documentation for The Git League backend.

---

## Overview

The Git League backend includes **comprehensive unit tests, integration tests, and end-to-end tests** to ensure all scenarios work correctly.

**Test Coverage:**
- ✅ Unit Tests: 100+ tests for core services
- ✅ E2E Tests: 50+ API endpoint tests
- ✅ Integration Tests: Git sync, author matching, batch processing
- ✅ Feature Tests: Fantasy league, scoring, leaderboards

---

## Test Structure

```
backend/tests/
├── conftest.py                      # Shared fixtures and configuration
├── test_auth_service.py             # Authentication & user management
├── test_api_endpoints.py            # API endpoint E2E tests
├── test_scoring_service.py          # Scoring calculations & leaderboards
├── test_git_sync_integration.py     # Git sync & commit processing
├── test_fantasy_league.py           # Fantasy league functionality
├── test_api_keys.py                 # API key generation & management
├── test_api_keys_endpoints.py       # API key endpoints
├── test_sync.py                     # Sync service tests
└── test_migration.py                # Database migration tests
```

---

## Running Tests

### Run All Tests

```bash
cd backend
pytest
```

### Run Specific Test File

```bash
pytest tests/test_auth_service.py
```

### Run Specific Test Class

```bash
pytest tests/test_auth_service.py::TestMagicLinkGeneration
```

### Run Specific Test

```bash
pytest tests/test_auth_service.py::TestMagicLinkGeneration::test_create_magic_link_token
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

Coverage report will be in `htmlcov/index.html`

### Run with Verbose Output

```bash
pytest -v
```

### Run with Debugging

```bash
pytest -vv -s  # -s shows print statements
```

---

## Test Categories

### 1. Authentication & User Management (`test_auth_service.py`)

**Tests:**
- ✅ Magic link token generation
- ✅ Access token creation and expiration
- ✅ Password hashing and verification
- ✅ User approval workflow
- ✅ Role-based access control

**Scenarios:**
```python
# Magic link creation
def test_create_magic_link_token()

# Token expiration
def test_magic_link_token_expiration()

# Multiple magic links
def test_multiple_magic_links_valid()

# Password hashing
def test_password_hashing_different_each_time()

# User roles
def test_commissioner_role()
def test_player_role()
def test_spectator_role()
```

### 2. API Endpoints (`test_api_endpoints.py`)

**Coverage:**
- ✅ Health checks
- ✅ Authentication endpoints
- ✅ User management
- ✅ Project management
- ✅ Repository management
- ✅ Leaderboards
- ✅ Seasons
- ✅ Awards
- ✅ Fantasy leagues
- ✅ API keys
- ✅ Error handling

**Test Categories:**

```python
class TestHealthEndpoints:
    def test_health_check()
    def test_health_db_connection()
    def test_health_redis_connection()

class TestAuthenticationEndpoints:
    def test_request_magic_link()
    def test_logout()

class TestProjectEndpoints:
    def test_create_project()
    def test_get_project()
    def test_update_project()

class TestLeaderboardEndpoints:
    def test_get_leaderboard()
    def test_get_leaderboard_with_period_filter()
    def test_player_stats()

class TestErrorHandling:
    def test_not_found_error()
    def test_unauthorized_error()
    def test_forbidden_error()
```

### 3. Scoring & Leaderboards (`test_scoring_service.py`)

**Tests:**
- ✅ Scoring calculations (PTS, REB, AST, BLK, STL, TOV)
- ✅ Scoring coefficients
- ✅ Player statistics
- ✅ Leaderboard calculations
- ✅ Award calculations
- ✅ Period-based statistics
- ✅ Ranking and percentiles

**Scenarios:**
```python
# Scoring
def test_base_scoring()
def test_scoring_with_zero_changes()
def test_scoring_capped_additions()
def test_scoring_bonus_for_multifile_commits()
def test_scoring_rebounds_from_deletions()

# Leaderboards
def test_empty_leaderboard()
def test_leaderboard_sorting()
def test_leaderboard_filters()

# Awards
def test_player_of_the_week_calculation()
def test_most_improved_calculation()
def test_mvp_calculation()

# Periods
def test_daily_stats()
def test_weekly_stats()
def test_monthly_stats()
```

### 4. Git Synchronization (`test_git_sync_integration.py`)

**Tests:**
- ✅ Repository URL validation
- ✅ Commit parsing and metadata extraction
- ✅ Sync workflow (new/existing repos)
- ✅ Commit deduplication
- ✅ Author matching and linking
- ✅ Sync progress tracking
- ✅ Error recovery
- ✅ Batch processing

**Scenarios:**
```python
# Validation
def test_valid_https_url()
def test_valid_ssh_url()
def test_invalid_url()

# Parsing
def test_parse_commit_message()
def test_skip_stats_detection()
def test_wip_detection()
def test_bug_fix_detection()
def test_revert_detection()

# Sync
def test_sync_new_repository()
def test_sync_existing_repository()
def test_partial_sync_recovery()

# Deduplication
def test_duplicate_detection_by_sha()
def test_unique_commits()

# Author matching
def test_match_author_by_email()
def test_match_author_multiple_emails()
```

### 5. Fantasy League (`test_fantasy_league.py`)

**Tests:**
- ✅ League creation
- ✅ Draft management
- ✅ Roster management
- ✅ Fantasy scoring
- ✅ League standings
- ✅ Schedule generation
- ✅ League settings

**Scenarios:**
```python
# League
def test_create_fantasy_league()
def test_league_unique_name_per_season()
def test_league_roster_constraints()

# Draft
def test_start_draft()
def test_draft_pick_player()
def test_avoid_duplicate_picks()

# Roster
def test_create_roster()
def test_add_player_to_roster()
def test_roster_size_constraints()
def test_lock_roster_before_season()

# Scoring
def test_calculate_fantasy_points()
def test_roster_total_score()

# Standings
def test_league_standings()
def test_standings_sorted_by_score()

# Schedule
def test_create_schedule()
def test_schedule_fairness()
```

### 6. API Keys (`test_api_keys.py` & `test_api_keys_endpoints.py`)

**Tests:**
- ✅ API key generation
- ✅ Key creation and storage
- ✅ Key verification
- ✅ Scopes and permissions
- ✅ Key revocation

---

## Test Fixtures

### Common Fixtures (conftest.py)

```python
# Database
@pytest.fixture
def engine()           # Test database engine
@pytest.fixture
def db_session()       # Test database session

# Users
@pytest.fixture
def test_user()        # Commissioner user
@pytest.fixture
def test_player()      # Player user

# Project
@pytest.fixture
def test_project()     # Test project

# API Client
@pytest.fixture
def client()           # FastAPI TestClient

# Authentication
@pytest.fixture
def auth_headers()     # Bearer token headers
@pytest.fixture
def commissioner_headers()  # Commissioner token headers
```

### Usage Example

```python
def test_example(db_session, test_user, test_project, auth_headers):
    """Test using multiple fixtures."""
    # db_session: Database session for test
    # test_user: Pre-created commissioner user
    # test_project: Pre-created project
    # auth_headers: Authorization headers with test_user token

    response = client.get(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
```

---

## Best Practices

### 1. Test Isolation

Each test should be independent:

```python
# Good: Fixture creates fresh data for each test
def test_user_creation(db_session):
    user = create_user(db_session)
    assert user.id is not None

# Bad: Test depends on previous test
def test_update_user():
    # Assumes user from previous test exists
```

### 2. Clear Test Names

Test names should describe what they test:

```python
# Good
def test_create_magic_link_with_valid_email()

# Bad
def test_magic_link()
```

### 3. Arrange-Act-Assert Pattern

```python
def test_update_user_profile(client, auth_headers, test_user):
    # Arrange
    new_name = "Updated Name"

    # Act
    response = client.put(
        f"/api/v1/users/me",
        headers=auth_headers,
        json={"display_name": new_name},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["display_name"] == new_name
```

### 4. Testing Edge Cases

```python
def test_scoring_with_edge_cases():
    """Test scoring doesn't break with extreme values."""
    # Empty commit
    assert scoring_service.calculate_points(0, 0) >= 0

    # Huge commit
    assert scoring_service.calculate_points(1000000, 0) > 0

    # Negative values (shouldn't happen but should handle gracefully)
    assert scoring_service.calculate_points(-10, -5) >= 0
```

### 5. Mocking External Dependencies

```python
from unittest.mock import patch, Mock

@patch('app.services.repository.repository_service.clone_repo')
def test_sync_with_mock(mock_clone, db_session):
    """Test sync without actually cloning."""
    mock_clone.return_value = "/tmp/test-repo"

    result = sync_repository(db_session)
    mock_clone.assert_called_once()
```

---

## Coverage Goals

### Minimum Coverage

- **Backend:** 80% overall
- **Critical paths:** 90% (auth, scoring, sync)
- **API endpoints:** 85%

### Check Coverage

```bash
pytest --cov=app --cov-fail-under=80
```

### View Coverage Report

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- ✅ Every push to main/develop
- ✅ Every pull request
- ✅ Scheduled daily at midnight

**Workflow:** `.github/workflows/ci.yml`

**Steps:**
1. Lint code (Ruff, MyPy)
2. Run tests with coverage
3. Upload coverage to Codecov
4. Build Docker images

### Pre-commit Hooks

Run tests before committing:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run tests
pre-commit run --all-files
```

---

## Troubleshooting

### Database Connection Error

```bash
# Check SQLite is available
python -c "import sqlite3; print(sqlite3.sqlite_version)"

# Reset test database
rm .pytest_cache/
pytest --cache-clear
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Check PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH
```

### Timeout Errors

Increase timeout:
```bash
pytest --timeout=300
```

### Flaky Tests

Use retry plugin:
```bash
pip install pytest-rerunfailures
pytest --reruns 3 --reruns-delay 1
```

---

## Adding New Tests

### 1. Create Test File

```bash
touch tests/test_new_feature.py
```

### 2. Import Fixtures

```python
import pytest
from app.services.new_service import new_service
```

### 3. Write Test Class

```python
class TestNewFeature:
    """Test new feature."""

    def test_basic_functionality(self, db_session):
        """Test basic functionality."""
        result = new_service.do_something()
        assert result is not None
```

### 4. Run Test

```bash
pytest tests/test_new_feature.py -v
```

---

## Test Documentation

Each test file should include:

```python
"""
Brief description of what's being tested.

This module tests:
- Feature A
- Feature B
- Feature C
"""

class TestFeatureA:
    """Test Feature A."""

    def test_scenario_1(self, fixtures):
        """Test specific scenario for Feature A."""
```

---

## Performance Testing

### Load Testing

```bash
pip install locust
```

See `load_tests/` directory for load testing scripts.

### Benchmarking

```python
def test_performance(benchmark):
    """Benchmark scoring calculation."""
    result = benchmark(scoring_service.calculate_metrics, ...)
    assert result is not None
```

---

## Security Testing

### SQL Injection

Tests verify parameterized queries:
```python
def test_sql_injection_prevention(db_session):
    """Verify SQLAlchemy prevents SQL injection."""
    result = db_session.query(User).filter(
        User.email == "'; DROP TABLE users; --"
    )
    # Should safely handle the string, not execute SQL
```

### Authentication

Tests verify:
- ✅ Tokens are validated
- ✅ Expired tokens rejected
- ✅ Invalid tokens rejected
- ✅ Permissions enforced

---

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy testing](https://docs.sqlalchemy.org/en/14/faq/testing.html)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

---

## Contributing Tests

When contributing code:
1. Write tests first (TDD preferred)
2. Ensure 80%+ coverage for new code
3. Test happy path + error cases
4. Use clear test names
5. Document complex test logic

---

**Happy Testing!** 🧪

[Back to README](./README.md) | [Development Guide](./DEVELOPMENT.md)
