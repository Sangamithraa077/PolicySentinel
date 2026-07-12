"""create_regulatory_mappings_table

Revision ID: 2fa2f947fae4
Revises: 08b078539026
Create Date: 2026-07-12 20:29:21.303317

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2fa2f947fae4'
down_revision: Union[str, Sequence[str], None] = '08b078539026'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('regulatory_mappings',
    sa.Column('policy_id', sa.UUID(), nullable=False),
    sa.Column('obligation_id', sa.UUID(), nullable=False),
    sa.Column('framework_name', sa.Text(), nullable=False),
    sa.Column('regulation_id', sa.Text(), nullable=False),
    sa.Column('clause_number', sa.Text(), nullable=False),
    sa.Column('confidence_score', sa.Float(), nullable=False),
    sa.Column('ai_explanation', sa.Text(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['obligation_id'], ['obligations.id'], name=op.f('fk_regulatory_mappings_obligation_id_obligations'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], name=op.f('fk_regulatory_mappings_policy_id_policies'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_regulatory_mappings'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('regulatory_mappings')
    # ### end Alembic commands ###
