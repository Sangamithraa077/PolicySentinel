"""Dependency providers for upload endpoints."""

from __future__ import annotations

from fastapi import Depends

from backend.api.dependencies.common import get_app_settings
from backend.api.dependencies.database import DbSession
from backend.config.settings import Settings
from backend.domain.interfaces.file_storage_interface import FileStorageInterface
from backend.repositories.postgres_file_storage_repository import PostgresFileStorageRepository
from backend.services.file_storage_service import FileStorageService
from backend.services.persist_policy_upload_service import PersistPolicyUploadService
from backend.services.validate_policy_document_service import ValidatePolicyDocumentService


def get_file_storage(db: DbSession) -> FileStorageInterface:
    # Postgres-backed, not `LocalFileStorageRepository` — Render's free-tier
    # web services have ephemeral local disk, which loses every uploaded
    # file on the next deploy/restart (see models/file_blob.py). Shares
    # `db` with whatever else the request already uses, so a file write
    # and its owning Policy/PolicyVersion rows commit/roll back together.
    return PostgresFileStorageRepository(db)


def get_file_storage_service(
    storage: FileStorageInterface = Depends(get_file_storage),
) -> FileStorageService:
    return FileStorageService(storage)


def get_validate_policy_document_service(
    settings: Settings = Depends(get_app_settings),
) -> ValidatePolicyDocumentService:
    return ValidatePolicyDocumentService(max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB)


def get_persist_policy_upload_service(
    db: DbSession,
    file_storage: FileStorageService = Depends(get_file_storage_service),
) -> PersistPolicyUploadService:
    return PersistPolicyUploadService(db=db, file_storage=file_storage)
