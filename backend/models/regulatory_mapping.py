"""RegulatoryMapping — AI-generated mapping linking internal obligations to regulatory frameworks."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from backend.models.policy import Policy
    from backend.models.obligation import Obligation


class RegulatoryMapping(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "regulatory_mappings"

    policy_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
    )
    obligation_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("obligations.id", ondelete="CASCADE"),
        nullable=False,
    )
    framework_name: Mapped[str] = mapped_column(Text, nullable=False)
    regulation_id: Mapped[str] = mapped_column(Text, nullable=False)
    clause_number: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    ai_explanation: Mapped[str] = mapped_column(Text, nullable=False)

    policy: Mapped["Policy"] = relationship("Policy", back_populates="regulatory_mappings")
    obligation: Mapped["Obligation"] = relationship("Obligation", back_populates="regulatory_mappings")
