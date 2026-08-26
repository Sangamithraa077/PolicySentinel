"""Service for generating concise compliance explanations for detected conflicts using Gemini."""

from __future__ import annotations

import logging
from google import genai
from google.genai import types

from backend.config.settings import Settings, get_settings
from backend.models.obligation import Obligation

logger = logging.getLogger(__name__)

CONFLICT_EXPLANATION_SYSTEM_INSTRUCTION = """
You are a senior compliance and legal analyst. Your job is to analyze a detected compliance conflict between two policy obligations and generate a concise, professional explanation.

Your explanation must cover:
1. Why the two obligations conflict.
2. The specific differing fields (e.g. differing modality: "Must" vs "Should", differing time constraints, or missing compliance gaps).
3. A recommendation on which obligation requires review (e.g. recommend reviewing the new obligation to ensure alignment with existing standards).

Be extremely concise and professional. Do not use formatting like markdown bolding inside the response string. Limit the output to 3 short sentences.
"""

CONFLICT_EXPLANATION_USER_PROMPT = """
Analyze the following conflict:

Conflict Type: {conflict_type}
Severity: {severity}

Source Obligation:
- Subject: {source_subject}
- Action: {source_action}
- Object: {source_object}
- Modality: {source_modality}
- Time Constraint: {source_time}

Target Obligation:
- Subject: {target_subject}
- Action: {target_action}
- Object: {target_object}
- Modality: {target_modality}
- Time Constraint: {target_time}
"""


from backend.services.ai.gemini_client import create_gemini_client

class ConflictExplanationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = create_gemini_client(self._settings)

    def generate_explanation(
        self,
        conflict_type: str,
        severity: str,
        source_ob: Obligation | None,
        target_ob: Obligation | None
    ) -> str:
        """Generates an AI explanation of a compliance conflict, highlighting differings and suggestions."""
        if self._client is None:
            logger.info("No Gemini API key configured. Falling back to rule-based explanation generator.")
            return self.get_mock_explanation(conflict_type, severity, source_ob, target_ob)

        user_prompt = CONFLICT_EXPLANATION_USER_PROMPT.format(
            conflict_type=conflict_type,
            severity=severity,
            source_subject=source_ob.subject if source_ob else "N/A",
            source_action=source_ob.action if source_ob else "N/A",
            source_object=source_ob.object if source_ob else "N/A",
            source_modality=source_ob.modality if source_ob else "N/A",
            source_time=source_ob.time_constraint if source_ob else "N/A",
            target_subject=target_ob.subject if target_ob else "N/A",
            target_action=target_ob.action if target_ob else "N/A",
            target_object=target_ob.object if target_ob else "N/A",
            target_modality=target_ob.modality if target_ob else "N/A",
            target_time=target_ob.time_constraint if target_ob else "N/A",
        )

        try:
            response = self._client.models.generate_content(
                model=self._settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=CONFLICT_EXPLANATION_SYSTEM_INSTRUCTION,
                    temperature=0.2,
                )
            )
            return response.text.strip()
        except Exception as exc:
            logger.error("Failed to call Gemini for conflict explanation: %s. Falling back to mock.", exc)
            return self.get_mock_explanation(conflict_type, severity, source_ob, target_ob)

    def get_mock_explanation(
        self,
        conflict_type: str,
        severity: str,
        source_ob: Obligation | None,
        target_ob: Obligation | None
    ) -> str:
        """Generates a high-quality, professional mock explanation for compliance conflicts."""
        if conflict_type == "duplicate":
            sub = source_ob.subject if source_ob else "Employees"
            act = source_ob.action if source_ob else "comply with rules"
            return (
                f"Both policies specify the exact same requirement for {sub} to {act}. "
                "This redundancy can lead to duplicate auditing efforts. "
                "We recommend reviewing the target policy to consolidate or reference the existing source policy."
            )
        elif conflict_type == "contradiction":
            sub_a = source_ob.subject if source_ob else "N/A"
            sub_b = target_ob.subject if target_ob else "N/A"
            mod_a = source_ob.modality if source_ob else "N/A"
            mod_b = target_ob.modality if target_ob else "N/A"
            
            diffs = []
            if mod_a != mod_b:
                diffs.append(f"modality ({mod_a} vs {mod_b})")
            if source_ob and target_ob and source_ob.time_constraint != target_ob.time_constraint:
                diffs.append(f"time constraint ({source_ob.time_constraint} vs {target_ob.time_constraint})")

            diff_str = " and ".join(diffs) or "varying parameters"
            
            return (
                f"A parameter mismatch exists between the obligations due to differing {diff_str}. "
                f"The source obligation specifies a '{mod_a}' mandate while the target specifies a '{mod_b}' permission. "
                "We recommend reviewing the target obligation to clarify the authority level required."
            )
        else: # missing
            if source_ob:
                sub = source_ob.subject
                act = source_ob.action
                obj = source_ob.object
                return (
                    f"The compliance obligation for {sub} to {act} {obj} in the source policy is missing in the target policy. "
                    "This omission creates a compliance gap that may weaken organizational alignment. "
                    "We recommend reviewing the target policy to verify if this omission was intentional."
                )
            else:
                sub = target_ob.subject if target_ob else "Employees"
                act = target_ob.action if target_ob else "perform action"
                obj = target_ob.object if target_ob else "object"
                return (
                    f"A new compliance requirement for {sub} to {act} {obj} has been introduced in the target policy. "
                    "This requirement has no corresponding origin in the source policy version. "
                    "We recommend reviewing the target obligation to ensure it conforms to existing corporate guidelines."
                )
