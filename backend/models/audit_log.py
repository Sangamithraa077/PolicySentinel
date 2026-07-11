"""AuditLog — append-only record of who did what, to which entity, and when.

Deliberately does NOT use `TimestampMixin` or `SoftDeleteMixin`: an audit
trail that could be edited or soft-deleted isn't an audit trail. The
`trg_audit_logs_immutable` trigger in 001_schema.sql enforces this at the
database level by rejecting UPDATE/DELETE outright.

`entity_id` is a polymorphic reference (discriminated by `entity_type`)
and intentionally carries no foreign key or `relationship()` — a single
audit table covering every auditable entity is the point, and a formal
FK per entity type would defeat that.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import TYPE_CHECKING, Any, Optional, Union

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from database.base import Base
from models.enums import AuditAction, AuditableEntityType, pg_enum
from models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.company import Company
    from models.user import User


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[AuditAction] = mapped_column(
        pg_enum(AuditAction, "audit_action"), nullable=False
    )
    entity_type: Mapped[AuditableEntityType] = mapped_column(
        pg_enum(AuditableEntityType, "auditable_entity_type"), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    before_state: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    after_state: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    ip_address: Mapped[Optional[Union[IPv4Address, IPv6Address]]] = mapped_column(INET)
    occurred_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )

    company: Mapped["Company"] = relationship("Company", back_populates="audit_logs")
    actor: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys="[AuditLog.actor_user_id]",
        back_populates="audit_logs",
    )
