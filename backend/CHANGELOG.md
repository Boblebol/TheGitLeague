# Changelog

All notable changes to the TheGitLeague Backend project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-02

### Added

#### Phase 1: API Keys System
- **New**: Complete API Key management system with Argon2 password hashing
- **New**: `app/models/api_key.py` - APIKey SQLAlchemy model with audit fields
- **New**: `app/services/api_key.py` - APIKeyService with create, verify, revoke, list operations
- **New**: `app/schemas/api_key.py` - Pydantic validation schemas for API key operations
- **New**: `app/api/v1/api_keys.py` - REST endpoints for API key CRUD operations
  - `POST /api/v1/api-keys/` - Create new API key (JWT auth)
  - `GET /api/v1/api-keys/` - List API keys for current user
  - `DELETE /api/v1/api-keys/{id}` - Revoke API key
- **New**: `alembic/versions/2026_01_02_1600_create_api_keys_table.py` - Database migration for api_keys table
- **New**: Hybrid authentication in `app/api/deps.py`
  - `get_current_user_from_api_key()` - Extract and verify API key from Bearer token
  - `get_current_user_hybrid()` - Try JWT first, fallback to API key
- **New**: API key features:
  - Argon2 password hashing with configurable parameters
  - Prefix-based lookup (`tgl_xxxxxxxx_secret` format)
  - Optional expiration with automatic invalidation
  - Revocation with instant deactivation
  - Usage tracking (IP address, timestamp, usage count)
  - Comprehensive audit logging

#### Phase 2: Repository Migration Infrastructure
- **New**: `SyncMethod` enum in `app/models/project.py`
  - `PULL_CELERY` - Legacy pull-based sync via Celery
  - `PUSH_CLIENT` - New push-based sync via external client
- **New**: `alembic/versions/2026_01_02_1630_add_sync_method_to_repos.py` - Repository migration
  - Added `sync_method` column to repositories table (defaults to PULL_CELERY)
  - Made `remote_url` and `remote_type` nullable for push-based repos
  - Added index on `sync_method` for performance
- **Enhanced**: `app/schemas/project.py` - Updated repository schemas with sync_method
- **Feature**: Backward compatibility - both PULL_CELERY and PUSH_CLIENT methods coexist

#### Phase 3: Synchronization API
- **New**: `app/schemas/sync.py` - Commit and sync schemas with strict validation
  - `CommitMetadata` - Single commit with SHA (40 hex), email normalization, stats
  - `SyncCommitsRequest` - Batch submission (1-1000 commits) with deduplication validation
  - `SyncCommitsResponse` - Detailed result with per-commit status
  - `SyncStatusResponse` - Repository sync status and metrics
- **New**: `app/services/sync.py` - Commit ingestion service
  - `validate_repo_for_sync()` - Validate repo is push-based and owned by user
  - `ingest_commits()` - Batch insert with deduplication, atomic transactions, status tracking
  - `get_sync_status()` - Repository status with last_ingested_sha and error info
- **New**: `app/api/v1/sync.py` - Synchronization endpoints
  - `POST /api/v1/sync/projects/{project_id}/repos/{repo_id}/commits` - Submit commits (rate limited 100/min)
  - `GET /api/v1/sync/projects/{project_id}/repos/{repo_id}/status` - Get sync status
- **New**: Rate limiting (slowapi) on sync endpoints (100 requests/minute per IP)
- **Feature**: Commit deduplication by SHA - automatically skip existing commits
- **Feature**: Status tracking - PENDING → SYNCING → HEALTHY/ERROR workflow
- **Feature**: Comprehensive audit logging of all sync operations

#### Phase 4: Python Client Package
- **New**: Complete `gitleague-client` Python package with 7 core modules:
  - `cli.py` - Click CLI interface (init, test, sync commands)
  - `config.py` - YAML configuration loader with Pydantic validation
  - `git_scanner.py` - Git commit extraction with incremental sync support
  - `api_client.py` - HTTP client with retry logic and rate limit handling
  - `sync.py` - Sync orchestrator with progress bars and dry-run support
  - `exceptions.py` - Custom exception hierarchy
  - `__init__.py` - Package initialization and exports
