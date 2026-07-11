"""Policy — the stable identity of a policy across its lifetime; the versions
are what actually change.

`current_version_id` and `policy_versions.policy_id` form a circular
foreign-key pair (see 001_schema.sql, where the FK is added via a
deferred `ALTER TABLE` after `policy_versions` is created). `post_update`
tells SQLAlchemy's unit of work to resolve that cycle with a follow-up
UPDATE rather than failing to order the INSERTs.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.models.enums import PolicyStatus, pg_enum
from backend.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.clause import Clause
    from backend.models.company import Company
    from backend.models.department import Department
    from backend.models.policy_version import PolicyVersion


class Policy(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "policies"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    # Nullable: a policy created via upload (see
    # services/persist_policy_upload_service.py) isn't assigned to a
    # department yet — that happens in a later triage step.
    owning_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("departments.id", ondelete="RESTRICT")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    policy_code: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[PolicyStatus] = mapped_column(
        pg_enum(PolicyStatus, "policy_status"), nullable=False, default=PolicyStatus.DRAFT
    )
    current_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("policy_versions.id", ondelete="SET NULL")
    )

    company: Mapped["Company"] = relationship("Company", back_populates="policies")
    owning_department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="policies"
    )

    versions: Mapped[List["PolicyVersion"]] = relationship(
        "PolicyVersion",
        foreign_keys="[PolicyVersion.policy_id]",
        back_populates="policy",
    )
    current_version: Mapped[Optional["PolicyVersion"]] = relationship(
        "PolicyVersion",
        foreign_keys="[Policy.current_version_id]",
        post_update=True,
    )
    clauses: Mapped[List["Clause"]] = relationship("Clause", back_populates="policy")
