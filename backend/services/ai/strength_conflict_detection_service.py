"""Service for comparing obligation modality strengths (Must vs Should vs May) using Gemini."""

from __future__ import annotations

import logging
import json
from pydantic import BaseModel, Field, ConfigDict
from google import genai
from google.genai import types

from backend.config.settings import Settings, get_settings
from backend.models.obligation import Obligation
from backend.services.ai.prompts import (
    STRENGTH_CONFLICT_SYSTEM_INSTRUCTION,
    STRENGTH_CONFLICT_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class StrengthConflictResult(BaseModel):
    is_conflict: bool = Field(..., description="Whether a strength/modality mismatch conflict is detected")
    strength_conflict: str = Field(..., description="The strength mismatch category: 'WEAKENED', 'STRENGTHENED', 'MODALITY_MISMATCH', or 'NONE'")
    explanation: str = Field(..., description="A description of how the modalities weaken, strengthen, or contradict each other")
    confidence_score: float = Field(..., description="A confidence score between 0.0 and 1.0 representing classification assurance")

    model_config = ConfigDict(from_attributes=True)


class StrengthConflictDetectionService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None

        if self._settings.GEMINI_API_KEY and self._settings.GEMINI_API_KEY != "changeme":
            try:
                self._client = genai.Client(api_key=self._settings.GEMINI_API_KEY)
            except Exception as exc:
                logger.error("Failed to initialize Google GenAI client in StrengthConflictDetectionService: %s", exc)

    def detect_strength_conflict(
        self,
        ob_a: Obligation | None,
        ob_b: Obligation | None
    ) -> StrengthConflictResult:
        """Analyzes modality differences between two obligations using Gemini with fallback options."""
        if self._client is None:
            return self._get_mock_strength_conflict(ob_a, ob_b)

        user_prompt = STRENGTH_CONFLICT_USER_PROMPT.format(
            modality_a=ob_a.modality if ob_a else "N/A",
            action_a=ob_a.action if ob_a else "N/A",
            modality_b=ob_b.modality if ob_b else "N/A",
            action_b=ob_b.action if ob_b else "N/A",
        )

        try:
            response = self._client.models.generate_content(
                model=self._settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=STRENGTH_CONFLICT_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=StrengthConflictResult,
                    temperature=0.1,
                )
            )
            data = json.loads(response.text)
            
            # Normalize enum types
            str_cat = data.get("strength_conflict", "NONE").strip().upper()
            valid_cats = {"WEAKENED", "STRENGTHENED", "MODALITY_MISMATCH", "NONE"}
            if str_cat not in valid_cats:
                str_cat = "NONE"
            data["strength_conflict"] = str_cat
            
            return StrengthConflictResult(**data)
        except Exception as exc:
            logger.error("Failed to detect strength conflict with AI: %s. Falling back to mock.", exc)
            return self._get_mock_strength_conflict(ob_a, ob_b)

    def _get_mock_strength_conflict(
        self,
        ob_a: Obligation | None,
        ob_b: Obligation | None
    ) -> StrengthConflictResult:
        """Deterministic weight-based fallback matching for obligation modality strength comparison."""
        if not ob_a or not ob_b:
            return StrengthConflictResult(
                is_conflict=False,
                strength_conflict="NONE",
                explanation="Modality comparison is skipped for missing obligations.",
                confidence_score=1.0
            )

        m1 = (ob_a.modality or "").strip().lower()
        m2 = (ob_b.modality or "").strip().lower()

        if not m1 or not m2:
            return StrengthConflictResult(
                is_conflict=True,
                strength_conflict="MODALITY_MISMATCH",
                explanation=f"One or both obligations lack a clear modality string. A: '{m1 or 'none'}', B: '{m2 or 'none'}'.",
                confidence_score=0.88
            )

        def get_weight(m: str) -> int:
            if "must" in m or "shall" in m:
                return 3
            if "should" in m:
                return 2
            if "may" in m:
                return 1
            return 0

        w1 = get_weight(m1)
        w2 = get_weight(m2)

        if w1 == 0 or w2 == 0:
            return StrengthConflictResult(
                is_conflict=True,
                strength_conflict="MODALITY_MISMATCH",
                explanation=f"Custom modality detected. Obligation A: '{ob_a.modality}', Obligation B: '{ob_b.modality}'.",
                confidence_score=0.85
            )

        if w1 > w2:
            # Weaker
            return StrengthConflictResult(
                is_conflict=True,
                strength_conflict="WEAKENED",
                explanation=f"Obligation modality weakened from mandatory/strongly recommended ('{ob_a.modality}') to a weaker instruction ('{ob_b.modality}').",
                confidence_score=0.95
            )
        elif w1 < w2:
            # Stronger
            return StrengthConflictResult(
                is_conflict=True,
                strength_conflict="STRENGTHENED",
                explanation=f"Obligation modality strengthened from permissive/guideline ('{ob_a.modality}') to a mandatory instruction ('{ob_b.modality}').",
                confidence_score=0.95
            )

        return StrengthConflictResult(
            is_conflict=False,
            strength_conflict="NONE",
            explanation=f"Obligations possess equivalent modality strengths: '{ob_a.modality}' vs '{ob_b.modality}'.",
            confidence_score=0.90
        )
