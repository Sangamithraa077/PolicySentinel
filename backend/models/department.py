"""Department — a business unit within a Company; supports a self-referential
parent/child hierarchy."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.models.company import Company
    from backend.models.policy import Policy
    from backend.models.user import User


class Department(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "departments"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    parent_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)

    company: Mapped["Company"] = relationship("Company", back_populates="departments")

    parent: Mapped[Optional["Department"]] = relationship(
        "Department", remote_side="Department.id", back_populates="children"
    )
    children: Mapped[List["Department"]] = relationship(
        "Department", back_populates="parent"
    )

    users: Mapped[List["User"]] = relationship("User", back_populates="department")
    policies: Mapped[List["Policy"]] = relationship(
        "Policy", back_populates="owning_department"
    )
