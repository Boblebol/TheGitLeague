"""create commits table

Revision ID: 2024_12_27_1630
Revises: 2024_12_27_1600
Create Date: 2024-12-27 16:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2024_12_27_1630'
down_revision: Union[str, None] = '2024_12_27_1600'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create commits table
    op.create_table(
        'commits',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('sha', sa.String(length=40), nullable=False),
        sa.Column('repo_id', sa.String(length=36), nullable=False),
        sa.Column('author_name', sa.String(length=255), nullable=False),
        sa.Column('author_email', sa.String(length=255), nullable=False),
        sa.Column('committer_name', sa.String(length=255), nullable=False),
        sa.Column('committer_email', sa.String(length=255), nullable=False),
        sa.Column('commit_date', sa.DateTime(), nullable=False),
        sa.Column('message_title', sa.String(length=500), nullable=False),
        sa.Column('message_body', sa.Text(), nullable=True),
        sa.Column('additions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deletions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('files_changed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_merge', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parent_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repo_id'], ['repos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sha')
    )

    # Create indexes
    op.create_index('ix_commits_sha', 'commits', ['sha'])
    op.create_index('ix_commits_repo_id', 'commits', ['repo_id'])
    op.create_index('ix_commits_author_email', 'commits', ['author_email'])
    op.create_index('ix_commits_committer_email', 'commits', ['committer_email'])
    op.create_index('ix_commits_commit_date', 'commits', ['commit_date'])

    # Composite indexes for common queries
    op.create_index('ix_commits_repo_date', 'commits', ['repo_id', 'commit_date'])
    op.create_index('ix_commits_author_date', 'commits', ['author_email', 'commit_date'])


def downgrade() -> None:
    op.drop_index('ix_commits_author_date', table_name='commits')
    op.drop_index('ix_commits_repo_date', table_name='commits')
    op.drop_index('ix_commits_commit_date', table_name='commits')
    op.drop_index('ix_commits_committer_email', table_name='commits')
    op.drop_index('ix_commits_author_email', table_name='commits')
    op.drop_index('ix_commits_repo_id', table_name='commits')
    op.drop_index('ix_commits_sha', table_name='commits')
    op.drop_table('commits')
