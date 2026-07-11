"""initial schema

Revision ID: 517c2ef6e254
Revises:
Create Date: 2026-07-11 11:10:39.732937

Brings an empty PostgreSQL database up to parity with every model in
`models/`: 16 enum types, 13 tables, all foreign keys / constraints /
indexes, and the two plpgsql trigger functions (`set_updated_at`,
`prevent_mutation`) with their per-table triggers.

Mirrors `docker/postgres/init/001_schema.sql` table-for-table — see
`backend/alembic/README.md` for why that file only bootstraps extensions
rather than duplicating this migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "517c2ef6e254"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# ---------------------------------------------------------------------------
# Enum types — one canonical definition each, used for the explicit
# create()/drop() calls below. Column definitions reference a
# create_type=False copy (see `_enum_ref`) so `op.create_table` doesn't
# also try to (re)issue `CREATE TYPE`.
# ---------------------------------------------------------------------------
user_role = postgresql.ENUM(
    "admin", "compliance_officer", "department_head", "auditor", "viewer", name="user_role"
)
policy_status = postgresql.ENUM("draft", "active", "archived", "superseded", name="policy_status")
policy_version_status = postgresql.ENUM(
    "draft", "under_review", "published", "superseded", name="policy_version_status"
)
clause_type = postgresql.ENUM(
    "obligation", "definition", "prohibition", "permission", "procedural", name="clause_type"
)
extraction_method = postgresql.ENUM("ai", "manual", name="extraction_method")
obligation_deadline_type = postgresql.ENUM(
    "one_time", "recurring", "conditional", name="obligation_deadline_type"
)
obligation_priority = postgresql.ENUM(
    "low", "medium", "high", "critical", name="obligation_priority"
)
obligation_status = postgresql.ENUM("active", "fulfilled", "breached", name="obligation_status")
mapping_type = postgresql.ENUM(
    "satisfies", "partially_satisfies", "references", name="mapping_type"
)
finding_type = postgresql.ENUM(
    "conflict", "redundancy", "staleness", "gap", "breach", name="finding_type"
)
finding_severity = postgresql.ENUM("low", "medium", "high", "critical", name="finding_severity")
finding_status = postgresql.ENUM(
    "open", "under_review", "resolved", "dismissed", name="finding_status"
)
detection_method = postgresql.ENUM(
    "z3_formal_proof", "ai_inference", "rule_based", name="detection_method"
)
finding_clause_role = postgresql.ENUM("primary", "counterpart", name="finding_clause_role")
audit_action = postgresql.ENUM(
    "created",
    "updated",
    "uploaded",
    "approved",
    "resolved",
    "dismissed",
    "deleted",
    "login",
    name="audit_action",
)
auditable_entity_type = postgresql.ENUM(
    "company",
    "department",
    "user",
    "policy",
    "policy_version",
    "clause",
    "obligation",
    "regulatory_framework",
    "regulatory_clause",
    "clause_regulatory_mapping",
    "finding",
    "finding_clause_link",
    name="auditable_entity_type",
)

ALL_ENUMS = [
    user_role,
    policy_status,
    policy_version_status,
    clause_type,
    extraction_method,
    obligation_deadline_type,
    obligation_priority,
    obligation_status,
    mapping_type,
    finding_type,
    finding_severity,
    finding_status,
    detection_method,
    finding_clause_role,
    audit_action,
    auditable_entity_type,
]


def _enum_ref(enum_type: postgresql.ENUM) -> postgresql.ENUM:
    """Reference an already-created enum type from a column definition
    without `op.create_table` attempting to `CREATE TYPE` it again."""
    return postgresql.ENUM(*enum_type.enums, name=enum_type.name, create_type=False)


SET_UPDATED_AT_FN = """
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql
"""

PREVENT_MUTATION_FN = """
CREATE OR REPLACE FUNCTION prevent_mutation()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION '% is append-only: % not permitted on row %', TG_TABLE_NAME, TG_OP, OLD.id;
END;
$$ LANGUAGE plpgsql
"""


def _updated_at_trigger(table: str) -> str:
    # op.execute() appends its own terminating `;` — don't include one here.
    return (
        f"CREATE TRIGGER trg_{table}_updated_at "
        f"BEFORE UPDATE ON {table} "
        f"FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )


def upgrade() -> None:
    bind = op.get_bind()

    # -- extensions (idempotent; also bootstrapped in docker/postgres/init/) --
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    # -- enum types --
    for enum_type in ALL_ENUMS:
        enum_type.create(bind, checkfirst=True)

    # -- shared trigger functions --
    op.execute(SET_UPDATED_AT_FN)
    op.execute(PREVENT_MUTATION_FN)

    # =========================================================== companies
    op.create_table(
        "companies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("industry", sa.Text(), nullable=True),
        sa.Column("jurisdiction", sa.Text(), nullable=True),
        sa.Column("registration_number", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("btrim(name) <> ''", name="companies_name_not_blank"),
    )
    op.create_index(
        "companies_registration_number_key",
        "companies",
        ["registration_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND registration_number IS NOT NULL"),
    )
    op.create_index(
        "companies_active_idx",
        "companies",
        ["is_active"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(_updated_at_trigger("companies"))

    # ========================================================== departments
    op.create_table(
        "departments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.CheckConstraint("btrim(name) <> ''", name="departments_name_not_blank"),
        sa.CheckConstraint(
            "parent_department_id IS DISTINCT FROM id", name="departments_parent_not_self"
        ),
    )
    op.create_index(
        "departments_company_id_idx",
        "departments",
        ["company_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "departments_parent_id_idx",
        "departments",
        ["parent_department_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "departments_company_code_key",
        "departments",
        ["company_id", "code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND code IS NOT NULL"),
    )
    op.execute(_updated_at_trigger("departments"))

    # ================================================================ users
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("role", _enum_ref(user_role), server_default=sa.text("'viewer'"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "email ~* '^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$'",
            name="users_email_format",
        ),
    )
    op.create_index(
        "users_email_key",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "users_company_id_idx",
        "users",
        ["company_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "users_department_id_idx",
        "users",
        ["department_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "users_role_idx", "users", ["role"], postgresql_where=sa.text("deleted_at IS NULL")
    )
    op.execute(_updated_at_trigger("users"))

    # ============================================================ policies
    # current_version_id -> policy_versions.id is circular; the FK is added
    # further down, once policy_versions exists.
    op.create_table(
        "policies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owning_department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("policy_code", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column(
            "status", _enum_ref(policy_status), server_default=sa.text("'draft'"), nullable=False
        ),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owning_department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("btrim(title) <> ''", name="policies_title_not_blank"),
    )
    op.create_index(
        "policies_company_id_idx",
        "policies",
        ["company_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "policies_department_id_idx",
        "policies",
        ["owning_department_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "policies_status_idx",
        "policies",
        ["status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "policies_company_code_key",
        "policies",
        ["company_id", "policy_code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND policy_code IS NOT NULL"),
    )
    op.execute(_updated_at_trigger("policies"))

    # ====================================================== policy_versions
    op.create_table(
        "policy_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("source_file_reference", sa.Text(), nullable=False),
        sa.Column("file_hash", sa.Text(), nullable=False),
        sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            _enum_ref(policy_version_status),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("superseded_by_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["superseded_by_version_id"], ["policy_versions.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint("version_number > 0", name="policy_versions_version_number_positive"),
        sa.CheckConstraint(
            "superseded_by_version_id IS DISTINCT FROM id",
            name="policy_versions_not_self_superseding",
        ),
    )
    op.create_index(
        "policy_versions_policy_id_idx",
        "policy_versions",
        ["policy_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "policy_versions_uploaded_by_idx",
        "policy_versions",
        ["uploaded_by_user_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "policy_versions_status_idx",
        "policy_versions",
        ["status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "policy_versions_superseded_by_idx",
        "policy_versions",
        ["superseded_by_version_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "policy_versions_policy_version_key",
        "policy_versions",
        ["policy_id", "version_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(_updated_at_trigger("policy_versions"))

    # -- close the circular reference from policies -> policy_versions --
    op.create_foreign_key(
        "policies_current_version_fk",
        "policies",
        "policy_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "policies_current_version_id_idx",
        "policies",
        ["current_version_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ================================================================ clauses
    op.create_table(
        "clauses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("policy_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clause_number", sa.Text(), nullable=False),
        sa.Column("heading", sa.Text(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("clause_type", _enum_ref(clause_type), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "extracted_by",
            _enum_ref(extraction_method),
            server_default=sa.text("'ai'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["policy_version_id"], ["policy_versions.id"], ondelete="CASCADE"),
        sa.CheckConstraint("btrim(text) <> ''", name="clauses_text_not_blank"),
    )
    op.create_index(
        "clauses_policy_version_id_idx",
        "clauses",
        ["policy_version_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "clauses_clause_type_idx",
        "clauses",
        ["clause_type"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "clauses_version_number_key",
        "clauses",
        ["policy_version_id", "clause_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(_updated_at_trigger("clauses"))

    # ============================================================ obligations
    op.create_table(
        "obligations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("clause_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("responsible_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("action_required", sa.Text(), nullable=False),
        sa.Column("deadline_type", _enum_ref(obligation_deadline_type), nullable=False),
        sa.Column("deadline_expression", sa.Text(), nullable=True),
        sa.Column(
            "priority",
            _enum_ref(obligation_priority),
            server_default=sa.text("'medium'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            _enum_ref(obligation_status),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["clause_id"], ["clauses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["responsible_department_id"], ["departments.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "obligations_clause_id_idx",
        "obligations",
        ["clause_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "obligations_department_id_idx",
        "obligations",
        ["responsible_department_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "obligations_status_idx",
        "obligations",
        ["status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(_updated_at_trigger("obligations"))

    # =================================================== regulatory_frameworks
    op.create_table(
        "regulatory_frameworks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("jurisdiction", sa.Text(), nullable=True),
        sa.Column("issuing_body", sa.Text(), nullable=True),
        sa.Column("edition_or_version", sa.Text(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("btrim(name) <> ''", name="regulatory_frameworks_name_not_blank"),
    )
    op.create_index(
        "regulatory_frameworks_name_edition_key",
        "regulatory_frameworks",
        ["name", "edition_or_version"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(_updated_at_trigger("regulatory_frameworks"))

    # ====================================================== regulatory_clauses
    op.create_table(
        "regulatory_clauses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("regulatory_framework_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clause_reference", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["regulatory_framework_id"], ["regulatory_frameworks.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "regulatory_clauses_framework_id_idx",
        "regulatory_clauses",
        ["regulatory_framework_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "regulatory_clauses_framework_reference_key",
        "regulatory_clauses",
        ["regulatory_framework_id", "clause_reference"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(_updated_at_trigger("regulatory_clauses"))

    # ================================================ clause_regulatory_mappings
    op.create_table(
        "clause_regulatory_mappings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("clause_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("regulatory_clause_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mapping_type", _enum_ref(mapping_type), nullable=False),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("verified_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["clause_id"], ["clauses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["regulatory_clause_id"], ["regulatory_clauses.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["verified_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1",
            name="crm_confidence_score_range",
        ),
        sa.CheckConstraint(
            "(verified_by_user_id IS NULL) = (verified_at IS NULL)",
            name="crm_verification_consistency",
        ),
    )
    op.create_index(
        "crm_clause_id_idx",
        "clause_regulatory_mappings",
        ["clause_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "crm_regulatory_clause_id_idx",
        "clause_regulatory_mappings",
        ["regulatory_clause_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "crm_verified_by_idx",
        "clause_regulatory_mappings",
        ["verified_by_user_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "crm_clause_regulatory_clause_key",
        "clause_regulatory_mappings",
        ["clause_id", "regulatory_clause_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(_updated_at_trigger("clause_regulatory_mappings"))

    # ================================================================ findings
    op.create_table(
        "findings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finding_type", _enum_ref(finding_type), nullable=False),
        sa.Column("severity", _enum_ref(finding_severity), nullable=False),
        sa.Column(
            "status", _enum_ref(finding_status), server_default=sa.text("'open'"), nullable=False
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("detection_method", _enum_ref(detection_method), nullable=False),
        sa.Column("proof_reference", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("regulatory_clause_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "detected_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["regulatory_clause_id"], ["regulatory_clauses.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1",
            name="findings_confidence_score_range",
        ),
        sa.CheckConstraint(
            "finding_type <> 'gap' OR regulatory_clause_id IS NOT NULL",
            name="findings_gap_requires_regulatory_clause",
        ),
        sa.CheckConstraint(
            "(status = 'resolved') = (resolved_at IS NOT NULL)",
            name="findings_resolution_consistency",
        ),
        sa.CheckConstraint(
            "resolved_at IS NULL OR resolved_at >= detected_at",
            name="findings_resolved_after_detected",
        ),
    )
    op.create_index(
        "findings_company_id_idx",
        "findings",
        ["company_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "findings_status_idx",
        "findings",
        ["status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "findings_type_idx",
        "findings",
        ["finding_type"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "findings_severity_idx",
        "findings",
        ["severity"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "findings_regulatory_clause_id_idx",
        "findings",
        ["regulatory_clause_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "findings_resolved_by_idx",
        "findings",
        ["resolved_by_user_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(_updated_at_trigger("findings"))

    # ======================================================= finding_clause_links
    op.create_table(
        "finding_clause_links",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clause_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_in_finding", _enum_ref(finding_clause_role), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clause_id"], ["clauses.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "fcl_finding_id_idx",
        "finding_clause_links",
        ["finding_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "fcl_clause_id_idx",
        "finding_clause_links",
        ["clause_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "fcl_finding_clause_key",
        "finding_clause_links",
        ["finding_id", "clause_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(_updated_at_trigger("finding_clause_links"))

    # =============================================================== audit_logs
    # Append-only: no updated_at/deleted_at columns, no update trigger.
    # entity_id is a polymorphic reference (see auditable_entity_type) and
    # intentionally carries no foreign key.
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", _enum_ref(audit_action), nullable=False),
        sa.Column("entity_type", _enum_ref(auditable_entity_type), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("before_state", postgresql.JSONB(), nullable=True),
        sa.Column("after_state", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column(
            "occurred_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("audit_logs_company_id_idx", "audit_logs", ["company_id"])
    op.create_index("audit_logs_actor_id_idx", "audit_logs", ["actor_user_id"])
    op.create_index("audit_logs_entity_idx", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("audit_logs_occurred_at_idx", "audit_logs", [sa.text("occurred_at DESC")])
    op.execute(
        "CREATE TRIGGER trg_audit_logs_immutable "
        "BEFORE UPDATE OR DELETE ON audit_logs "
        "FOR EACH ROW EXECUTE FUNCTION prevent_mutation()"
    )


def downgrade() -> None:
    bind = op.get_bind()

    # Break the policies <-> policy_versions cycle before dropping either.
    op.drop_constraint("policies_current_version_fk", "policies", type_="foreignkey")

    # Reverse creation order; dropping a table drops its own indexes,
    # constraints, and triggers automatically.
    op.drop_table("audit_logs")
    op.drop_table("finding_clause_links")
    op.drop_table("findings")
    op.drop_table("clause_regulatory_mappings")
    op.drop_table("regulatory_clauses")
    op.drop_table("regulatory_frameworks")
    op.drop_table("obligations")
    op.drop_table("clauses")
    op.drop_table("policy_versions")
    op.drop_table("policies")
    op.drop_table("users")
    op.drop_table("departments")
    op.drop_table("companies")

    op.execute("DROP FUNCTION IF EXISTS prevent_mutation()")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    for enum_type in reversed(ALL_ENUMS):
        enum_type.drop(bind, checkfirst=True)

    # Extensions are a shared resource (other objects may depend on them)
    # and are intentionally left in place — see docker/postgres/init/.
