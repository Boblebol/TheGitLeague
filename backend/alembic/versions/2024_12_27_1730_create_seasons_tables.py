"""create seasons tables

Revision ID: 2024_12_27_1730
Revises: 2024_12_27_1700
Create Date: 2024-12-27 17:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2024_12_27_1730'
down_revision: Union[str, None] = '2024_12_27_1700'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create seasons table
    op.create_table(
        'seasons',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('start_at', sa.DateTime(), nullable=False),
        sa.Column('end_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('end_at > start_at', name='check_season_dates'),
    )
    
    # Create indexes for seasons
    op.create_index('ix_seasons_project_id', 'seasons', ['project_id'])
    op.create_index('ix_seasons_status', 'seasons', ['status'])
    op.create_index('idx_seasons_project_name', 'seasons', ['project_id', 'name'], unique=True)

    # Create absences table
    op.create_table(
        'absences',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('season_id', sa.String(length=36), nullable=False),
        sa.Column('start_at', sa.Date(), nullable=False),
        sa.Column('end_at', sa.Date(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('end_at >= start_at', name='check_absence_dates'),
    )
    
    # Create indexes for absences
    op.create_index('ix_absences_user_id', 'absences', ['user_id'])
    op.create_index('ix_absences_season_id', 'absences', ['season_id'])
    op.create_index('idx_absences_user_season', 'absences', ['user_id', 'season_id'])


def downgrade() -> None:
    op.drop_index('idx_absences_user_season', table_name='absences')
    op.drop_index('ix_absences_season_id', table_name='absences')
    op.drop_index('ix_absences_user_id', table_name='absences')
    op.drop_table('absences')
    
    op.drop_index('idx_seasons_project_name', table_name='seasons')
    op.drop_index('ix_seasons_status', table_name='seasons')
    op.drop_index('ix_seasons_project_id', table_name='seasons')
    op.drop_table('seasons')
