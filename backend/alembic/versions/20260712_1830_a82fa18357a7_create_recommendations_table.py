"""create recommendations table

Revision ID: a82fa18357a7
Revises: a82fa18357a6
Create Date: 2026-07-12 18:30:00.000000

"""

from collections.abc import Sequence
import alembic
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a82fa18357a7"
down_revision: str | None = "a82fa18357a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create recommendations table
    op = alembic.op
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conflict_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_summary", sa.Text(), nullable=False),
        sa.Column("suggested_action", sa.Text(), nullable=False),
        sa.Column("original_clause", sa.Text(), nullable=True),
        sa.Column("revised_clause", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("ai_model", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="Pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        
        sa.ForeignKeyConstraint(["conflict_id"], ["conflicts.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index("ix_recommendations_conflict_id", "recommendations", ["conflict_id"])
    op.create_index("ix_recommendations_status", "recommendations", ["status"])


def downgrade() -> None:
    op = alembic.op
    op.drop_index("ix_recommendations_status", table_name="recommendations")
    op.drop_index("ix_recommendations_conflict_id", table_name="recommendations")
    op.drop_table("recommendations")
