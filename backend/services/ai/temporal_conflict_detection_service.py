"""Service for analyzing time-based/temporal conflicts between policy obligations using Gemini."""

from __future__ import annotations

import logging
import json
import re
from pydantic import BaseModel, Field, ConfigDict
from google import genai
from google.genai import types

from backend.config.settings import Settings, get_settings
from backend.models.obligation import Obligation
from backend.services.ai.prompts import (
    TEMPORAL_CONFLICT_SYSTEM_INSTRUCTION,
    TEMPORAL_CONFLICT_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class TemporalConflictResult(BaseModel):
    is_conflict: bool = Field(..., description="Whether a temporal conflict is detected between the two obligations")
    conflict_type: str = Field(..., description="Type of temporal conflict, e.g. 'deadline_mismatch', 'frequency_mismatch', 'validity_period_mismatch', 'review_cycle_mismatch', or 'none'")
    detected_values: str = Field(..., description="Summary of compared values (e.g. '90 days vs 180 days')")
    ai_explanation: str = Field(..., description="Detailed description explaining why this represents a temporal mismatch or contradiction")
    confidence_score: float = Field(..., description="A confidence score between 0.0 and 1.0 representing classification assurance")

    model_config = ConfigDict(from_attributes=True)


class TemporalConflictDetectionService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None

        if self._settings.GEMINI_API_KEY and self._settings.GEMINI_API_KEY != "changeme":
            try:
                self._client = genai.Client(api_key=self._settings.GEMINI_API_KEY)
            except Exception as exc:
                logger.error("Failed to initialize Google GenAI client in TemporalConflictDetectionService: %s", exc)

    def detect_temporal_conflict(
        self,
        ob_a: Obligation | None,
        ob_b: Obligation | None
    ) -> TemporalConflictResult:
        """Compares two obligations for deadlines, frequencies, validity periods, and review cycles using Gemini."""
        if self._client is None:
            return self._get_mock_temporal_conflict(ob_a, ob_b)

        user_prompt = TEMPORAL_CONFLICT_USER_PROMPT.format(
            action_a=ob_a.action if ob_a else "N/A",
            time_a=ob_a.time_constraint if ob_a else "N/A",
            action_b=ob_b.action if ob_b else "N/A",
            time_b=ob_b.time_constraint if ob_b else "N/A",
        )

        try:
            response = self._client.models.generate_content(
                model=self._settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=TEMPORAL_CONFLICT_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=TemporalConflictResult,
                    temperature=0.1,
                )
            )
            data = json.loads(response.text)
            return TemporalConflictResult(**data)
        except Exception as exc:
            logger.error("Failed to detect temporal conflict with AI: %s. Falling back to mock.", exc)
            return self._get_mock_temporal_conflict(ob_a, ob_b)

    def _get_mock_temporal_conflict(
        self,
        ob_a: Obligation | None,
        ob_b: Obligation | None
    ) -> TemporalConflictResult:
        """Deterministic mock matching for time-based/temporal conflicts."""
        if not ob_a or not ob_b:
            return TemporalConflictResult(
                is_conflict=False,
                conflict_type="none",
                detected_values="N/A",
                ai_explanation="Cannot perform temporal comparison on missing obligations.",
                confidence_score=1.0
            )

        t1 = (ob_a.time_constraint or "").strip().lower()
        t2 = (ob_b.time_constraint or "").strip().lower()

        if not t1 or not t2:
            return TemporalConflictResult(
                is_conflict=False,
                conflict_type="none",
                detected_values=f"A: '{t1 or 'none'}', B: '{t2 or 'none'}'",
                ai_explanation="One or both obligations are missing time constraints.",
                confidence_score=0.90
            )

        # 1. Parse numbers mismatch
        nums_a = re.findall(r'\d+', t1)
        nums_b = re.findall(r'\d+', t2)
        if nums_a and nums_b and nums_a[0] != nums_b[0]:
            return TemporalConflictResult(
                is_conflict=True,
                conflict_type="deadline_mismatch",
                detected_values=f"{t1} vs {t2}",
                ai_explanation=f"Time constraint numerical mismatch detected: '{t1}' conflicts with '{t2}'.",
                confidence_score=0.95
            )

        # 2. Parse frequency mismatch
        freqs = ["monthly", "quarterly", "weekly", "bi-weekly", "annual", "annually", "semi-annual", "daily"]
        found_a = [f for f in freqs if f in t1]
        found_b = [f for f in freqs if f in t2]
        if found_a and found_b and found_a[0] != found_b[0]:
            # Ignore synonyms
            syns = {"annual": "annually", "annually": "annual"}
            if syns.get(found_a[0]) != found_b[0]:
                return TemporalConflictResult(
                    is_conflict=True,
                    conflict_type="frequency_mismatch",
                    detected_values=f"{found_a[0].capitalize()} vs {found_b[0].capitalize()}",
                    ai_explanation=f"Obligation check frequency mismatch: Obligation A requires '{t1}' while Obligation B requires '{t2}'.",
                    confidence_score=0.90
                )

        return TemporalConflictResult(
            is_conflict=False,
            conflict_type="none",
            detected_values=f"A: '{t1}', B: '{t2}'",
            ai_explanation="No direct time-based conflict detected under current constraints.",
            confidence_score=0.85
        )
