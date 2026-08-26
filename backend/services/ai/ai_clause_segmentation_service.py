"""AI-assisted clause segmentation service using Gemini structured JSON response, with heuristic fallback."""

from __future__ import annotations

import json
import logging
import uuid
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from backend.config.settings import Settings, get_settings
from backend.domain.entities.clause import ClauseMarkerType, PolicyClause
from backend.services.ai.prompts import (
    CLAUSE_SEGMENTATION_SYSTEM_INSTRUCTION,
    CLAUSE_SEGMENTATION_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class ExtractedClauseItem(BaseModel):
    clause_number: str | None = Field(None, description="Section number or designator")
    heading: str | None = Field(None, description="Clause title or section heading")
    level: int = Field(1, description="Nesting level (1=main, 2=sub, 3=item)")
    text: str = Field(..., description="Full text content of the clause")


class ExtractedClauseList(BaseModel):
    clauses: list[ExtractedClauseItem] = Field(..., description="List of segmented document clauses")


class AIClauseSegmentationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None

        if self._settings.GEMINI_API_KEY and self._settings.GEMINI_API_KEY != "changeme":
            try:
                self._client = genai.Client(api_key=self._settings.GEMINI_API_KEY)
            except Exception as exc:
                logger.error("Failed to initialize Google GenAI client for clause segmentation: %s", exc)

    def segment_with_ai(self, document_text: str) -> list[PolicyClause]:
        """Segments document text into structured PolicyClause entities using AI or heuristic fallback."""
        if not document_text.strip():
            return []

        if self._client is None:
            logger.info("No Gemini API key configured. Using paragraph-heuristic fallback for AI segmentation.")
            return self._heuristic_segmentation_fallback(document_text)

        user_prompt = CLAUSE_SEGMENTATION_USER_PROMPT.format(document_text=document_text[:12000])

        try:
            from backend.utils.retry_helper import retry_on_transient_error

            @retry_on_transient_error(max_retries=2, initial_delay=1.0)
            def _call_gemini_retried():
                return self._client.models.generate_content(
                    model=self._settings.GEMINI_MODEL,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=CLAUSE_SEGMENTATION_SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        response_schema=ExtractedClauseList,
                        temperature=0.1,
                    ),
                )

            response = _call_gemini_retried()
            if response and response.text:
                data = ExtractedClauseList.model_validate_json(response.text)
                return self._to_policy_clauses(data.clauses)

        except Exception as exc:
            logger.error("AI clause segmentation call failed: %s. Falling back to paragraph heuristics.", exc)

        return self._heuristic_segmentation_fallback(document_text)

    def _to_policy_clauses(self, items: list[ExtractedClauseItem]) -> list[PolicyClause]:
        result: list[PolicyClause] = []
        parent_id_by_level: dict[int, uuid.UUID] = {}

        for idx, item in enumerate(items):
            clause_id = uuid.uuid4()
            level = max(1, item.level)

            # Determine parent_id from previous higher levels
            parent_id = None
            for parent_level in range(level - 1, 0, -1):
                if parent_level in parent_id_by_level:
                    parent_id = parent_id_by_level[parent_level]
                    break

            parent_id_by_level[level] = clause_id
            # Clear deeper nesting levels
            for deeper in list(parent_id_by_level.keys()):
                if deeper > level:
                    del parent_id_by_level[deeper]

            marker_type = ClauseMarkerType.HEADING if level == 1 else ClauseMarkerType.SUBHEADING
            if not item.heading and not item.clause_number:
                marker_type = ClauseMarkerType.BODY

            result.append(
                PolicyClause(
                    id=clause_id,
                    parent_id=parent_id,
                    order_index=idx,
                    level=level,
                    marker_type=marker_type,
                    clause_number=item.clause_number,
                    heading=item.heading,
                    text=item.text,
                )
            )

        return result

    def _heuristic_segmentation_fallback(self, document_text: str) -> list[PolicyClause]:
        """Fall back to breaking document by paragraph double-newlines into logical clauses."""
        paragraphs = [p.strip() for p in document_text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in document_text.split("\n") if p.strip()]

        result: list[PolicyClause] = []
        for idx, para in enumerate(paragraphs):
            first_line, _, rest = para.partition("\n")
            heading = None
            text_content = para

            # If first line is short (< 80 chars), treat it as heading
            if len(first_line) <= 80 and rest.strip():
                heading = first_line.strip()
                text_content = rest.strip()

            result.append(
                PolicyClause(
                    id=uuid.uuid4(),
                    parent_id=None,
                    order_index=idx,
                    level=1,
                    marker_type=ClauseMarkerType.HEADING if heading else ClauseMarkerType.BODY,
                    clause_number=f"Section {idx + 1}" if heading else None,
                    heading=heading,
                    text=text_content,
                )
            )

        return result
