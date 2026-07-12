"""Service for orchestrating the extraction and storage of obligations for a policy version."""

from __future__ import annotations

import logging
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.services.ai.obligation_extractor_service import ObligationExtractorService
from backend.config.settings import get_settings

logger = logging.getLogger(__name__)


class ObligationExtractionPipelineService:
    def __init__(self, db: Session, extractor_service: ObligationExtractorService | None = None) -> None:
        self._db = db
        self._extractor = extractor_service or ObligationExtractorService()

    def run_pipeline(self, policy_version_id: uuid.UUID) -> list[Obligation]:
        """Runs the obligation extraction pipeline for a given policy version.
        
        Reads all clauses, extracts obligations using Gemini, saves them,
        and continues processing even if a single clause fails.
        """
        logger.info("Starting obligation extraction pipeline for policy version: %s", policy_version_id)
        
        # 1. Read stored clauses
        clauses = self._db.scalars(
            select(Clause).where(
                Clause.policy_version_id == policy_version_id,
                Clause.deleted_at.is_(None)
            ).order_by(Clause.order_index)
        ).all()

        if not clauses:
            logger.warning("No clauses found for policy version: %s", policy_version_id)
            return []

        logger.info("Found %s clauses to process.", len(clauses))
        
        obligations: list[Obligation] = []
        ai_model_name = self._extractor._settings.GEMINI_MODEL
        
        for idx, clause in enumerate(clauses):
            logger.info("Processing clause %s/%s (ID: %s)", idx + 1, len(clauses), clause.id)
            
            try:
                if not clause.text.strip():
                    logger.info("Skipping empty clause: %s", clause.id)
                    continue
                
                # 2. Send clause to Gemini & Parse/Validate schema
                extracted = self._extractor.extract_obligation(clause.text)
                
                # 3. Instantiate Obligation record
                obligation = Obligation(
                    clause_id=clause.id,
                    policy_id=clause.policy_id,
                    subject=extracted.subject,
                    action=extracted.action,
                    object=extracted.object,
                    modality=extracted.modality,
                    conditions=extracted.conditions,
                    time_constraint=extracted.time_constraints,
                    compliance_category=extracted.compliance_category,
                    confidence_score=extracted.confidence_score,
                    ai_model=ai_model_name,
                )
                
                # 4. Store obligation in database
                self._db.add(obligation)
                self._db.flush()
                obligations.append(obligation)
                
                logger.info("Successfully extracted and stored obligation for clause %s (Obligation ID: %s)", clause.id, obligation.id)
                
            except Exception as exc:
                # 5. Continue processing even if one clause fails
                logger.error("Failed to extract obligation for clause %s: %s. Continuing...", clause.id, exc)
                continue

        # Commit all successfully extracted obligations
        try:
            self._db.commit()
            logger.info("Obligation extraction pipeline completed successfully. Stored %s obligations.", len(obligations))
        except Exception as exc:
            self._db.rollback()
            logger.error("Failed to commit extracted obligations to the database: %s", exc)
            raise

        return obligations
