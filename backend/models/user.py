"""User — an authenticated actor (RBAC via `role`), optionally scoped to a Department."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from backend.database.base import Base
from backend.models.enums import UserRole, pg_enum
from backend.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.audit_log import AuditLog
    from backend.models.clause_regulatory_mapping import ClauseRegulatoryMapping
    from backend.models.company import Company
    from backend.models.department import Department
    from backend.models.finding import Finding
    from backend.models.policy_version import PolicyVersion


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        pg_enum(UserRole, "user_role"), nullable=False, default=UserRole.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    company: Mapped["Company"] = relationship("Company", back_populates="users")
    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="users"
    )

    uploaded_policy_versions: Mapped[List["PolicyVersion"]] = relationship(
        "PolicyVersion",
        foreign_keys="[PolicyVersion.uploaded_by_user_id]",
        back_populates="uploaded_by",
    )
    resolved_findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        foreign_keys="[Finding.resolved_by_user_id]",
        back_populates="resolved_by",
    )
    verified_mappings: Mapped[List["ClauseRegulatoryMapping"]] = relationship(
        "ClauseRegulatoryMapping",
        foreign_keys="[ClauseRegulatoryMapping.verified_by_user_id]",
        back_populates="verified_by",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        foreign_keys="[AuditLog.actor_user_id]",
        back_populates="actor",
    )
