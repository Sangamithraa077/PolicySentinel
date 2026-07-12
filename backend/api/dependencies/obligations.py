"""Dependency providers for obligation endpoints."""

from __future__ import annotations

from fastapi import Depends
from backend.api.dependencies.database import DbSession
from backend.services.obligation_management_service import ObligationManagementService


def get_obligation_management_service(
    db: DbSession
) -> ObligationManagementService:
    return ObligationManagementService(db)
