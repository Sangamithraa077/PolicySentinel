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

from sqlalchemy import select, func
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
    company_name: str
    policy_title: str
    version_number: int
    description: str | None
    uploaded_by_user_id: uuid.UUID
    uploaded_by_name: str
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
        company_id: uuid.UUID | str | None = None,
        company_name: str | None = None,
        uploaded_by_user_id: uuid.UUID | str | None = None,
        uploaded_by_name: str | None = None,
        policy_title: str,
        version_number: int,
        description: str | None,
        auto_create_missing: bool = True,
    ) -> PersistedPolicyUpload:
        stored: StoredFile | None = None
        try:
            # 1. Resolve Company
            company = None
            if company_name and company_name.strip():
                c_name = company_name.strip()
                company = self._db.scalar(
                    select(Company).where(
                        func.lower(Company.name) == c_name.lower(),
                        Company.deleted_at.is_(None)
                    )
                )
                if company is None:
                    new_cid = None
                    if company_id:
                        try:
                            new_cid = uuid.UUID(str(company_id))
                        except (ValueError, TypeError):
                            pass
                    if not new_cid:
                        new_cid = uuid.uuid4()
                    
                    company = Company(
                        id=new_cid,
                        name=c_name,
                        industry="Enterprise",
                        jurisdiction="General",
                        registration_number=f"REG-{str(new_cid)[:8].upper()}",
                    )
                    self._db.add(company)
                    self._db.flush()

            if company is None and company_id:
                cid = None
                try:
                    cid = uuid.UUID(str(company_id))
                except (ValueError, TypeError):
                    c_name = str(company_id).strip()
                    company = self._db.scalar(
                        select(Company).where(
                            func.lower(Company.name) == c_name.lower(),
                            Company.deleted_at.is_(None)
                        )
                    )
                    if company is None:
                        new_cid = uuid.uuid4()
                        company = Company(
                            id=new_cid,
                            name=c_name,
                            industry="Enterprise",
                            jurisdiction="General",
                            registration_number=f"REG-{str(new_cid)[:8].upper()}",
                        )
                        self._db.add(company)
                        self._db.flush()

                if company is None and cid:
                    company = self._db.scalar(
                        select(Company).where(Company.id == cid, Company.deleted_at.is_(None))
                    )
                    if company is None:
                        if auto_create_missing:
                            company = Company(
                                id=cid,
                                name=f"Company {str(cid)[:8]}",
                                industry="Enterprise",
                                jurisdiction="General",
                                registration_number=f"REG-{str(cid)[:8].upper()}",
                            )
                            self._db.add(company)
                            self._db.flush()
                        else:
                            raise CompanyNotFoundError(f"Company '{cid}' does not exist.")

            if company is None:
                first_c = self._db.scalar(select(Company).where(Company.deleted_at.is_(None)).order_by(Company.created_at))
                if first_c:
                    company = first_c
                else:
                    new_cid = uuid.uuid4()
                    company = Company(
                        id=new_cid,
                        name="Default Organization",
                        industry="Enterprise",
                        jurisdiction="General",
                        registration_number=f"REG-{str(new_cid)[:8].upper()}",
                    )
                    self._db.add(company)
                    self._db.flush()

            # 2. Resolve Uploader User
            uploader = None
            u_name = (uploaded_by_name or "").strip() or "Compliance Officer"
            from backend.models.enums import UserRole

            # 1) Check if user by name already exists under THIS company
            uploader = self._db.scalar(
                select(User).where(
                    func.lower(User.full_name) == u_name.lower(),
                    User.company_id == company.id,
                    User.deleted_at.is_(None)
                )
            )

            # 2) If uploaded_by_user_id provided, check if it belongs to THIS company
            if uploader is None and uploaded_by_user_id:
                try:
                    uid = uuid.UUID(str(uploaded_by_user_id))
                    existing_user = self._db.scalar(
                        select(User).where(User.id == uid, User.deleted_at.is_(None))
                    )
                    if existing_user and existing_user.company_id == company.id:
                        uploader = existing_user
                except (ValueError, TypeError):
                    pass

            # 3) Check if company already has any user we can use
            if uploader is None:
                any_user_in_comp = self._db.scalar(
                    select(User).where(User.company_id == company.id, User.deleted_at.is_(None))
                )
                if any_user_in_comp and not (uploaded_by_name or "").strip():
                    uploader = any_user_in_comp

            # 4) Create a fresh user for this company with a NEW UUID and unique email
            if uploader is None:
                new_uid = uuid.uuid4()
                clean_user = "".join(c for c in u_name.lower() if c.isalnum()) or "user"
                clean_comp = "".join(c for c in company.name.lower() if c.isalnum()) or "company"
                candidate_email = f"{clean_user}@{clean_comp}.com"

                # Check if email is already taken in the system
                email_exists = self._db.scalar(
                    select(User).where(func.lower(User.email) == candidate_email.lower(), User.deleted_at.is_(None))
                )
                if email_exists:
                    candidate_email = f"{clean_user}-{str(new_uid)[:8]}@{clean_comp}.com"

                uploader = User(
                    id=new_uid,
                    company_id=company.id,
                    email=candidate_email,
                    password_hash="",
                    full_name=u_name,
                    role=UserRole.ADMIN,
                    is_active=True,
                )
                self._db.add(uploader)
                self._db.flush()

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

                    self._db.commit()

                    # Launch background thread for AI obligation extraction, conflict analysis & Neo4j sync
                    # so that upload HTTP request returns INSTANTLY (< 1 sec) to the user UI!
                    import threading

                    def _run_async_ai_pipeline(version_id: uuid.UUID, company_id: uuid.UUID, uploader_email: str, policy_id: uuid.UUID, v_num: int):
                        from backend.database.session import SessionLocal
                        from backend.services.compliance_dashboard_service import record_compliance_audit_log
                        with SessionLocal() as bg_db:
                            try:
                                from backend.services.ai.obligation_extraction_pipeline_service import ObligationExtractionPipelineService
                                obligation_pipeline = ObligationExtractionPipelineService(bg_db)
                                obligation_pipeline.run_pipeline(version_id)
                                logger.info("Successfully extracted obligations for policy version %s", version_id)
                                record_compliance_audit_log(
                                    bg_db,
                                    company_id,
                                    "Obligation Extraction",
                                    uploader_email,
                                    f"Successfully extracted compliance obligations for policy version {v_num}"
                                )
                                bg_db.commit()

                                from backend.services.comparison.comparison_pipeline_service import ComparisonPipelineService
                                comparison_pipeline = ComparisonPipelineService(bg_db)
                                comparison_pipeline.run_pipeline(version_id)
                                logger.info("Successfully compared and detected conflicts for policy version %s", version_id)
                                record_compliance_audit_log(
                                    bg_db,
                                    company_id,
                                    "Conflict Detection",
                                    uploader_email,
                                    f"Successfully completed semantic comparison and conflict detection for policy version {v_num}"
                                )
                                bg_db.commit()

                                from backend.graph.graph_population_service import GraphPopulationService
                                sync_service = GraphPopulationService(bg_db)
                                logger.info("Synchronizing policy %s to Neo4j graph...", policy_id)
                                sync_service.sync_policy(policy_id)
                                logger.info("Successfully synchronized policy %s to Neo4j graph", policy_id)
                            except Exception as exc:
                                logger.error("Background AI pipeline error for version %s: %s", version_id, exc)

                    threading.Thread(
                        target=_run_async_ai_pipeline,
                        args=(version.id, company.id, uploader.email, policy.id, version.version_number),
                        daemon=True
                    ).start()
                except Exception as exc:
                    logger.error("Failed to automatically segment and store clauses for policy %s: %s", policy.id, exc)
                    self._db.commit()
            else:
                self._db.commit()
        except Exception:
            self._db.rollback()
            if stored is not None:
                self._file_storage.delete(stored.storage_path)
            raise

        return PersistedPolicyUpload(
            policy_id=policy.id,
            policy_version_id=version.id,
            company_id=company.id,
            company_name=company.name,
            policy_title=policy.title,
            version_number=version.version_number,
            description=version.description,
            uploaded_by_user_id=uploader.id,
            uploaded_by_name=uploader.full_name,
            original_filename=validated.original_filename,
            stored_filename=stored.stored_filename,
            storage_path=stored.storage_path,
            extension=validated.extension,
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
            sha256=stored.sha256,
            uploaded_at=stored.stored_at,
        )
