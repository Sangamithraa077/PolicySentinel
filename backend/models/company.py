"""Company — the multi-tenant root; the regulated institution using the platform."""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.audit_log import AuditLog
    from backend.models.department import Department
    from backend.models.finding import Finding
    from backend.models.policy import Policy
    from backend.models.user import User


class Company(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(Text)
    jurisdiction: Mapped[Optional[str]] = mapped_column(Text)
    registration_number: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    departments: Mapped[List["Department"]] = relationship(
        "Department", back_populates="company"
    )
    users: Mapped[List["User"]] = relationship("User", back_populates="company")
    policies: Mapped[List["Policy"]] = relationship("Policy", back_populates="company")
    findings: Mapped[List["Finding"]] = relationship("Finding", back_populates="company")
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="company"
    )
