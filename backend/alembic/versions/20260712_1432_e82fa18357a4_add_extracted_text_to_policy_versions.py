"""add extracted text to policy versions

Revision ID: e82fa18357a4
Revises: d7a145d9bdc8
Create Date: 2026-07-12 14:32:00.000000

Adds the extracted_text column to policy_versions table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e82fa18357a4"
down_revision: str | Sequence[str] | None = "d7a145d9bdc8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("policy_versions", sa.Column("extracted_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("policy_versions", "extracted_text")
