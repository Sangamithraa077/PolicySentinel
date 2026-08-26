"""Use case: persist a validated policy document as a new Policy +
PolicyVersion pair, storing its file along the way.

Talks to the ORM (models/) directly rather than through a repository
interface — no PolicyRepository abstraction exists yet, and building
one for this single write path would be premature; introduce it if a
second use case needs to reuse this persistence logic.

Every upload through this endpoint creates a brand-new Policy (there is
no "add a version to an existing policy" flow yet), owned by the given
company, with no department assignment — that's a later triage step.

The Policy row is flushed (INSERTed within the transaction, not yet
committed) before the file is stored, specifically so the file storage
service can organize the file under .../policies/{policy_id}/ — the
policy has to exist to be organized by. If anything fails afterward —
storage error, or the PolicyVersion insert itself — the transaction is
rolled back and, if the file was already written, it's deleted too, so
a failed upload never leaves an orphan behind in either the database or
storage.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.domain.exceptions.policy_exceptions import CompanyNotFoundError, UserNotFoundError
from backend.models.company import Company
from backend.models.enums import PolicyDocumentFileType, PolicyStatus, PolicyVersionStatus
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.user import User
from backend.services.file_storage_service import FileStorageService, StoredFile
from backend.services.validate_policy_document_service import ValidatedPolicyDocument

_EXTENSION_TO_FILE_TYPE: dict[str, PolicyDocumentFileType] = {
    ".txt": PolicyDocumentFileType.TXT,
    ".md": PolicyDocumentFileType.MD,
    ".pdf": PolicyDocumentFileType.PDF,
    ".docx": PolicyDocumentFileType.DOCX,
}


@dataclass(frozen=True)
class PersistedPolicyUpload:
    policy_id: uuid.UUID
    policy_version_id: uuid.UUID
    company_id: uuid.UUID
    policy_title: str
    version_number: int
    description: str | None
    uploaded_by_user_id: uuid.UUID
    original_filename: str
    stored_filename: str
    storage_path: str
    extension: str
    content_type: str
    size_bytes: int
    sha256: str
    uploaded_at: datetime


class PersistPolicyUploadService:
    def __init__(self, db: Session, file_storage: FileStorageService) -> None:
        self._db = db
        self._file_storage = file_storage

    def persist(
        self,
        validated: ValidatedPolicyDocument,
        *,
        company_id: uuid.UUID,
        uploaded_by_user_id: uuid.UUID,
        policy_title: str,
        version_number: int,
        description: str | None,
        auto_create_missing: bool = False,
    ) -> PersistedPolicyUpload:
        stored: StoredFile | None = None
        try:
            company = self._db.scalar(
                select(Company).where(Company.id == company_id, Company.deleted_at.is_(None))
            )
            if company is None:
                if auto_create_missing:
                    company = Company(
                        id=company_id,
                        name=f"Company {str(company_id)[:8]}",
                        industry="Technology",
                        jurisdiction="General",
                        registration_number=f"REG-{str(company_id)[:8].upper()}",
                    )
                    self._db.add(company)
                    self._db.flush()
                else:
                    raise CompanyNotFoundError(f"Company '{company_id}' does not exist.")

            uploader = self._db.scalar(
                select(User).where(User.id == uploaded_by_user_id, User.deleted_at.is_(None))
            )
            if uploader is None:
                if auto_create_missing:
                    from backend.models.enums import UserRole
                    uploader = User(
                        id=uploaded_by_user_id,
                        company_id=company.id,
                        email=f"user-{str(uploaded_by_user_id)[:8]}@{company.name.lower().replace(' ', '')}.com",
                        password_hash="",  # Not checking passwords for uploads, or set a dummy hashed one
                        full_name=f"User {str(uploaded_by_user_id)[:8]}",
                        role=UserRole.ADMIN,
                        is_active=True,
                    )
                    self._db.add(uploader)
                    self._db.flush()
                else:
                    raise UserNotFoundError(f"User '{uploaded_by_user_id}' does not exist.")

            policy = Policy(
                company=company,
                owning_department=None,
                title=policy_title,
                status=PolicyStatus.DRAFT,
            )
            self._db.add(policy)
            self._db.flush()  # allocates policy.id so the file can be organized under it

            stored = self._file_storage.store(
                validated.content,
                company_id=company.id,
                policy_id=policy.id,
                extension=validated.extension,
                content_type=validated.content_type,
            )

            # Auto-extract text for all supported document formats
            extracted_text: str | None = None
            try:
                from backend.services.document_parsing_service import build_default_document_parsing_service
                from backend.services.text_normalization_service import TextNormalizationService

                parsing_service = build_default_document_parsing_service()
                parsed_doc = parsing_service.parse(validated.content, validated.extension)
                normalizer = TextNormalizationService()
                normalized_doc = normalizer.normalize(parsed_doc.text)
                extracted_text = normalized_doc.text
                logger.info(
                    "Successfully extracted text (%d chars) from %s for policy %s",
                    len(extracted_text),
                    validated.extension,
                    policy.id,
                )
            except Exception as exc:
                logger.error("Failed to automatically extract text for policy %s: %s", policy.id, exc)

            version = PolicyVersion(
                policy=policy,
                version_number=version_number,
                source_file_reference=stored.storage_path,
                file_hash=stored.sha256,
                uploaded_by=uploader,
                status=PolicyVersionStatus.DRAFT,
                original_filename=validated.original_filename,
                size_bytes=stored.size_bytes,
                file_type=_EXTENSION_TO_FILE_TYPE[validated.extension],
                description=description,
                uploaded_at=stored.stored_at,
                extracted_text=extracted_text,
            )
            policy.current_version = version

            self._db.add(version)
            self._db.flush()

            # Record Policy Upload Audit Log
            from backend.services.compliance_dashboard_service import record_compliance_audit_log
            record_compliance_audit_log(
                self._db,
                company.id,
                "Policy Upload",
                uploader.email,
                f"Policy '{policy.title}' uploaded by {uploader.email} (File: {validated.original_filename})"
            )

            if extracted_text:
                record_compliance_audit_log(
                    self._db,
                    company.id,
                    "Text Extraction",
                    uploader.email,
                    f"Successfully extracted text from policy document '{validated.original_filename}'"
                )

            # Automatically run clause segmentation and store in database
            if extracted_text:
                try:
                    from backend.repositories.clause_repository import ClauseRepository
                    from backend.services.clause_segmentation_service import ClauseSegmentationService
                    from backend.services.store_segmented_clauses_service import StoreSegmentedClausesService

                    segmenter = ClauseSegmentationService()
                    segmented_clauses = segmenter.segment(extracted_text)

                    clause_repo = ClauseRepository(self._db)
                    store_service = StoreSegmentedClausesService(clause_repo)
                    store_service.store(
                        segmented_clauses,
                        policy_id=policy.id,
                        policy_version_id=version.id,
                    )
                    logger.info("Successfully automatically segmented and stored clauses for policy %s", policy.id)
                    record_compliance_audit_log(
                        self._db,
                        company.id,
                        "Clause Segmentation",
                        uploader.email,
                        f"Successfully segmented policy text into {len(segmented_clauses)} clauses"
                    )

                    # Automatically extract and store compliance obligations
                    try:
                        from backend.services.ai.obligation_extraction_pipeline_service import ObligationExtractionPipelineService
                        obligation_pipeline = ObligationExtractionPipelineService(self._db)
                        obligation_pipeline.run_pipeline(version.id)
                        logger.info("Successfully automatically extracted obligations for policy version %s", version.id)
                        record_compliance_audit_log(
                            self._db,
                            company.id,
                            "Obligation Extraction",
                            uploader.email,
                            f"Successfully extracted compliance obligations for policy version {version.version_number}"
                        )

                        # Run comparison pipeline to detect and persist conflicts
                        try:
                            from backend.services.comparison.comparison_pipeline_service import ComparisonPipelineService
                            comparison_pipeline = ComparisonPipelineService(self._db)
                            comparison_pipeline.run_pipeline(version.id)
                            logger.info("Successfully automatically compared and detected conflicts for policy version %s", version.id)
                            record_compliance_audit_log(
                                self._db,
                                company.id,
                                "Conflict Detection",
                                uploader.email,
                                f"Successfully completed semantic comparison and conflict detection for policy version {version.version_number}"
                            )
                        except Exception as exc:
                            logger.error("Failed to automatically run comparison pipeline for policy version %s: %s", version.id, exc)
                    except Exception as exc:
                        logger.error("Failed to automatically extract obligations for policy version %s: %s", version.id, exc)
                except Exception as exc:
                    logger.error("Failed to automatically segment and store clauses for policy %s: %s", policy.id, exc)

            self._db.commit()

            # Automatically synchronize metadata to Neo4j Knowledge Graph
            try:
                from backend.graph.graph_population_service import GraphPopulationService
                # Initialize new session from connection pool to be completely isolated and safe
                from backend.database.session import SessionLocal
                with SessionLocal() as sync_db:
                    sync_service = GraphPopulationService(sync_db)
                    logger.info("Automatically synchronizing policy %s to Neo4j graph...", policy.id)
                    sync_success = sync_service.sync_policy(policy.id)
                    if sync_success:
                        logger.info("Successfully automatically synchronized policy %s to Neo4j graph.", policy.id)
                    else:
                        logger.warning("Automatic graph sync failed for policy %s, but workflow continued.", policy.id)
            except Exception as sync_err:
                logger.error("Error during automatic graph synchronization for policy %s: %s", policy.id, sync_err)
        except Exception:
            self._db.rollback()
            if stored is not None:
                self._file_storage.delete(stored.storage_path)
            raise

        return PersistedPolicyUpload(
            policy_id=policy.id,
            policy_version_id=version.id,
            company_id=company.id,
            policy_title=policy.title,
            version_number=version.version_number,
            description=version.description,
            uploaded_by_user_id=uploader.id,
            original_filename=validated.original_filename,
            stored_filename=stored.stored_filename,
            storage_path=stored.storage_path,
            extension=validated.extension,
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
            sha256=stored.sha256,
            uploaded_at=stored.stored_at,
        )
