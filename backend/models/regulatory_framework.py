"""RegulatoryFramework — a named body of external regulation (GDPR, SOX, Basel III)."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DATE

from backend.database.base import Base
from backend.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.regulatory_clause import RegulatoryClause


class RegulatoryFramework(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "regulatory_frameworks"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    jurisdiction: Mapped[Optional[str]] = mapped_column(Text)
    issuing_body: Mapped[Optional[str]] = mapped_column(Text)
    edition_or_version: Mapped[Optional[str]] = mapped_column(Text)
    effective_date: Mapped[Optional[date]] = mapped_column(DATE)
    description: Mapped[Optional[str]] = mapped_column(Text)

    regulatory_clauses: Mapped[List["RegulatoryClause"]] = relationship(
        "RegulatoryClause", back_populates="framework"
    )
