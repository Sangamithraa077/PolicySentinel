"""add policy upload metadata

Revision ID: 881fa18357a3
Revises: 517c2ef6e254
Create Date: 2026-07-11 15:16:38.060741

Adds the columns the upload module extracts and stores for each
uploaded document (original_filename, size_bytes, file_type,
description) to policy_versions, and relaxes
policies.owning_department_id to nullable — a policy created purely
from an upload has no department assignment yet; that's a later
triage step, not part of upload metadata.

Assumes an empty/fresh policy_versions table (true for this project at
its current stage): the three NOT NULL columns are added without a
server_default, which would fail against a table that already has
rows. If this table ever has real data before this migration runs,
add the columns nullable, backfill, then tighten to NOT NULL instead.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "881fa18357a3"
down_revision: str | Sequence[str] | None = "517c2ef6e254"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

policy_document_file_type = postgresql.ENUM(
    "txt", "md", "pdf", "docx", name="policy_document_file_type"
)


def upgrade() -> None:
    bind = op.get_bind()
    policy_document_file_type.create(bind, checkfirst=True)

    op.add_column("policy_versions", sa.Column("original_filename", sa.Text(), nullable=False))
    op.add_column("policy_versions", sa.Column("size_bytes", sa.Integer(), nullable=False))
    op.add_column(
        "policy_versions",
        sa.Column(
            "file_type",
            postgresql.ENUM(
                "txt", "md", "pdf", "docx", name="policy_document_file_type", create_type=False
            ),
            nullable=False,
        ),
    )
    op.add_column("policy_versions", sa.Column("description", sa.Text(), nullable=True))
    op.create_check_constraint(
        "policy_versions_size_bytes_positive", "policy_versions", "size_bytes > 0"
    )

    op.alter_column("policies", "owning_department_id", nullable=True)


def downgrade() -> None:
    op.alter_column("policies", "owning_department_id", nullable=False)

    op.drop_constraint("policy_versions_size_bytes_positive", "policy_versions", type_="check")
    op.drop_column("policy_versions", "description")
    op.drop_column("policy_versions", "file_type")
    op.drop_column("policy_versions", "size_bytes")
    op.drop_column("policy_versions", "original_filename")

    policy_document_file_type.drop(op.get_bind(), checkfirst=True)
