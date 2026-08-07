"""create stored_files table

Revision ID: b17c9f4a2e01
Revises: 2fa2f947fae4
Create Date: 2026-08-07 15:30:00.000000

"""

from collections.abc import Sequence
import alembic
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b17c9f4a2e01"
down_revision: str | None = "2fa2f947fae4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op = alembic.op
    op.create_table(
        "stored_files",
        sa.Column("storage_path", sa.Text(), primary_key=True),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op = alembic.op
    op.drop_table("stored_files")
