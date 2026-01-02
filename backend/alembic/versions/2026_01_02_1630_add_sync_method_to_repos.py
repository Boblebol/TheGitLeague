"""Add sync_method column to repos table and make remote fields nullable

Revision ID: 2026_01_02_1630
Revises: 2026_01_02_1600
Create Date: 2026-01-02 16:30:00

This migration adds support for push-based Git synchronization by introducing
the sync_method column to repos. The new PUSH_CLIENT method allows external
clients to push commits via API, while PULL_CELERY preserves backward compatibility.

Changes:
- Add sync_method column (default: PULL_CELERY for backward compatibility)
- Make remote_url nullable (supports push-client repos without remote URL)
- Make remote_type nullable (supports push-client repos without remote type)
- Create index on sync_method for query optimization

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_01_02_1630"
down_revision: Union[str, None] = "2026_01_02_1600"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sync_method column to repos table
    op.add_column(
        "repos",
        sa.Column(
            "sync_method",
            sa.String(length=20),
            nullable=False,
            server_default="pull_celery",
        ),
    )

    # Make remote_url nullable
    op.alter_column(
        "repos",
        "remote_url",
        existing_type=sa.Text(),
        nullable=True,
        existing_nullable=False,
    )

    # Make remote_type nullable
    op.alter_column(
        "repos",
        "remote_type",
        existing_type=sa.String(length=20),
        nullable=True,
        existing_nullable=False,
    )

    # Create index on sync_method for query optimization
    op.create_index("idx_repos_sync_method", "repos", ["sync_method"])


def downgrade() -> None:
    # Drop index
    op.drop_index("idx_repos_sync_method", table_name="repos")

    # Restore remote_type to NOT nullable
    op.alter_column(
        "repos",
        "remote_type",
        existing_type=sa.String(length=20),
        nullable=False,
        existing_nullable=True,
    )

    # Restore remote_url to NOT nullable
    op.alter_column(
        "repos",
        "remote_url",
        existing_type=sa.Text(),
        nullable=False,
        existing_nullable=True,
    )

    # Drop sync_method column
    op.drop_column("repos", "sync_method")
