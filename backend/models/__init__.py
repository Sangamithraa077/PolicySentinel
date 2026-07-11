"""SQLAlchemy 2.x ORM models mapping onto `docker/postgres/init/001_schema.sql`.

Every model is imported here so `Base.metadata` sees the full set and so
that string-based `relationship()` targets (e.g. `"PolicyVersion"`) can be
resolved regardless of which module is imported first.
"""
from database.base import Base
from models.audit_log import AuditLog
from models.clause import Clause
from models.clause_regulatory_mapping import ClauseRegulatoryMapping
from models.company import Company
from models.department import Department
from models.finding import Finding
from models.finding_clause_link import FindingClauseLink
from models.obligation import Obligation
from models.policy import Policy
from models.policy_version import PolicyVersion
from models.regulatory_clause import RegulatoryClause
from models.regulatory_framework import RegulatoryFramework
from models.user import User

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
