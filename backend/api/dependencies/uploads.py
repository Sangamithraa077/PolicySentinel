"""Dependency providers for upload endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import Depends

from api.dependencies.common import get_app_settings
from api.dependencies.database import DbSession
from config.settings import Settings
from domain.interfaces.file_storage_interface import FileStorageInterface
from repositories.local_file_storage_repository import LocalFileStorageRepository
from services.file_storage_service import FileStorageService
from services.persist_policy_upload_service import PersistPolicyUploadService
from services.validate_policy_document_service import ValidatePolicyDocumentService


def get_file_storage(settings: Settings = Depends(get_app_settings)) -> FileStorageInterface:
    return LocalFileStorageRepository(Path(settings.UPLOAD_DIR))


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
