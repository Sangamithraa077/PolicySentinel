"""Dependency providers for clause endpoints."""

from __future__ import annotations

from fastapi import Depends

from backend.api.dependencies.database import DbSession
from backend.domain.interfaces.clause_repository_interface import ClauseRepositoryInterface
from backend.repositories.clause_repository import ClauseRepository
from backend.services.clause_management_service import ClauseManagementService


def get_clause_repository(db: DbSession) -> ClauseRepositoryInterface:
    return ClauseRepository(db)


def get_clause_management_service(
    clause_repository: ClauseRepositoryInterface = Depends(get_clause_repository),
) -> ClauseManagementService:
    return ClauseManagementService(clause_repository)
