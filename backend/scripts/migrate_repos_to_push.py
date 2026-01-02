#!/usr/bin/env python
"""
Migrate repositories from pull-based (PULL_CELERY) to push-based (PUSH_CLIENT) synchronization.

Usage:
    python migrate_repos_to_push.py <repo_id1> <repo_id2> ...

    python migrate_repos_to_push.py --all              # Migrate all PULL_CELERY repos
    python migrate_repos_to_push.py --dry-run <repo_id>  # Preview changes
    python migrate_repos_to_push.py --rollback <repo_id> # Revert to PULL_CELERY

Example:
    python migrate_repos_to_push.py abc123def456 xyz789uvw012
    python migrate_repos_to_push.py --all --exclude-active
"""

import sys
import argparse
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to path
sys.path.insert(0, "/Users/alexandre/Projects/TheGitLeague/backend")

from app.db.base import Base
from app.models.project import Repository, RepoStatus, SyncMethod
from app.models.user import AuditLog
from app.core.config import settings


def create_session():
    """Create database session."""
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def migrate_repo_to_push(
    repo_id: str,
    db,
    dry_run: bool = False,
    clear_credentials: bool = True,
) -> bool:
    """
    Migrate a repository to push-based sync.

    Args:
        repo_id: Repository ID to migrate
        db: Database session
        dry_run: If True, show what would change without making changes
        clear_credentials: If True, clear encrypted credentials

    Returns:
        True if migration successful
    """
    repo = db.query(Repository).filter(Repository.id == repo_id).first()

    if not repo:
        print(f"✗ Repository not found: {repo_id}")
        return False

    if repo.sync_method == SyncMethod.PUSH_CLIENT:
        print(f"⚠ Repository already using PUSH_CLIENT: {repo.name}")
        return True

    if repo.sync_method != SyncMethod.PULL_CELERY:
        print(f"✗ Repository has unsupported sync method: {repo.sync_method}")
        return False

    print(f"\n📦 Repository: {repo.name}")
    print(f"   Current: {repo.sync_method}")
    print(f"   Target:  {SyncMethod.PUSH_CLIENT}")

    if dry_run:
        print("   [DRY RUN] Changes that would be made:")
        print(f"   - Set sync_method to: {SyncMethod.PUSH_CLIENT}")
        if clear_credentials:
            print("   - Clear encrypted credentials")
        print(f"   - Preserve last_ingested_sha: {repo.last_ingested_sha or 'None'}")
        return True

    # Perform migration
    try:
        # Update sync method
        repo.sync_method = SyncMethod.PUSH_CLIENT

        # Clear credentials if requested
        if clear_credentials:
            repo.credentials_encrypted = None

        # Update timestamp
        repo.updated_at = datetime.now(timezone.utc)

        db.commit()

        # Create audit log
        project = repo.project
        audit = AuditLog(
            user_id=project.created_by,
            action="migrate_repo_sync_method",
            resource_type="repository",
            resource_id=repo.id,
            details=f"Migrated repository '{repo.name}' from {SyncMethod.PULL_CELERY} to {SyncMethod.PUSH_CLIENT}",
        )
        db.add(audit)
        db.commit()

        print("   ✓ Migrated successfully")
        return True

    except Exception as e:
        db.rollback()
        print(f"   ✗ Migration failed: {e}")
        return False


def rollback_repo_to_pull(repo_id: str, db, dry_run: bool = False) -> bool:
    """
    Rollback a repository to pull-based sync.

    Args:
        repo_id: Repository ID to rollback
        db: Database session
        dry_run: If True, show what would change without making changes

    Returns:
        True if rollback successful
    """
    repo = db.query(Repository).filter(Repository.id == repo_id).first()

    if not repo:
        print(f"✗ Repository not found: {repo_id}")
        return False

    if repo.sync_method == SyncMethod.PULL_CELERY:
        print(f"⚠ Repository already using PULL_CELERY: {repo.name}")
        return True

    print(f"\n🔄 Repository: {repo.name}")
    print(f"   Current: {repo.sync_method}")
    print(f"   Target:  {SyncMethod.PULL_CELERY}")
    print(f"   WARNING: You'll need to reconfigure credentials for this repo")

    if dry_run:
        print("   [DRY RUN] Changes that would be made:")
        print(f"   - Set sync_method to: {SyncMethod.PULL_CELERY}")
        return True

    # Perform rollback
    try:
        repo.sync_method = SyncMethod.PULL_CELERY
        repo.updated_at = datetime.now(timezone.utc)

        db.commit()

        # Create audit log
        project = repo.project
        audit = AuditLog(
            user_id=project.created_by,
            action="rollback_repo_sync_method",
            resource_type="repository",
            resource_id=repo.id,
            details=f"Rolled back repository '{repo.name}' from {SyncMethod.PUSH_CLIENT} to {SyncMethod.PULL_CELERY}",
        )
        db.add(audit)
        db.commit()

        print("   ✓ Rolled back successfully")
        return True

    except Exception as e:
        db.rollback()
        print(f"   ✗ Rollback failed: {e}")
        return False


