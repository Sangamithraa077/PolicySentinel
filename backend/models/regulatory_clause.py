"""RegulatoryClause — a single citable provision within a RegulatoryFramework
(e.g. "Art. 17(1)")."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.clause_regulatory_mapping import ClauseRegulatoryMapping
    from backend.models.finding import Finding
    from backend.models.regulatory_framework import RegulatoryFramework


class RegulatoryClause(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "regulatory_clauses"

    regulatory_framework_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regulatory_frameworks.id", ondelete="CASCADE"),
        nullable=False,
    )
    clause_reference: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(Text)

    framework: Mapped["RegulatoryFramework"] = relationship(
        "RegulatoryFramework", back_populates="regulatory_clauses"
    )
    mappings: Mapped[List["ClauseRegulatoryMapping"]] = relationship(
        "ClauseRegulatoryMapping", back_populates="regulatory_clause"
    )
    findings: Mapped[List["Finding"]] = relationship(
        "Finding", back_populates="regulatory_clause"
    )
