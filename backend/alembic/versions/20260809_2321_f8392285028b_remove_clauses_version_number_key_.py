"""remove_clauses_version_number_key_unique_index

Revision ID: f8392285028b
Revises: b17c9f4a2e01
Create Date: 2026-08-09 23:21:36.722241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8392285028b'
down_revision: Union[str, Sequence[str], None] = 'b17c9f4a2e01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index("clauses_version_number_key", table_name="clauses")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_index(
        "clauses_version_number_key",
        "clauses",
        ["policy_version_id", "clause_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

