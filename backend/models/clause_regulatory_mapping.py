"""ClauseRegulatoryMapping — associative entity recording that an internal
Clause satisfies (or references) an external RegulatoryClause."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from backend.database.base import Base
from backend.models.enums import MappingType, pg_enum
from backend.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.clause import Clause
    from backend.models.regulatory_clause import RegulatoryClause
    from backend.models.user import User


class ClauseRegulatoryMapping(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "clause_regulatory_mappings"

    clause_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("clauses.id", ondelete="CASCADE"), nullable=False
    )
    regulatory_clause_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regulatory_clauses.id", ondelete="CASCADE"),
        nullable=False,
    )
    mapping_type: Mapped[MappingType] = mapped_column(
        pg_enum(MappingType, "mapping_type"), nullable=False
    )
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3))
    verified_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    clause: Mapped["Clause"] = relationship(
        "Clause", back_populates="regulatory_mappings"
    )
    regulatory_clause: Mapped["RegulatoryClause"] = relationship(
        "RegulatoryClause", back_populates="mappings"
    )
    verified_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys="[ClauseRegulatoryMapping.verified_by_user_id]",
        back_populates="verified_mappings",
    )
