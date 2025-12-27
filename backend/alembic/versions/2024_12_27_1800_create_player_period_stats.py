"""create player_period_stats table

Revision ID: 2024_12_27_1800
Revises: 2024_12_27_1730
Create Date: 2024-12-27 18:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2024_12_27_1800'
down_revision: Union[str, None] = '2024_12_27_1730'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create player_period_stats table
    op.create_table(
        'player_period_stats',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('season_id', sa.String(length=36), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),

        # Raw commit stats
        sa.Column('commits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('additions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deletions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('files_changed', sa.Integer(), nullable=False, server_default='0'),

        # NBA metrics
        sa.Column('pts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reb', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ast', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('blk', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tov', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('impact_score', sa.Float(), nullable=False, server_default='0.0'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        # Foreign keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ondelete='CASCADE'),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Check constraints
        sa.CheckConstraint("period_type IN ('day', 'week', 'month', 'season')", name='check_period_type'),
    )

    # Create indexes for performance
    # Unique constraint: one stats record per player per period
    op.create_index(
        'idx_player_period_unique',
        'player_period_stats',
        ['user_id', 'season_id', 'period_type', 'period_start'],
        unique=True
    )

    # Performance indexes for leaderboard queries
    op.create_index(
        'idx_period_stats_season_period',
        'player_period_stats',
        ['season_id', 'period_type', 'period_start']
    )
    op.create_index('idx_period_stats_impact_score', 'player_period_stats', ['impact_score'])
    op.create_index('idx_period_stats_pts', 'player_period_stats', ['pts'])
    op.create_index('idx_period_stats_reb', 'player_period_stats', ['reb'])
    op.create_index('idx_period_stats_ast', 'player_period_stats', ['ast'])
    op.create_index('idx_period_stats_blk', 'player_period_stats', ['blk'])
    op.create_index('idx_period_stats_commits', 'player_period_stats', ['commits'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_period_stats_commits', table_name='player_period_stats')
    op.drop_index('idx_period_stats_blk', table_name='player_period_stats')
    op.drop_index('idx_period_stats_ast', table_name='player_period_stats')
    op.drop_index('idx_period_stats_reb', table_name='player_period_stats')
    op.drop_index('idx_period_stats_pts', table_name='player_period_stats')
    op.drop_index('idx_period_stats_impact_score', table_name='player_period_stats')
    op.drop_index('idx_period_stats_season_period', table_name='player_period_stats')
    op.drop_index('idx_player_period_unique', table_name='player_period_stats')

    # Drop table
    op.drop_table('player_period_stats')
