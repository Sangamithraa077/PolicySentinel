"""Recommendation — structured AI resolution recommendations and redline suggestions for detected compliance conflicts."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.conflict import Conflict


class Recommendation(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "recommendations"

    conflict_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conflicts.id", ondelete="CASCADE"), nullable=False
    )
    
    recommendation_summary: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_action: Mapped[str] = mapped_column(Text, nullable=False)
    original_clause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    revised_clause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    ai_model: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="Pending")  # Pending, Accepted, Rejected

    conflict: Mapped["Conflict"] = relationship("Conflict", back_populates="recommendations")
