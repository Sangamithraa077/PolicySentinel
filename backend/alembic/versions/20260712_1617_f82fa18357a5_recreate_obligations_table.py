"""recreate obligations table

Revision ID: f82fa18357a5
Revises: e82fa18357a4
Create Date: 2026-07-12 16:17:00.000000

Drops the old obligations table and recreates it with new AI obligation fields.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f82fa18357a5"
down_revision: str | Sequence[str] | None = "e82fa18357a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop the old obligations table first
    op.drop_table("obligations")

    # Create the new obligations table
    op.create_table(
        "obligations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("clause_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("object", sa.Text(), nullable=False),
        sa.Column("modality", sa.Text(), nullable=False),
        sa.Column("conditions", sa.Text(), nullable=True),
        sa.Column("time_constraint", sa.Text(), nullable=True),
        sa.Column("compliance_category", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("ai_model", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["clause_id"], ["clauses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "obligations_clause_id_idx",
        "obligations",
        ["clause_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "obligations_policy_id_idx",
        "obligations",
        ["policy_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("obligations_policy_id_idx", table_name="obligations")
    op.drop_index("obligations_clause_id_idx", table_name="obligations")
    op.drop_table("obligations")

    # Recreate the old obligations table
    op.create_table(
        "obligations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clause_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("responsible_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("action_required", sa.Text(), nullable=False),
        sa.Column(
            "deadline_type",
            postgresql.ENUM(
                "ad_hoc",
                "continuous",
                "one_time",
                "recurring",
                name="obligation_deadline_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("deadline_expression", sa.Text(), nullable=True),
        sa.Column(
            "priority",
            postgresql.ENUM(
                "low",
                "medium",
                "high",
                "critical",
                name="obligation_priority",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active",
                "superseded",
                "waived",
                name="obligation_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["clause_id"], ["clauses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["responsible_department_id"], ["departments.id"], ondelete="SET NULL"),
    )
