"""create awards and plays_of_day tables

Revision ID: 2024_12_27_1830
Revises: 2024_12_27_1800
Create Date: 2024-12-27 18:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2024_12_27_1830'
down_revision: Union[str, None] = '2024_12_27_1800'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create awards table
    op.create_table(
        'awards',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('season_id', sa.String(length=36), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('award_type', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),

        # Foreign keys
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Check constraints
        sa.CheckConstraint("period_type IN ('week', 'month', 'season')", name='check_period_type'),
    )

    # Create indexes for awards
    op.create_index(
        'idx_award_unique',
        'awards',
        ['season_id', 'period_type', 'period_start', 'award_type'],
        unique=True
    )
    op.create_index('idx_awards_season', 'awards', ['season_id'])
    op.create_index('idx_awards_user', 'awards', ['user_id'])
    op.create_index('idx_awards_type', 'awards', ['award_type'])

    # Create plays_of_day table
    op.create_table(
        'plays_of_day',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('season_id', sa.String(length=36), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('commit_sha', sa.String(length=40), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),

        # Foreign keys
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),

        # Primary key
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for plays_of_day
    op.create_index(
        'idx_play_unique',
        'plays_of_day',
        ['season_id', 'date'],
        unique=True
    )
    op.create_index('idx_plays_season', 'plays_of_day', ['season_id'])
    op.create_index('idx_plays_user', 'plays_of_day', ['user_id'])
    op.create_index('idx_plays_date', 'plays_of_day', ['date'])


def downgrade() -> None:
    # Drop plays_of_day indexes and table
    op.drop_index('idx_plays_date', table_name='plays_of_day')
    op.drop_index('idx_plays_user', table_name='plays_of_day')
    op.drop_index('idx_plays_season', table_name='plays_of_day')
    op.drop_index('idx_play_unique', table_name='plays_of_day')
    op.drop_table('plays_of_day')

    # Drop awards indexes and table
    op.drop_index('idx_awards_type', table_name='awards')
    op.drop_index('idx_awards_user', table_name='awards')
    op.drop_index('idx_awards_season', table_name='awards')
    op.drop_index('idx_award_unique', table_name='awards')
    op.drop_table('awards')
