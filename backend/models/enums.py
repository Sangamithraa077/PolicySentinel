"""Python mirrors of the native Postgres ENUM types created in
`docker/postgres/init/001_schema.sql`.

`create_type=False` on every column built with `pg_enum()` is required —
the types already exist in the database; letting SQLAlchemy attempt to
`CREATE TYPE` them again (e.g. during test-DB setup via
`Base.metadata.create_all()`) would fail.
"""
from __future__ import annotations

import enum
from typing import Type

from sqlalchemy import Enum as SqlEnum


def pg_enum(python_enum: Type[enum.Enum], name: str) -> SqlEnum:
    """Bind a Python str-enum to an existing native Postgres enum type."""
    return SqlEnum(
        python_enum,
        name=name,
        native_enum=True,
        create_type=False,
        validate_strings=True,
        values_callable=lambda cls: [member.value for member in cls],
    )


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    COMPLIANCE_OFFICER = "compliance_officer"
    DEPARTMENT_HEAD = "department_head"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class PolicyStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class PolicyVersionStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"


class ClauseType(str, enum.Enum):
    OBLIGATION = "obligation"
    DEFINITION = "definition"
    PROHIBITION = "prohibition"
    PERMISSION = "permission"
    PROCEDURAL = "procedural"


class ExtractionMethod(str, enum.Enum):
    AI = "ai"
    MANUAL = "manual"


class ObligationDeadlineType(str, enum.Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    CONDITIONAL = "conditional"


class ObligationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ObligationStatus(str, enum.Enum):
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    BREACHED = "breached"


class MappingType(str, enum.Enum):
    SATISFIES = "satisfies"
    PARTIALLY_SATISFIES = "partially_satisfies"
    REFERENCES = "references"


class FindingType(str, enum.Enum):
    CONFLICT = "conflict"
    REDUNDANCY = "redundancy"
    STALENESS = "staleness"
    GAP = "gap"
    BREACH = "breach"


class FindingSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class DetectionMethod(str, enum.Enum):
    Z3_FORMAL_PROOF = "z3_formal_proof"
    AI_INFERENCE = "ai_inference"
    RULE_BASED = "rule_based"


class FindingClauseRole(str, enum.Enum):
    PRIMARY = "primary"
    COUNTERPART = "counterpart"


class AuditAction(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    UPLOADED = "uploaded"
    APPROVED = "approved"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    DELETED = "deleted"
    LOGIN = "login"


class AuditableEntityType(str, enum.Enum):
    COMPANY = "company"
    DEPARTMENT = "department"
    USER = "user"
    POLICY = "policy"
    POLICY_VERSION = "policy_version"
    CLAUSE = "clause"
    OBLIGATION = "obligation"
    REGULATORY_FRAMEWORK = "regulatory_framework"
    REGULATORY_CLAUSE = "regulatory_clause"
    CLAUSE_REGULATORY_MAPPING = "clause_regulatory_mapping"
    FINDING = "finding"
    FINDING_CLAUSE_LINK = "finding_clause_link"
