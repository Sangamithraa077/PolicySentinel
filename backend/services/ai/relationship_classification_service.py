"""Service for classifying the compliance relationship between two policy obligations using Gemini."""

from __future__ import annotations

import logging
import json
from pydantic import BaseModel, Field, ConfigDict
from google import genai
from google.genai import types

from backend.config.settings import Settings, get_settings
from backend.models.obligation import Obligation
from backend.services.ai.prompts import (
    RELATIONSHIP_CLASSIFICATION_SYSTEM_INSTRUCTION,
    RELATIONSHIP_CLASSIFICATION_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class RelationshipClassificationResult(BaseModel):
    relationship_type: str = Field(..., description="The relationship category. Must be one of: CONFLICT, REDUNDANT, COMPLEMENTARY, UNRELATED")
    confidence_score: float = Field(..., description="A confidence score between 0.0 and 1.0 representing classification assurance")
    explanation: str = Field(..., description="A short explanation of why the obligations stand in this relationship")

    model_config = ConfigDict(from_attributes=True)


class RelationshipClassificationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None

        if self._settings.GEMINI_API_KEY and self._settings.GEMINI_API_KEY != "changeme":
            try:
                self._client = genai.Client(api_key=self._settings.GEMINI_API_KEY)
            except Exception as exc:
                logger.error("Failed to initialize Google GenAI client in RelationshipClassificationService: %s", exc)

    def classify_relationship(
        self,
        existing_ob: Obligation | None,
        new_ob: Obligation | None
    ) -> RelationshipClassificationResult:
        """Classifies the relationship of two policy obligations using Gemini with fallback options."""
        if self._client is None:
            return self._get_mock_classification(existing_ob, new_ob)

        user_prompt = RELATIONSHIP_CLASSIFICATION_USER_PROMPT.format(
            existing_subject=existing_ob.subject if existing_ob else "N/A",
            existing_action=existing_ob.action if existing_ob else "N/A",
            existing_object=existing_ob.object if existing_ob else "N/A",
            existing_modality=existing_ob.modality if existing_ob else "N/A",
            existing_time=existing_ob.time_constraint if existing_ob else "N/A",
            existing_category=existing_ob.compliance_category if existing_ob else "N/A",
            new_subject=new_ob.subject if new_ob else "N/A",
            new_action=new_ob.action if new_ob else "N/A",
            new_object=new_ob.object if new_ob else "N/A",
            new_modality=new_ob.modality if new_ob else "N/A",
            new_time=new_ob.time_constraint if new_ob else "N/A",
            new_category=new_ob.compliance_category if new_ob else "N/A",
        )

        try:
            response = self._client.models.generate_content(
                model=self._settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=RELATIONSHIP_CLASSIFICATION_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=RelationshipClassificationResult,
                    temperature=0.1,
                )
            )
            data = json.loads(response.text)
            
            # Normalize type to match uppercase expected values
            rel_type = data.get("relationship_type", "UNRELATED").strip().upper()
            valid_types = {"CONFLICT", "REDUNDANT", "COMPLEMENTARY", "UNRELATED"}
            if rel_type not in valid_types:
                rel_type = "UNRELATED"
            data["relationship_type"] = rel_type
            
            return RelationshipClassificationResult(**data)
        except Exception as exc:
            logger.error("Failed to generate relationship classification: %s. Falling back to mock.", exc)
            return self._get_mock_classification(existing_ob, new_ob)

    def _get_mock_classification(self, existing_ob: Obligation | None, new_ob: Obligation | None) -> RelationshipClassificationResult:
        """Deterministic mock rule-based classification fallback when Gemini is unavailable."""
        if not existing_ob or not new_ob:
            return RelationshipClassificationResult(
                relationship_type="UNRELATED",
                confidence_score=1.0,
                explanation="One or both obligations are missing."
            )
        
        ex_sub = existing_ob.subject.strip().lower()
        new_sub = new_ob.subject.strip().lower()
        
        ex_act = existing_ob.action.strip().lower()
        new_act = new_ob.action.strip().lower()
        
        has_subject_overlap = ex_sub in new_sub or new_sub in ex_sub
        has_action_overlap = ex_act[:12] in new_act or new_act[:12] in ex_act
        
        # Word intersection for fallback matching
        w1 = set(ex_act.split())
        w2 = set(new_act.split())
        stop_words = {"to", "the", "a", "an", "and", "of", "in", "on", "for", "with", "by", "at", "from"}
        meaningful_overlap = len((w1 & w2) - stop_words) >= 2

        m1 = (existing_ob.modality or "").strip().lower()
        m2 = (new_ob.modality or "").strip().lower()
        
        # Check negative modality contradictions
        is_contradicting_modality = (
            ("must" in m1 or "shall" in m1 or "should" in m1) and ("not" in m2 or "never" in m2)
        ) or (
            ("must" in m2 or "shall" in m2 or "should" in m2) and ("not" in m1 or "never" in m1)
        )

        if has_subject_overlap:
            if has_action_overlap or meaningful_overlap:
                if is_contradicting_modality:
                    return RelationshipClassificationResult(
                        relationship_type="CONFLICT",
                        confidence_score=0.95,
                        explanation=f"Contradicting modalities detected for similar actions. Existing: '{existing_ob.modality}', New: '{new_ob.modality}'."
                    )
                
                # Check redundancy
                if ex_act == new_act:
                    return RelationshipClassificationResult(
                        relationship_type="REDUNDANT",
                        confidence_score=0.98,
                        explanation="The obligations enforce the exact same action on the same subject."
                    )
                
                # Otherwise Complementary
                return RelationshipClassificationResult(
                    relationship_type="COMPLEMENTARY",
                    confidence_score=0.88,
                    explanation="The obligations enforce related compliance aspects under the same subject."
                )
        
        return RelationshipClassificationResult(
            relationship_type="UNRELATED",
            confidence_score=0.90,
            explanation="No significant subject or action overlaps detected between these obligations."
        )