- **New**: `gitleague-client/pyproject.toml` - Package metadata and dependencies
- **New**: `examples/repos.yaml` - Example configuration template
- **New**: `gitleague-client/README.md` - Client documentation
- **New**: Client features:
  - Config validation via Pydantic
  - Path expansion for home directories and environment variables
  - Git commit scanning with branch validation
  - Incremental sync (since last_ingested_sha)
  - Batch commit uploads (configurable batch size)
  - Intelligent retry logic with exponential backoff
  - Rate limit handling (429 status)
  - Dry-run mode for previewing syncs
  - Rich console output with progress bars
  - Support for SSH key and HTTPS authentication

#### Phase 5: Migration & Deployment Tools
- **New**: `scripts/migrate_repos_to_push.py` - Comprehensive repository migration script
  - Migrate specific repositories: `python migrate_repos_to_push.py <repo_id1> <repo_id2>`
  - Migrate all repositories: `python migrate_repos_to_push.py --all`
  - Dry-run mode: `python migrate_repos_to_push.py --dry-run <repo_id>`
  - Selective migration: `python migrate_repos_to_push.py --all --exclude-active`
  - Rollback support: `python migrate_repos_to_push.py --rollback <repo_id>`
  - Status reporting: `python migrate_repos_to_push.py --status`
  - Features:
    - Preserves last_ingested_sha for incremental syncs
    - Clears encrypted credentials during migration
    - Updates migration timestamp
    - Creates audit log entries
    - Full rollback support
- **New**: `docs/MIGRATION_GUIDE.md` - 7-phase migration documentation
  - Pre-migration planning and client setup
  - Dry-run procedures
  - Multiple migration strategies (gradual, all-at-once, by-project)
  - Coexistence period explanation
  - Troubleshooting guide with 6+ common issues
  - Monitoring queries and FAQ
- **New**: `docs/DEPLOYMENT_CHECKLIST.md` - Production deployment guide
  - Pre-deployment verification (1-2 weeks)
  - Deployment day procedures with step-by-step commands
  - Post-deployment monitoring (48 hours)
  - Migration phase checklist (weeks 1-3)
  - Stability criteria (functionality, data integrity, performance, reliability, security)
  - Rollback procedure (15-minute response plan)
  - Emergency contacts and common commands
- **New**: `docs/IMPLEMENTATION_SUMMARY.md` - Complete implementation reference
  - Architecture diagrams (before/after)
  - All 5 phases with file locations
  - Test coverage summary (99+ tests)
  - Security features detailed
  - Database schema changes
  - API reference with examples
  - Performance characteristics
  - Monitoring and observability
  - Future enhancements

#### Tests & Quality Assurance
- **New**: 21 API key service tests - generation, creation, verification, expiration, revocation
- **New**: 12 API key endpoint tests - CRUD operations, authentication, multi-user isolation
- **New**: 9 sync API schema tests - SHA validation, email normalization, limit validation
- **New**: 8 sync API service tests - deduplication, status tracking, error handling
- **New**: 11 migration scenario tests - migration, rollback, status preservation, filtering
- **New**: 17 client config tests - YAML loading, validation, path expansion
- **New**: 10 API client tests - connection testing, retry logic, rate limit handling
- **Total**: 88 backend tests + 27 client tests = **115 comprehensive tests**, all passing
- **Coverage**: Critical paths in API keys, sync, authentication, validation, migration

#### Infrastructure & Documentation
- **New**: Database fixtures and conftest.py for pytest
- **New**: In-memory SQLite database for testing
- **New**: FastAPI dependency override for test authentication
- **New**: Timezone-aware datetime handling (Python 3.13+ compatible)
- **Fixed**: SQLite pool configuration issue (conditional pool_size/max_overflow)
- **Enhanced**: Complete docstrings throughout codebase
- **Enhanced**: Migration script comments and descriptive variable names

### Changed

