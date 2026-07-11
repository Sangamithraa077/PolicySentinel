"""Obligation — a specific, actionable duty a Clause imposes."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from models.enums import ObligationDeadlineType, ObligationPriority, ObligationStatus, pg_enum
from models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.clause import Clause
    from models.department import Department


class Obligation(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "obligations"

    clause_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("clauses.id", ondelete="CASCADE"), nullable=False
    )
    responsible_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action_required: Mapped[str] = mapped_column(Text, nullable=False)
    deadline_type: Mapped[ObligationDeadlineType] = mapped_column(
        pg_enum(ObligationDeadlineType, "obligation_deadline_type"), nullable=False
    )
    deadline_expression: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[ObligationPriority] = mapped_column(
        pg_enum(ObligationPriority, "obligation_priority"),
        nullable=False,
        default=ObligationPriority.MEDIUM,
    )
    status: Mapped[ObligationStatus] = mapped_column(
        pg_enum(ObligationStatus, "obligation_status"),
        nullable=False,
        default=ObligationStatus.ACTIVE,
    )

    clause: Mapped["Clause"] = relationship("Clause", back_populates="obligations")
    responsible_department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="obligations"
    )
