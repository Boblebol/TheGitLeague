"""create project configs table

Revision ID: 2024_12_27_1700
Revises: 2024_12_27_1630
Create Date: 2024-12-27 17:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2024_12_27_1700'
down_revision: Union[str, None] = '2024_12_27_1630'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create project_configs table
    op.create_table(
        'project_configs',
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('scoring_coefficients', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('project_id')
    )


def downgrade() -> None:
    op.drop_table('project_configs')
