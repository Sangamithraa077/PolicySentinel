"""add clause hierarchy and ownership

Revision ID: d7a145d9bdc8
Revises: 881fa18357a3
Create Date: 2026-07-11 17:30:00.000000

Brings the `clauses` table up to what clause segmentation
(services/clause_segmentation_service.py) and its persistence layer
(repositories/clause_repository.py) need:

  - `policy_id`, a direct FK to `policies` alongside the existing
    `policy_version_id`, so callers can filter/query by policy without
    a join through policy_versions.
  - `parent_clause_id`, a self-referential FK supporting the
    heading -> subheading -> list item -> bullet hierarchy segmentation
    produces. `ON DELETE CASCADE` so a removed clause takes its
    descendants with it, matching the containment semantics of the
    hierarchy (unlike departments.parent_department_id's SET NULL,
    which models a reporting line, not containment).
  - `clause_number` relaxed to nullable: segmentation produces
    unnumbered clauses too (body/preamble text, bullet points) that
    still need to be stored. Postgres treats each NULL as distinct for
    the existing `clauses_version_number_key` unique index, so multiple
    unnumbered clauses per policy version were never blocked by it.
  - `clause_type` relaxed to nullable: segmentation only determines
    document structure, not what a clause means — classification is a
    separate, likely AI-assisted step this migration doesn't require
    up front.
  - `extraction_method` gains a `rule_based` value, since this
    pipeline (parsing -> normalization -> segmentation -> storage)
    never calls the AI layer and `manual` would misleadingly imply a
    human did it.

`policy_id` is added nullable, backfilled from
`policy_versions.policy_id` via the existing `policy_version_id` link,
then tightened to NOT NULL — safe whether or not `clauses` already has
rows, unlike the previous migration's "assume the table is empty"
shortcut for policy_versions' new columns.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7a145d9bdc8"
down_revision: str | Sequence[str] | None = "881fa18357a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Postgres forbids using a freshly added enum value in the same
    # transaction that adds it, so this must run and commit before any
    # row in this migration (there are none) could reference it.
    op.execute("ALTER TYPE extraction_method ADD VALUE IF NOT EXISTS 'rule_based'")

    op.add_column("clauses", sa.Column("policy_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        "UPDATE clauses SET policy_id = policy_versions.policy_id "
        "FROM policy_versions WHERE clauses.policy_version_id = policy_versions.id"
    )
    op.alter_column("clauses", "policy_id", nullable=False)
    op.create_foreign_key(
        "clauses_policy_id_fkey", "clauses", "policies", ["policy_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index(
        "clauses_policy_id_idx",
        "clauses",
        ["policy_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.add_column(
        "clauses", sa.Column("parent_clause_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "clauses_parent_clause_id_fkey",
        "clauses",
        "clauses",
        ["parent_clause_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "clauses_parent_not_self", "clauses", "parent_clause_id IS DISTINCT FROM id"
    )
    op.create_index(
        "clauses_parent_clause_id_idx",
        "clauses",
        ["parent_clause_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.alter_column("clauses", "clause_number", nullable=True)
    op.alter_column("clauses", "clause_type", nullable=True)


def downgrade() -> None:
    op.alter_column("clauses", "clause_type", nullable=False)
    op.alter_column("clauses", "clause_number", nullable=False)

    op.drop_index("clauses_parent_clause_id_idx", table_name="clauses")
    op.drop_constraint("clauses_parent_not_self", "clauses", type_="check")
    op.drop_constraint("clauses_parent_clause_id_fkey", "clauses", type_="foreignkey")
    op.drop_column("clauses", "parent_clause_id")

    op.drop_index("clauses_policy_id_idx", table_name="clauses")
    op.drop_constraint("clauses_policy_id_fkey", "clauses", type_="foreignkey")
    op.drop_column("clauses", "policy_id")

    # Postgres has no `ALTER TYPE ... DROP VALUE` — removing 'rule_based'
    # would require rebuilding the enum type, which is not worth doing
    # for a downgrade path. Left in place; harmless if unused.
