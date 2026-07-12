"""Service for generating compliance resolution recommendations and policy redlines using Gemini."""

from __future__ import annotations

import logging
import json
from pydantic import BaseModel, Field, ConfigDict
from google import genai
from google.genai import types

from backend.config.settings import Settings, get_settings
from backend.models.obligation import Obligation

logger = logging.getLogger(__name__)


class RecommendationAIResult(BaseModel):
    conflict_summary: str = Field(..., description="Summary of the compliance conflict")
    recommended_resolution: str = Field(..., description="Actionable recommendation to resolve the conflict")
    suggested_action: str = Field(..., description="Concise suggested action summary")

    model_config = ConfigDict(from_attributes=True)


class RedlineAIResult(BaseModel):
    original_clause: str = Field(..., description="Original conflicting clause text")
    revised_clause: str = Field(..., description="Revised clause text resolving the conflict")
    reason_for_change: str = Field(..., description="Reason for the changes made")

    model_config = ConfigDict(from_attributes=True)


RECOMMENDATION_SYSTEM_INSTRUCTION = """
You are a principal compliance auditor. Your job is to analyze a detected compliance conflict between two policy obligations and generate a structured resolution recommendation.

You must return:
1. conflict_summary: A concise, clear summary of the compliance conflict.
2. recommended_resolution: A clear, actionable suggestion to resolve the conflict (e.g. recommend aligning the modalities or adding/excluding requirements).
3. suggested_action: A short summary of the suggested action, e.g. "Align modalities", "Document gap", "Add NDA obligation".

Return the result as a structured JSON object matching the requested schema.
"""

RECOMMENDATION_USER_PROMPT = """
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

REDLINE_SYSTEM_INSTRUCTION = """
You are a legal counsel and policy draftsman. Your job is to compare an existing clause text with a conflicting clause text, consider the recommendation, and generate a suggested revised clause.

You must:
1. Preserve legal wording as much as possible.
2. Highlight only the modified portions.
3. Keep the output professional and structured.

Return:
1. original_clause: The exact original conflicting clause text from the target/new version.
2. revised_clause: The suggested revised clause text that resolves the contradiction/gap.
3. reason_for_change: Concise explanation of why the change is recommended.

Return the result as a structured JSON object matching the requested schema.
"""

REDLINE_USER_PROMPT = """
Context:
Existing Clause (Source):
{source_clause_text}

Conflicting Clause (Target):
{target_clause_text}

Recommendation:
{recommendation_summary}
Suggested Action: {suggested_action}
"""


class AIRecommendationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None

        if self._settings.GEMINI_API_KEY and self._settings.GEMINI_API_KEY != "changeme":
            try:
                self._client = genai.Client(api_key=self._settings.GEMINI_API_KEY)
            except Exception as exc:
                logger.error("Failed to initialize Google GenAI client in AIRecommendationService: %s", exc)

    def generate_recommendation(
        self,
        conflict_type: str,
        severity: str,
        source_ob: Obligation | None,
        target_ob: Obligation | None
    ) -> RecommendationAIResult:
        """Generates a structured compliance recommendation based on obligations and conflict metadata."""
        if self._client is None:
            return self._get_mock_recommendation(conflict_type, severity, source_ob, target_ob)

        user_prompt = RECOMMENDATION_USER_PROMPT.format(
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
                    system_instruction=RECOMMENDATION_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=RecommendationAIResult,
                    temperature=0.2,
                )
            )
            data = json.loads(response.text)
            return RecommendationAIResult(**data)
        except Exception as exc:
            logger.error("Failed to generate AI recommendation: %s. Falling back to mock.", exc)
            return self._get_mock_recommendation(conflict_type, severity, source_ob, target_ob)

    def generate_redline(
        self,
        source_clause_text: str | None,
        target_clause_text: str | None,
        recommendation_summary: str,
        suggested_action: str
    ) -> RedlineAIResult:
        """Generates policy clause redlines highlighting only modified elements while preserving legal phrasing."""
        if self._client is None:
            return self._get_mock_redline(source_clause_text, target_clause_text, recommendation_summary, suggested_action)

        user_prompt = REDLINE_USER_PROMPT.format(
            source_clause_text=source_clause_text or "N/A",
            target_clause_text=target_clause_text or "N/A",
            recommendation_summary=recommendation_summary,
            suggested_action=suggested_action,
        )

        try:
            response = self._client.models.generate_content(
                model=self._settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=REDLINE_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=RedlineAIResult,
                    temperature=0.2,
                )
            )
            data = json.loads(response.text)
            return RedlineAIResult(**data)
        except Exception as exc:
            logger.error("Failed to generate AI redline: %s. Falling back to mock.", exc)
            return self._get_mock_redline(source_clause_text, target_clause_text, recommendation_summary, suggested_action)

    def _get_mock_recommendation(
        self,
        conflict_type: str,
        severity: str,
        source_ob: Obligation | None,
        target_ob: Obligation | None
    ) -> RecommendationAIResult:
        if conflict_type == "duplicate":
            return RecommendationAIResult(
                conflict_summary="Redundant obligation detected between policies.",
                recommended_resolution="Consolidate duplicate obligations to simplify policies.",
                suggested_action="Consolidate duplicates"
            )
        elif conflict_type == "contradiction":
            return RecommendationAIResult(
                conflict_summary=f"Modality mismatch: Modality '{source_ob.modality if source_ob else 'N/A'}' contradicts '{target_ob.modality if target_ob else 'N/A'}'.",
                recommended_resolution="Align target obligation modality to match the source policy strict mandate.",
                suggested_action="Align modalities"
            )
        else: # missing
            action_name = f"Add missing obligation" if source_ob else "Validate new obligation"
            desc = f"Obligation is present in source policy but missing in target." if source_ob else "New obligation has no historical origin."
            return RecommendationAIResult(
                conflict_summary=desc,
                recommended_resolution="Integrate missing obligation into policy version to prevent compliance gap.",
                suggested_action=action_name
            )

    def _get_mock_redline(
        self,
        source_clause_text: str | None,
        target_clause_text: str | None,
        recommendation_summary: str,
        suggested_action: str
    ) -> RedlineAIResult:
        orig = target_clause_text or "No original clause."
        if "Align modalities" in suggested_action or "contradicts" in recommendation_summary:
            # Simple redline modification replacement
            revised = orig.replace("should", "must").replace("may", "must").replace("Should", "Must").replace("May", "Must")
            if revised == orig:
                revised = orig + " (Revised: Modality aligned to MUST)"
            return RedlineAIResult(
                original_clause=orig,
                revised_clause=revised,
                reason_for_change="Aligned modality to match strict requirements."
            )
        elif "Consolidate" in suggested_action:
            return RedlineAIResult(
                original_clause=orig,
                revised_clause="[Consolidated into source policy. This duplicate clause is removed.]",
                reason_for_change="Removed redundant duplicate obligation."
            )
        else:
            # missing or default
            revised = orig + " [Note: Add strict compliance control mapping to align with source policy requirements.]"
            return RedlineAIResult(
                original_clause=orig,
                revised_clause=revised,
                reason_for_change="Added missing compliance checks to target clause."
            )
