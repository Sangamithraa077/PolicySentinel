"""add review fields to recommendations

Revision ID: a82fa18357a9
Revises: a82fa18357a8
Create Date: 2026-07-12 18:59:00.000000

"""

from collections.abc import Sequence
import alembic
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a82fa18357a9"
down_revision: str | None = "a82fa18357a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op = alembic.op
    op.add_column("recommendations", sa.Column("reviewer_name", sa.Text(), nullable=True))
    op.add_column("recommendations", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("recommendations", sa.Column("review_comments", sa.Text(), nullable=True))


def downgrade() -> None:
    op = alembic.op
    op.drop_column("recommendations", "review_comments")
    op.drop_column("recommendations", "reviewed_at")
    op.drop_column("recommendations", "reviewer_name")
