"""Dependency providers for policy management endpoints."""

from __future__ import annotations

from fastapi import Depends

from backend.api.dependencies.clauses import get_clause_repository
from backend.api.dependencies.database import DbSession
from backend.api.dependencies.uploads import get_file_storage_service
from backend.domain.interfaces.clause_repository_interface import ClauseRepositoryInterface
from backend.services.file_storage_service import FileStorageService
from backend.services.policy_management_service import PolicyManagementService


def get_policy_management_service(
    db: DbSession,
    file_storage: FileStorageService = Depends(get_file_storage_service),
    clause_repository: ClauseRepositoryInterface = Depends(get_clause_repository),
) -> PolicyManagementService:
    return PolicyManagementService(
        db=db, file_storage=file_storage, clause_repository=clause_repository
    )
