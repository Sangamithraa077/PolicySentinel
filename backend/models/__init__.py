"""SQLAlchemy 2.x ORM models mapping onto `docker/postgres/init/001_schema.sql`.

Every model is imported here so `Base.metadata` sees the full set and so
that string-based `relationship()` targets (e.g. `"PolicyVersion"`) can be
resolved regardless of which module is imported first.
"""
from backend.database.base import Base
from backend.models.audit_log import AuditLog
from backend.models.clause import Clause
from backend.models.clause_regulatory_mapping import ClauseRegulatoryMapping
from backend.models.company import Company
from backend.models.department import Department
from backend.models.finding import Finding
from backend.models.finding_clause_link import FindingClauseLink
from backend.models.obligation import Obligation
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.regulatory_clause import RegulatoryClause
from backend.models.regulatory_framework import RegulatoryFramework
from backend.models.user import User

__all__ = [
    "Base",
    "Company",
    "Department",
    "User",
    "Policy",
    "PolicyVersion",
    "Clause",
    "Obligation",
    "RegulatoryFramework",
    "RegulatoryClause",
    "ClauseRegulatoryMapping",
    "Finding",
    "FindingClauseLink",
    "AuditLog",
]
