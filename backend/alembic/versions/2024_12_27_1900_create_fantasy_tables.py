"""create fantasy league tables

Revision ID: 2024_12_27_1900
Revises: 2024_12_27_1830
Create Date: 2024-12-27 19:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2024_12_27_1900'
down_revision: Union[str, None] = '2024_12_27_1830'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create fantasy_leagues table
    op.create_table(
        'fantasy_leagues',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('season_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('roster_min', sa.Integer(), nullable=False),
        sa.Column('roster_max', sa.Integer(), nullable=False),
        sa.Column('lock_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),

        # Foreign keys
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ondelete='CASCADE'),

        # Primary key
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for fantasy_leagues
    op.create_index('idx_fantasy_leagues_season', 'fantasy_leagues', ['season_id'])

    # Create fantasy_participants table
    op.create_table(
        'fantasy_participants',
        sa.Column('league_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),

        # Foreign keys
        sa.ForeignKeyConstraint(['league_id'], ['fantasy_leagues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),

        # Composite primary key
        sa.PrimaryKeyConstraint('league_id', 'user_id'),
    )

    # Create fantasy_rosters table
    op.create_table(
        'fantasy_rosters',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('league_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),

        # Foreign keys
        sa.ForeignKeyConstraint(['league_id'], ['fantasy_leagues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),

        # Primary key
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for fantasy_rosters
    op.create_index(
        'idx_fantasy_roster_unique',
        'fantasy_rosters',
        ['league_id', 'user_id'],
        unique=True
    )
    op.create_index('idx_fantasy_rosters_league', 'fantasy_rosters', ['league_id'])
    op.create_index('idx_fantasy_rosters_user', 'fantasy_rosters', ['user_id'])

    # Create fantasy_roster_picks table
    op.create_table(
        'fantasy_roster_picks',
        sa.Column('roster_id', sa.String(length=36), nullable=False),
        sa.Column('picked_user_id', sa.String(length=36), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),

        # Foreign keys
        sa.ForeignKeyConstraint(['roster_id'], ['fantasy_rosters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['picked_user_id'], ['users.id'], ondelete='CASCADE'),

        # Composite primary key
        sa.PrimaryKeyConstraint('roster_id', 'picked_user_id'),
    )


def downgrade() -> None:
    # Drop tables in reverse order (handle foreign keys)
    op.drop_table('fantasy_roster_picks')

    op.drop_index('idx_fantasy_rosters_user', table_name='fantasy_rosters')
    op.drop_index('idx_fantasy_rosters_league', table_name='fantasy_rosters')
    op.drop_index('idx_fantasy_roster_unique', table_name='fantasy_rosters')
    op.drop_table('fantasy_rosters')

    op.drop_table('fantasy_participants')

    op.drop_index('idx_fantasy_leagues_season', table_name='fantasy_leagues')
    op.drop_table('fantasy_leagues')
