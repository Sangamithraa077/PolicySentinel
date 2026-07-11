"""Clause — a discrete, extracted provision of a PolicyVersion; the atomic
unit that conflicts, redundancy, and regulatory mappings operate on."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from models.enums import ClauseType, ExtractionMethod, pg_enum
from models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.clause_regulatory_mapping import ClauseRegulatoryMapping
    from models.finding_clause_link import FindingClauseLink
    from models.obligation import Obligation
    from models.policy_version import PolicyVersion


class Clause(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "clauses"

    policy_version_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("policy_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    clause_number: Mapped[str] = mapped_column(Text, nullable=False)
    heading: Mapped[Optional[str]] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    clause_type: Mapped[ClauseType] = mapped_column(
        pg_enum(ClauseType, "clause_type"), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extracted_by: Mapped[ExtractionMethod] = mapped_column(
        pg_enum(ExtractionMethod, "extraction_method"),
        nullable=False,
        default=ExtractionMethod.AI,
    )

    policy_version: Mapped["PolicyVersion"] = relationship(
        "PolicyVersion", back_populates="clauses"
    )
    obligations: Mapped[List["Obligation"]] = relationship(
        "Obligation", back_populates="clause"
    )
    regulatory_mappings: Mapped[List["ClauseRegulatoryMapping"]] = relationship(
        "ClauseRegulatoryMapping", back_populates="clause"
    )
    finding_links: Mapped[List["FindingClauseLink"]] = relationship(
        "FindingClauseLink", back_populates="clause"
    )
