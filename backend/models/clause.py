"""Clause — a discrete, extracted provision of a PolicyVersion; the atomic
unit that conflicts, redundancy, and regulatory mappings operate on.

`policy_id` duplicates what `policy_version_id` -> `policy_versions.policy_id`
already implies, kept as its own column/FK so callers (and queries) can
filter by policy without a join — the two must always agree, but nothing
in this layer enforces that beyond both being set together by whichever
service writes the row (see services/store_segmented_clauses_service.py).

`parent_clause_id` is a self-referential FK supporting the hierarchy
clause segmentation produces (heading -> subheading -> list item ->
bullet); `clause_type` and `clause_number` are nullable because
segmentation (services/clause_segmentation_service.py) only determines
document structure, not what a clause means or whether it even carries
a number (body/bullet text doesn't) — classification is a later, likely
AI-assisted step this layer doesn't require up front.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.models.enums import ClauseType, ExtractionMethod, pg_enum
from backend.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.clause_regulatory_mapping import ClauseRegulatoryMapping
    from backend.models.finding_clause_link import FindingClauseLink
    from backend.models.obligation import Obligation
    from backend.models.policy import Policy
    from backend.models.policy_version import PolicyVersion


class Clause(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "clauses"

    policy_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    policy_version_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("policy_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_clause_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("clauses.id", ondelete="CASCADE")
    )
    clause_number: Mapped[Optional[str]] = mapped_column(Text)
    heading: Mapped[Optional[str]] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    clause_type: Mapped[Optional[ClauseType]] = mapped_column(pg_enum(ClauseType, "clause_type"))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extracted_by: Mapped[ExtractionMethod] = mapped_column(
        pg_enum(ExtractionMethod, "extraction_method"),
        nullable=False,
        default=ExtractionMethod.AI,
    )

    policy: Mapped["Policy"] = relationship("Policy", back_populates="clauses")
    policy_version: Mapped["PolicyVersion"] = relationship(
        "PolicyVersion", back_populates="clauses"
    )

    parent: Mapped[Optional["Clause"]] = relationship(
        "Clause", remote_side="Clause.id", back_populates="children"
    )
    children: Mapped[List["Clause"]] = relationship("Clause", back_populates="parent")

    obligations: Mapped[List["Obligation"]] = relationship(
        "Obligation", back_populates="clause"
    )
    regulatory_mappings: Mapped[List["ClauseRegulatoryMapping"]] = relationship(
        "ClauseRegulatoryMapping", back_populates="clause"
    )
    finding_links: Mapped[List["FindingClauseLink"]] = relationship(
        "FindingClauseLink", back_populates="clause"
    )
