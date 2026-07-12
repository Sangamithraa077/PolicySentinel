"""ComplianceAuditLog — append-only immutable audit trail record for tracking policySentinel actions."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.database.base import Base
from backend.models.mixins import UUIDPrimaryKeyMixin


class ComplianceAuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "compliance_audit_logs"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    user_identifier: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    company: Mapped["Company"] = relationship("Company")
