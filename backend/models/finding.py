"""Finding — a structured record of a conflict, redundancy, staleness flag,
coverage gap, or breach, unifying those detection-result shapes behind one
`finding_type` discriminator (see the domain model's design notes)."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from database.base import Base
from models.enums import DetectionMethod, FindingSeverity, FindingStatus, FindingType, pg_enum
from models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.company import Company
    from models.finding_clause_link import FindingClauseLink
    from models.regulatory_clause import RegulatoryClause
    from models.user import User


class Finding(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "findings"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    finding_type: Mapped[FindingType] = mapped_column(
        pg_enum(FindingType, "finding_type"), nullable=False
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        pg_enum(FindingSeverity, "finding_severity"), nullable=False
    )
    status: Mapped[FindingStatus] = mapped_column(
        pg_enum(FindingStatus, "finding_status"), nullable=False, default=FindingStatus.OPEN
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    detection_method: Mapped[DetectionMethod] = mapped_column(
        pg_enum(DetectionMethod, "detection_method"), nullable=False
    )
    proof_reference: Mapped[Optional[str]] = mapped_column(Text)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3))
    regulatory_clause_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("regulatory_clauses.id", ondelete="SET NULL")
    )
    resolved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    detected_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)

    company: Mapped["Company"] = relationship("Company", back_populates="findings")
    regulatory_clause: Mapped[Optional["RegulatoryClause"]] = relationship(
        "RegulatoryClause", back_populates="findings"
    )
    resolved_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys="[Finding.resolved_by_user_id]",
        back_populates="resolved_findings",
    )
    clause_links: Mapped[List["FindingClauseLink"]] = relationship(
        "FindingClauseLink", back_populates="finding"
    )
