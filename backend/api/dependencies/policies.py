"""Dependency providers for policy management endpoints."""

from __future__ import annotations

from fastapi import Depends

from api.dependencies.database import DbSession
from api.dependencies.uploads import get_file_storage_service
from services.file_storage_service import FileStorageService
from services.policy_management_service import PolicyManagementService


def get_policy_management_service(
    db: DbSession,
    file_storage: FileStorageService = Depends(get_file_storage_service),
) -> PolicyManagementService:
    return PolicyManagementService(db=db, file_storage=file_storage)
