"""Service for orchestrating semantic comparison and conflict detection against existing policies on new uploads."""

from __future__ import annotations

import logging
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.obligation import Obligation
from backend.models.conflict import Conflict
from backend.services.comparison.semantic_comparison_service import SemanticComparisonService
from backend.services.comparison.conflict_detection_engine import ConflictDetectionEngine

logger = logging.getLogger(__name__)


class ComparisonPipelineService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def run_pipeline(self, new_policy_version_id: uuid.UUID) -> list[Conflict]:
        """Runs the comparison and conflict detection pipeline between a new version and existing active policies."""
        new_version = self._db.get(PolicyVersion, new_policy_version_id)
        if new_version is None:
            logger.error("New policy version %s not found. Aborting comparison pipeline.", new_policy_version_id)
            return []

        new_policy = new_version.policy
        logger.info(
            "Starting semantic comparison pipeline for new policy: %s (Version: %s)", 
            new_policy.id, 
            new_version.id
        )

        # Retrieve all other policies belonging to the same company
        existing_policies = self._db.scalars(
            select(Policy)
            .where(
                Policy.company_id == new_policy.company_id,
                Policy.id != new_policy.id,
                Policy.deleted_at.is_(None)
            )
        ).all()

        logger.info("Found %s existing policies to compare against.", len(existing_policies))

        from backend.services.ai.conflict_explanation_service import ConflictExplanationService
        explanation_service = ConflictExplanationService()

        comp_service = SemanticComparisonService(self._db)
        conflict_engine = ConflictDetectionEngine(self._db)
        all_conflicts: list[Conflict] = []

        for existing_policy in existing_policies:
            if not existing_policy.current_version_id:
                logger.info("Skipping policy %s because it has no current version.", existing_policy.id)
                continue

            logger.info("Comparing new version %s with existing policy %s (Version: %s)", 
                        new_version.id, existing_policy.id, existing_policy.current_version_id)

            try:
                # 1. Run pairwise semantic comparisons
                comparisons = comp_service.compare_versions(
                    existing_policy.current_version_id, 
                    new_version.id
                )

                # 2. Detect conflicts
                conflicts_detected = conflict_engine.detect_conflicts(
                    existing_policy.current_version_id,
                    new_version.id,
                    comparisons
                )

                # 3. Store conflict records
                for item in conflicts_detected:
                    src_id = item.get("obligation_a_id")
                    tgt_id = item.get("obligation_b_id")

                    # Resolve similarity score
                    score = 0.0
                    if src_id and tgt_id:
                        for c in comparisons:
                            if c["obligation_a"].id == src_id and c["obligation_b"].id == tgt_id:
                                score = c["similarity_score"]
                                break

                    source_ob = self._db.get(Obligation, src_id) if src_id else None
                    target_ob = self._db.get(Obligation, tgt_id) if tgt_id else None

                    # Generate AI explanation
                    try:
                        ai_explanation = explanation_service.generate_explanation(
                            conflict_type=item["type"],
                            severity=item["severity"],
                            source_ob=source_ob,
                            target_ob=target_ob
                        )
                    except Exception as err:
                        logger.error("Failed to generate AI explanation: %s", err)
                        ai_explanation = item["description"]

                    conflict_record = Conflict(
                        source_policy_id=existing_policy.id,
                        target_policy_id=new_policy.id,
                        source_obligation_id=src_id,
                        target_obligation_id=tgt_id,
                        conflict_type=item["type"],
                        similarity_score=score,
                        severity=item["severity"],
                        ai_explanation=ai_explanation,
                        status="Open"
                    )
                    
                    # Generate and store relationship classification
                    try:
                        from backend.services.ai.relationship_classification_service import RelationshipClassificationService
                        rel_service = RelationshipClassificationService()
                        logger.info("Running AI relationship classification for obligations %s and %s", src_id, tgt_id)
                        rel_res = rel_service.classify_relationship(source_ob, target_ob)
                        conflict_record.relationship_type = rel_res.relationship_type
                        conflict_record.explanation = rel_res.explanation
                        conflict_record.confidence_score = rel_res.confidence_score
                        logger.info(
                            "Successfully classified relationship as %s with confidence %s for conflict comparison",
                            rel_res.relationship_type,
                            rel_res.confidence_score
                        )
                    except Exception as rel_err:
                        logger.error("Failed to run relationship classification: %s", rel_err)

                    self._db.add(conflict_record)
                    self._db.flush()

                    # Generate and store AI recommendation
                    try:
                        from backend.services.ai.ai_recommendation_service import AIRecommendationService
                        from backend.models.recommendation import Recommendation
                        
                        rec_ai_service = AIRecommendationService()
                        
                        # Resolve clause texts
                        source_clause_text = source_ob.clause.text if (source_ob and source_ob.clause) else None
                        target_clause_text = target_ob.clause.text if (target_ob and target_ob.clause) else None
                        
                        # Generate recommendation
                        rec_res = rec_ai_service.generate_recommendation(
                            conflict_type=item["type"],
                            severity=item["severity"],
                            source_ob=source_ob,
                            target_ob=target_ob
                        )
                        
                        # Generate redline
                        redline_res = rec_ai_service.generate_redline(
                            source_clause_text=source_clause_text,
                            target_clause_text=target_clause_text,
                            recommendation_summary=rec_res.recommended_resolution,
                            suggested_action=rec_res.suggested_action
                        )
                        
                        confidence = max(
                            source_ob.confidence_score if source_ob else 0.0,
                            target_ob.confidence_score if target_ob else 0.0,
                            0.90
                        )
                        
                        recommendation_record = Recommendation(
                            conflict_id=conflict_record.id,
                            recommendation_summary=rec_res.recommended_resolution,
                            suggested_action=rec_res.suggested_action,
                            original_clause=redline_res.original_clause,
                            revised_clause=redline_res.revised_clause,
                            reason=redline_res.reason_for_change,
                            ai_model=rec_ai_service._settings.GEMINI_MODEL,
                            confidence_score=confidence,
                            status="Pending"
                        )
                        self._db.add(recommendation_record)
                        logger.info("Successfully generated and linked AI recommendation for conflict %s", conflict_record.id)
                    except Exception as rec_err:
                        logger.error("Failed to generate AI recommendation for conflict %s: %s", conflict_record.id, rec_err)

                    all_conflicts.append(conflict_record)

                logger.info(
                    "Successfully compared and detected %s conflicts against policy %s.", 
                    len(conflicts_detected), 
                    existing_policy.id
                )

            except Exception as exc:
                logger.error(
                    "Failed to run comparison between version %s and existing policy %s: %s. Continuing...",
                    new_version.id,
                    existing_policy.id,
                    exc
                )

        # Commit all successfully generated conflict records
        if all_conflicts:
            try:
                self._db.commit()
                logger.info("Successfully committed %s conflict records to the database.", len(all_conflicts))
                
                # Write to the compliance audit log
                try:
                    from backend.services.compliance_dashboard_service import record_compliance_audit_log
                    user_email = new_version.uploaded_by.email if (new_version and new_version.uploaded_by) else "System"
                    record_compliance_audit_log(
                        self._db,
                        new_policy.company_id,
                        "Recommendation Generation",
                        user_email,
                        f"Successfully generated {len(all_conflicts)} AI resolution recommendations and redline drafts"
                    )
                except Exception as audit_err:
                    logger.error("Failed to write recommendation audit log: %s", audit_err)

            except Exception as exc:
                self._db.rollback()
                logger.error("Failed to commit conflict records to the database: %s", exc)
                raise
        else:
            logger.info("No conflicts detected across any comparison targets.")

        return all_conflicts
