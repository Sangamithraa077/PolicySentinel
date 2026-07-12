"""Service for evaluating policy version metadata (effective dates, version history) for staleness using Gemini."""

from __future__ import annotations

import logging
import json
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict
from google import genai
from google.genai import types

from backend.config.settings import Settings, get_settings
from backend.models.policy_version import PolicyVersion
from backend.services.ai.prompts import (
    STALENESS_DETECTION_SYSTEM_INSTRUCTION,
    STALENESS_DETECTION_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class StalenessDetectionResult(BaseModel):
    status: str = Field(..., description="Staleness classification status: exactly one of: 'Current', 'Review Required', 'Outdated'")
    explanation: str = Field(..., description="A detailed explanation explaining the staleness classification status reason")

    model_config = ConfigDict(from_attributes=True)


class StalenessDetectionService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None

        if self._settings.GEMINI_API_KEY and self._settings.GEMINI_API_KEY != "changeme":
            try:
                self._client = genai.Client(api_key=self._settings.GEMINI_API_KEY)
            except Exception as exc:
                logger.error("Failed to initialize Google GenAI client in StalenessDetectionService: %s", exc)

    def detect_staleness(
        self,
        version: PolicyVersion | None
    ) -> StalenessDetectionResult:
        """Determines the staleness status of a policy version based on dates and superseded links using Gemini."""
        if self._client is None:
            return self._get_mock_staleness(version)

        user_prompt = STALENESS_DETECTION_USER_PROMPT.format(
            version_number=version.version_number if version else "N/A",
            effective_date=version.effective_date.isoformat() if (version and version.effective_date) else "N/A",
            created_date=version.created_at.isoformat() if version else "N/A",
            superseded_by_id=str(version.superseded_by_version_id) if (version and version.superseded_by_version_id) else "N/A",
            status=version.status.value if version else "N/A",
        )

        try:
            response = self._client.models.generate_content(
                model=self._settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=STALENESS_DETECTION_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=StalenessDetectionResult,
                    temperature=0.1,
                )
            )
            data = json.loads(response.text)
            
            # Normalize status categories
            status_val = data.get("status", "Current").strip().title()
            valid_statuses = {"Current", "Review Required", "Outdated"}
            if status_val not in valid_statuses:
                status_val = "Review Required"
            data["status"] = status_val
            
            return StalenessDetectionResult(**data)
        except Exception as exc:
            logger.error("Failed to detect staleness with AI: %s. Falling back to mock.", exc)
            return self._get_mock_staleness(version)

    def _get_mock_staleness(
        self,
        version: PolicyVersion | None
    ) -> StalenessDetectionResult:
        """Rule-based deterministic fallback evaluation of policy version staleness status."""
        if not version:
            return StalenessDetectionResult(
                status="Outdated",
                explanation="No policy version metadata provided to evaluate."
            )

        # 1. Superseded status
        if version.superseded_by_version_id is not None:
            return StalenessDetectionResult(
                status="Outdated",
                explanation=f"This policy revision has been superseded by a newer version (ID: {version.superseded_by_version_id})."
            )

        # 2. Check effective dates/age relative to today
        today = date.today()
        eff_date = version.effective_date
        
        # Fallback to upload time if no effective date is present
        ref_date = eff_date if eff_date else version.created_at.date()
        days_diff = (today - ref_date).days
        years_diff = days_diff / 365.25

        if not eff_date:
            return StalenessDetectionResult(
                status="Review Required",
                explanation="The policy version lacks an explicit effective date, requiring immediate administrative review."
            )

        if years_diff >= 2.0:
            return StalenessDetectionResult(
                status="Outdated",
                explanation=f"The policy is outdated: it was effective on {eff_date} which is over 2 years ago and has not been updated."
            )
        elif years_diff >= 1.0:
            return StalenessDetectionResult(
                status="Review Required",
                explanation=f"The policy is due for review: its effective date ({eff_date}) is older than 1 year (annual review cycle limit)."
            )

        return StalenessDetectionResult(
            status="Current",
            explanation=f"The policy revision is current: it has a valid effective date ({eff_date}) within the last 12 months."
        )
