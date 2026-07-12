"""add_advanced_findings_columns_to_conflicts

Revision ID: 08b078539026
Revises: f3a8ae9b7add
Create Date: 2026-07-12 19:44:08.784213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '08b078539026'
down_revision: Union[str, Sequence[str], None] = 'f3a8ae9b7add'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('conflicts', sa.Column('temporal_conflict', sa.Text(), nullable=True))
    op.add_column('conflicts', sa.Column('strength_conflict', sa.Text(), nullable=True))
    op.add_column('conflicts', sa.Column('staleness_status', sa.Text(), nullable=True))
    op.add_column('conflicts', sa.Column('detected_parameters', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('conflicts', 'detected_parameters')
    op.drop_column('conflicts', 'staleness_status')
    op.drop_column('conflicts', 'strength_conflict')
    op.drop_column('conflicts', 'temporal_conflict')
    # ### end Alembic commands ###
