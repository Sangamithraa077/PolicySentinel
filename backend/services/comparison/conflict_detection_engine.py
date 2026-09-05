"""Engine for analyzing comparative semantic mapping data to detect duplicate, contradictory, and missing obligations."""

from __future__ import annotations

import logging
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.clause import Clause
from backend.models.obligation import Obligation

logger = logging.getLogger(__name__)


class ConflictDetectionEngine:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _normalize_str(self, val: str | None) -> str:
        return (val or "").strip().lower()

    def detect_conflicts(
        self,
        version_a_id: uuid.UUID,
        version_b_id: uuid.UUID,
        comparison_results: list[dict],
    ) -> list[dict]:
        """Analyzes pairwise comparison results to flag duplicate, contradictory, and missing obligations."""
        conflicts = []

        # 1. Fetch original lists to identify missing obligations
        obs_a = self._db.scalars(
            select(Obligation)
            .join(Clause, Clause.id == Obligation.clause_id)
            .where(
                Clause.policy_version_id == version_a_id,
                Obligation.deleted_at.is_(None)
            )
        ).all()

        obs_b = self._db.scalars(
            select(Obligation)
            .join(Clause, Clause.id == Obligation.clause_id)
            .where(
                Clause.policy_version_id == version_b_id,
                Obligation.deleted_at.is_(None)
            )
        ).all()

        # Track the maximum similarity score for each obligation in both versions
        max_similarity_for_a: dict[uuid.UUID, float] = {ob.id: 0.0 for ob in obs_a}
        max_similarity_for_b: dict[uuid.UUID, float] = {ob.id: 0.0 for ob in obs_b}

        # Maps for quick lookup of comparison pairs
        for res in comparison_results:
            ob_a_id = res["obligation_a"].id
            ob_b_id = res["obligation_b"].id
            score = res["similarity_score"]
            
            max_similarity_for_a[ob_a_id] = max(max_similarity_for_a[ob_a_id], score)
            max_similarity_for_b[ob_b_id] = max(max_similarity_for_b[ob_b_id], score)

            # Analyze for duplicates and contradictions
            # Core target matches (high similarity or matching subject/action/object)
            is_semantically_similar = score >= 0.60
            
            # Check fields
            sub_match = self._normalize_str(res["obligation_a"].subject) == self._normalize_str(res["obligation_b"].subject)
            norm_act_a = self._normalize_str(res["obligation_a"].action)
            norm_act_b = self._normalize_str(res["obligation_b"].action)
            act_match = norm_act_a == norm_act_b or (norm_act_a and norm_act_a in norm_act_b) or (norm_act_b and norm_act_b in norm_act_a)
            norm_obj_a = self._normalize_str(res["obligation_a"].object)
            norm_obj_b = self._normalize_str(res["obligation_b"].object)
            obj_match = norm_obj_a == norm_obj_b or (norm_obj_a and norm_obj_a in norm_obj_b) or (norm_obj_b and norm_obj_b in norm_obj_a)
            target_match = sub_match and (act_match or obj_match)

            if is_semantically_similar or target_match:
                mod_a = res["obligation_a"].modality
                mod_b = res["obligation_b"].modality
                time_a = res["obligation_a"].time_constraint
                time_b = res["obligation_b"].time_constraint

                # A. Duplicate obligations
                if mod_a.lower() == mod_b.lower() and self._normalize_str(time_a) == self._normalize_str(time_b):
                    if score >= 0.90:
                        conflicts.append({
                            "type": "duplicate",
                            "severity": "low",
                            "description": (
                                f"Redundant obligation detected between Version A (Clause {res['obligation_a'].clause.clause_number}) "
                                f"and Version B (Clause {res['obligation_b'].clause.clause_number})."
                            ),
                            "obligation_a_id": ob_a_id,
                            "obligation_b_id": ob_b_id,
                            "details": {
                                "subject": res["obligation_a"].subject,
                                "action": res["obligation_a"].action,
                                "object": res["obligation_a"].object,
                                "modality_a": mod_a,
                                "modality_b": mod_b,
                                "time_constraint_a": time_a,
                                "time_constraint_b": time_b,
                            }
                        })
                # B. Contradictory obligations
                else:
                    # Determine severity based on severity of contradiction
                    severity = "medium"
                    desc = ""

                    # High Severity: Opposing strict mandates vs soft permissions
                    strict_mandates = {"must", "shall"}
                    soft_perms = {"should", "may"}
                    
                    is_mod_contradiction = mod_a.lower() != mod_b.lower()
                    is_time_contradiction = self._normalize_str(time_a) != self._normalize_str(time_b)

                    if is_mod_contradiction:
                        if (mod_a.lower() in strict_mandates and mod_b.lower() in soft_perms) or \
                           (mod_b.lower() in strict_mandates and mod_a.lower() in soft_perms):
                            severity = "high"
                            desc = f"Modality conflict (strict mandate vs recommendation) between Clause {res['obligation_a'].clause.clause_number} ({mod_a}) and Clause {res['obligation_b'].clause.clause_number} ({mod_b})."
                        else:
                            desc = f"Modality variance between Clause {res['obligation_a'].clause.clause_number} ({mod_a}) and Clause {res['obligation_b'].clause.clause_number} ({mod_b})."
                    
                    elif is_time_contradiction:
                        desc = f"Time constraint conflict between Clause {res['obligation_a'].clause.clause_number} ({time_a or 'none'}) and Clause {res['obligation_b'].clause.clause_number} ({time_b or 'none'})."

                    conflicts.append({
                        "type": "contradiction",
                        "severity": severity,
                        "description": desc or "Varying parameters for semantically similar obligations.",
                        "obligation_a_id": ob_a_id,
                        "obligation_b_id": ob_b_id,
                        "details": {
                            "subject": res["obligation_a"].subject,
                            "action": res["obligation_a"].action,
                            "object": res["obligation_a"].object,
                            "modality_a": mod_a,
                            "modality_b": mod_b,
                            "time_constraint_a": time_a,
                            "time_constraint_b": time_b,
                        }
                    })

        # C. Missing obligations (Gap Detection)
        # Obligations in Version A not present in B
        for ob in obs_a:
            if max_similarity_for_a[ob.id] < 0.70:
                conflicts.append({
                    "type": "missing",
                    "severity": "medium",
                    "description": f"Obligation from Version A (Clause {ob.clause.clause_number}) is missing in Version B.",
                    "obligation_a_id": ob.id,
                    "obligation_b_id": None,
                    "details": {
                        "subject": ob.subject,
                        "action": ob.action,
                        "object": ob.object,
                        "modality_a": ob.modality,
                        "modality_b": None,
                        "time_constraint_a": ob.time_constraint,
                        "time_constraint_b": None,
                    }
                })

        # Obligations in Version B not present in A
        for ob in obs_b:
            if max_similarity_for_b[ob.id] < 0.70:
                conflicts.append({
                    "type": "missing",
                    "severity": "medium",
                    "description": f"New obligation introduced in Version B (Clause {ob.clause.clause_number}) has no matching origin in Version A.",
                    "obligation_a_id": None,
                    "obligation_b_id": ob.id,
                    "details": {
                        "subject": ob.subject,
                        "action": ob.action,
                        "object": ob.object,
                        "modality_a": None,
                        "modality_b": ob.modality,
                        "time_constraint_a": None,
                        "time_constraint_b": ob.time_constraint,
                    }
                })

        return conflicts