- **Updated**: `app/models/project.py` - Added SyncMethod enum and sync_method field to Repository
- **Updated**: `app/schemas/project.py` - Made remote_type optional, added sync_method to schemas
- **Updated**: `app/models/commit.py` - Updated datetime to use timezone-aware datetime.now(timezone.utc)
- **Updated**: `app/core/security.py` - Replaced datetime.utcnow() with datetime.now(timezone.utc)
- **Updated**: `app/api/deps.py` - Added hybrid authentication support
- **Updated**: `app/models/user.py` - Added api_keys relationship with CASCADE delete
- **Updated**: `app/api/v1/__init__.py` - Imported and registered sync router
- **Updated**: All datetime operations throughout codebase for Python 3.13+ compatibility

### Fixed

- **Fixed**: SQLAlchemy SQLite pool configuration - conditional application of pool_size/max_overflow
- **Fixed**: Timezone-aware datetime handling across SQLite and PostgreSQL
- **Fixed**: Path expansion in client config - now expands both path and ssh_key fields
- **Fixed**: Rate limiting decorator compatibility - added Request parameter to sync endpoints
- **Fixed**: Database rollback on migration errors - proper exception handling in migration script

### Security

- **Added**: Argon2 password hashing for API keys (industry standard)
- **Added**: Prefix-based API key lookup without exposing secrets
- **Added**: API key expiration support
- **Added**: Comprehensive audit logging for all API key operations
- **Added**: Usage tracking (IP address, timestamp, count)
- **Added**: Rate limiting on sync endpoints (100 requests/minute)
- **Added**: Strict Pydantic validation on all inputs
- **Added**: Email normalization (lowercase)
- **Added**: SHA format validation (40 hex characters)
- **Added**: Batch size limits (max 1000 commits)
- **Added**: Commit deduplication by SHA

### Performance

- **Optimized**: API key lookup by prefix (O(1) performance with index)
- **Optimized**: Commit deduplication with fast SHA lookup
- **Optimized**: Batch commit insertion (atomic transaction)
- **Optimized**: Database pooling for connection management
- **Optimized**: Client retry logic with exponential backoff
- **Optimized**: Git scanning with incremental SHA-based filtering

### Deprecated

- **Deprecated**: Direct credential storage in PULL_CELERY repos during migration to PUSH_CLIENT
- **Note**: PULL_CELERY method still supported for backward compatibility; deprecation planned for Q3 2026

## [0.3.0] - 2025-12-31

### Added

- Migration script and deployment tools
- Complete migration guide and deployment checklist
- Implementation summary documentation

## [0.2.0] - 2025-12-30

### Added

- Commit synchronization API
- Batch commit ingestion with deduplication
- Sync status tracking

## [0.1.0] - 2025-12-29

### Added

- API Key management system
- Repository sync method infrastructure
- Foundation for push-based synchronization

---

## Version Guidelines

### Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0) - Incompatible API changes (e.g., endpoint removal, breaking schema changes)
- **MINOR** (1.X.0) - New features, backward compatible (e.g., new endpoints, new scopes)
- **PATCH** (1.0.X) - Bug fixes, backward compatible (e.g., security patches, performance improvements)

### Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with changes
3. Create git tag: `git tag -a v1.0.0 -m "Release 1.0.0"`
4. Push tag: `git push origin v1.0.0`

### Supported Versions

- **1.0.x** - Current release (actively maintained)
- **0.3.x** - Maintenance only (security updates only)
- **0.2.x** - End of life (no support)
- **0.1.x** - End of life (no support)

---

## How to Use This Changelog

- **For Users**: Look at [Unreleased] and latest version to see what's new
- **For Developers**: Check version history for implementation details
- **For Maintainers**: Add entries to [Unreleased] as changes are made

## Related Documentation

- [README](README.md) - Project overview and quick start
- [CONTRIBUTING](CONTRIBUTING.md) - Development guidelines
- [ARCHITECTURE](docs/ARCHITECTURE.md) - System design

---

**Note**: Release dates are in ISO 8601 format (YYYY-MM-DD). See [CHANGELOG.md](CHANGELOG.md) for a complete history.
