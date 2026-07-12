"""create compliance audit logs table

Revision ID: a82fa18357a8
Revises: a82fa18357a7
Create Date: 2026-07-12 18:52:00.000000

"""

from collections.abc import Sequence
import alembic
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a82fa18357a8"
down_revision: str | None = "a82fa18357a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create compliance_audit_logs table
    op = alembic.op
    op.create_table(
        "compliance_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("user_identifier", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index("ix_compliance_audit_logs_company_id", "compliance_audit_logs", ["company_id"])
    op.create_index("ix_compliance_audit_logs_event_type", "compliance_audit_logs", ["event_type"])


def downgrade() -> None:
    op = alembic.op
    op.drop_index("ix_compliance_audit_logs_event_type", table_name="compliance_audit_logs")
    op.drop_index("ix_compliance_audit_logs_company_id", table_name="compliance_audit_logs")
    op.drop_table("compliance_audit_logs")
