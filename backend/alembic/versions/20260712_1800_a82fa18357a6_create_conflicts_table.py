"""create conflicts table

Revision ID: a82fa18357a6
Revises: f82fa18357a5
Create Date: 2026-07-12 18:00:00.000000

"""

from collections.abc import Sequence
import alembic
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a82fa18357a6"
down_revision: str | None = "f82fa18357a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create the conflicts table
    op = alembic.op
    op.create_table(
        "conflicts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_policy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_policy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_obligation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_obligation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conflict_type", sa.Text(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("ai_explanation", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="Open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        
        sa.ForeignKeyConstraint(["source_policy_id"], ["policies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_policy_id"], ["policies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_obligation_id"], ["obligations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_obligation_id"], ["obligations.id"], ondelete="SET NULL"),
    )

    # Create indexes for efficient querying
    op.create_index("ix_conflicts_source_policy_id", "conflicts", ["source_policy_id"])
    op.create_index("ix_conflicts_target_policy_id", "conflicts", ["target_policy_id"])
    op.create_index("ix_conflicts_status", "conflicts", ["status"])


def downgrade() -> None:
    op = alembic.op
    op.drop_index("ix_conflicts_status", table_name="conflicts")
    op.drop_index("ix_conflicts_target_policy_id", table_name="conflicts")
    op.drop_index("ix_conflicts_source_policy_id", table_name="conflicts")
    op.drop_table("conflicts")
