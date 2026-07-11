"""FindingClauseLink — associative entity tying a Finding to every Clause
involved in it (one for a staleness flag, two or more for a conflict or
redundancy pair)."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from models.enums import FindingClauseRole, pg_enum
from models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.clause import Clause
    from models.finding import Finding


class FindingClauseLink(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "finding_clause_links"

    finding_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False
    )
    clause_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("clauses.id", ondelete="CASCADE"), nullable=False
    )
    role_in_finding: Mapped[Optional[FindingClauseRole]] = mapped_column(
        pg_enum(FindingClauseRole, "finding_clause_role")
    )

    finding: Mapped["Finding"] = relationship("Finding", back_populates="clause_links")
    clause: Mapped["Clause"] = relationship("Clause", back_populates="finding_links")
