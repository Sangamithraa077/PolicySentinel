"""PolicyVersion — an immutable, uploaded revision of a Policy; the unit that
gets parsed into Clauses and evaluated for conflict/redundancy/staleness."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DATE, TIMESTAMP

from database.base import Base
from models.enums import PolicyVersionStatus, pg_enum
from models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.clause import Clause
    from models.policy import Policy
    from models.user import User


class PolicyVersion(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "policy_versions"

    policy_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    source_file_reference: Mapped[str] = mapped_column(Text, nullable=False)
    file_hash: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[PolicyVersionStatus] = mapped_column(
        pg_enum(PolicyVersionStatus, "policy_version_status"),
        nullable=False,
        default=PolicyVersionStatus.DRAFT,
    )
    effective_date: Mapped[Optional[date]] = mapped_column(DATE)
    superseded_by_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("policy_versions.id", ondelete="SET NULL")
    )
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )

    policy: Mapped["Policy"] = relationship(
        "Policy", foreign_keys="[PolicyVersion.policy_id]", back_populates="versions"
    )
    uploaded_by: Mapped["User"] = relationship(
        "User",
        foreign_keys="[PolicyVersion.uploaded_by_user_id]",
        back_populates="uploaded_policy_versions",
    )

    superseded_by: Mapped[Optional["PolicyVersion"]] = relationship(
        "PolicyVersion",
        remote_side="PolicyVersion.id",
        foreign_keys="[PolicyVersion.superseded_by_version_id]",
        back_populates="supersedes",
    )
    supersedes: Mapped[List["PolicyVersion"]] = relationship(
        "PolicyVersion",
        foreign_keys="[PolicyVersion.superseded_by_version_id]",
        back_populates="superseded_by",
    )

    clauses: Mapped[List["Clause"]] = relationship(
        "Clause", back_populates="policy_version"
    )
