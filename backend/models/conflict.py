"""Conflict — a structured compliance conflict between policy obligations detected by AI comparison."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.policy import Policy
    from backend.models.obligation import Obligation
    from backend.models.recommendation import Recommendation


class Conflict(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "conflicts"

    source_policy_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    target_policy_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False
    )
    source_obligation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("obligations.id", ondelete="SET NULL"), nullable=True
    )
    target_obligation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("obligations.id", ondelete="SET NULL"), nullable=True
    )
    
    conflict_type: Mapped[str] = mapped_column(Text, nullable=False)  # duplicate, contradiction, missing
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)  # low, medium, high
    ai_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="Open")  # Open, Reviewed, Resolved
    
    # Relationship Classification fields
    relationship_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Explicit foreign_keys definitions to disambiguate multiple relations to same tables
    source_policy: Mapped["Policy"] = relationship("Policy", foreign_keys=[source_policy_id])
    target_policy: Mapped["Policy"] = relationship("Policy", foreign_keys=[target_policy_id])
    source_obligation: Mapped[Optional["Obligation"]] = relationship("Obligation", foreign_keys=[source_obligation_id])
    target_obligation: Mapped[Optional["Obligation"]] = relationship("Obligation", foreign_keys=[target_obligation_id])
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="conflict", cascade="all, delete-orphan")