def migrate_all_repos(
    db,
    dry_run: bool = False,
    exclude_active: bool = False,
) -> int:
    """
    Migrate all PULL_CELERY repositories to PUSH_CLIENT.

    Args:
        db: Database session
        dry_run: If True, show what would change without making changes
        exclude_active: If True, only migrate repos that haven't synced recently

    Returns:
        Number of successful migrations
    """
    query = db.query(Repository).filter(Repository.sync_method == SyncMethod.PULL_CELERY)

    if exclude_active:
        # Only migrate repos that haven't been synced in 7 days
        from datetime import timedelta

        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        query = query.filter(
            (Repository.last_sync_at.is_(None)) | (Repository.last_sync_at < seven_days_ago)
        )

    repos = query.all()

    if not repos:
        print("No PULL_CELERY repositories found to migrate")
        return 0

    print(f"Found {len(repos)} PULL_CELERY repositories")

    if dry_run:
        print("[DRY RUN MODE]")

    successful = 0
    for repo in repos:
        if migrate_repo_to_push(repo.id, db, dry_run=dry_run):
            successful += 1

    return successful


def get_migration_status(db) -> dict:
    """Get migration status summary."""
    pull_count = db.query(Repository).filter(Repository.sync_method == SyncMethod.PULL_CELERY).count()
    push_count = db.query(Repository).filter(Repository.sync_method == SyncMethod.PUSH_CLIENT).count()

    return {
        "pull_celery": pull_count,
        "push_client": push_count,
        "total": pull_count + push_count,
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate repositories to push-based synchronization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "repo_ids",
        nargs="*",
        help="Repository IDs to migrate",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Migrate all PULL_CELERY repositories",
    )

    parser.add_argument(
        "--exclude-active",
        action="store_true",
        help="Only migrate inactive repos (not synced in 7 days)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without making them",
    )

    parser.add_argument(
        "--rollback",
        nargs="+",
        help="Rollback repository/repositories to PULL_CELERY",
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show migration status",
    )

    args = parser.parse_args()

    db = create_session()

    try:
        # Show status
        if args.status:
            status = get_migration_status(db)
            print("\n📊 Migration Status:")
            print(f"   PULL_CELERY (legacy): {status['pull_celery']}")
            print(f"   PUSH_CLIENT (new):    {status['push_client']}")
            print(f"   Total:                {status['total']}")
            if status["total"] > 0:
                percent = (status["push_client"] / status["total"]) * 100
                print(f"   Progress:             {percent:.1f}% migrated")
            return 0

        # Rollback
        if args.rollback:
            print("Rolling back repositories to PULL_CELERY...")
            successful = 0
            for repo_id in args.rollback:
                if rollback_repo_to_pull(repo_id, db, dry_run=args.dry_run):
                    successful += 1
            print(f"\n✓ {successful}/{len(args.rollback)} rollbacks completed")
            return 0

        # Migrate all
        if args.all:
            print("Migrating all PULL_CELERY repositories...")
            successful = migrate_all_repos(db, dry_run=args.dry_run, exclude_active=args.exclude_active)
            print(f"\n✓ {successful} migrations completed")
            return 0

        # Migrate specific repos
        if args.repo_ids:
            print(f"Migrating {len(args.repo_ids)} repositories...")
            successful = 0
            for repo_id in args.repo_ids:
                if migrate_repo_to_push(repo_id, db, dry_run=args.dry_run):
                    successful += 1
            print(f"\n✓ {successful}/{len(args.repo_ids)} migrations completed")
            return 0

        # No action specified
        parser.print_help()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
