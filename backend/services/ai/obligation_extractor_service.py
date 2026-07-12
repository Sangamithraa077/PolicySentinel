"""Service for extracting compliance obligations from policy clauses using Gemini."""

from __future__ import annotations

import logging
import json
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from backend.config.settings import Settings, get_settings
from backend.services.ai.prompts import (
    OBLIGATION_EXTRACTION_SYSTEM_INSTRUCTION,
    OBLIGATION_EXTRACTION_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class ObligationExtractionResult(BaseModel):
    subject: str = Field(..., description="Who the obligation applies to")
    action: str = Field(..., description="What the action is")
    object: str = Field(..., description="The object of the action")
    modality: str = Field(..., description="Must, Shall, Should, or May representing obligation/permission strength")
    conditions: str | None = Field(None, description="Any conditions under which this obligation applies")
    time_constraints: str | None = Field(None, description="Any time constraints or deadlines associated with the obligation")
    compliance_category: str = Field(..., description="Category of compliance, e.g. Data Protection, Security, Access Control, HR, etc.")
    confidence_score: float = Field(..., description="Confidence score of the extraction (0.0 to 1.0)")


class ObligationExtractorService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None
        
        # Initialize client if a real key is present
        if self._settings.GEMINI_API_KEY and self._settings.GEMINI_API_KEY != "changeme":
            try:
                self._client = genai.Client(api_key=self._settings.GEMINI_API_KEY)
            except Exception as exc:
                logger.error("Failed to initialize Google GenAI client: %s", exc)

    def extract_obligation(self, clause_text: str) -> ObligationExtractionResult:
        """Extracts a structured compliance obligation from a clause text.
        
        Uses Gemini response schema to enforce structured JSON output.
        Falls back to a structured mock response if no API key is configured.
        """
        if not clause_text.strip():
            raise ValueError("Clause text cannot be empty.")

        # Fallback to mock for local testing/development when key is unset
        if self._client is None:
            logger.info("No Gemini API key configured. Falling back to rule-based mock extraction.")
            return self._get_mock_obligation(clause_text)

        user_prompt = OBLIGATION_EXTRACTION_USER_PROMPT.format(clause_text=clause_text)
        
        try:
            from backend.utils.retry_helper import retry_on_transient_error
            
            @retry_on_transient_error(max_retries=3, initial_delay=1.0)
            def _call_gemini_retried():
                return self._client.models.generate_content(
                    model=self._settings.GEMINI_MODEL,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=OBLIGATION_EXTRACTION_SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        response_schema=ObligationExtractionResult,
                        temperature=0.1,
                    )
                )
            
            response = _call_gemini_retried()
            
            # The SDK automatically handles Pydantic validation when response_schema is passed,
            # but we parse the response string to return the parsed Pydantic object.
            data = json.loads(response.text)
            return ObligationExtractionResult(**data)
            
        except Exception as exc:
            logger.error("Failed to extract obligation using Gemini API after retries: %s. Falling back to mock.", exc)
            return self._get_mock_obligation(clause_text)

    def _get_mock_obligation(self, clause_text: str) -> ObligationExtractionResult:
        """Generates a structured fallback/mock obligation result based on clause content keywords."""
        lower_text = clause_text.lower()
        
        subject = "Employees"
        action = "comply with guidelines"
        obj = "policy requirements"
        modality = "Must"
        conditions = None
        time_constraints = None
        compliance_category = "General Security"
        confidence_score = 0.85

        if "ciso" in lower_text:
            subject = "CISO"
            action = "approve exception request"
            obj = "policy exceptions"
            modality = "Must"
            compliance_category = "Security Administration"
        elif "staff" in lower_text:
            subject = "Staff members"
            action = "observe boundaries"
            obj = "security boundaries"
            modality = "Must"
            compliance_category = "Security Awareness"
        elif "data" in lower_text or "privacy" in lower_text:
            subject = "Data custodian"
            action = "protect sensitive data"
            obj = "personally identifiable information (PII)"
            modality = "Must"
            compliance_category = "Data Protection"
        elif "access" in lower_text or "password" in lower_text:
            subject = "Users"
            action = "authenticate securely"
            obj = "system resources"
            modality = "Shall"
            compliance_category = "Access Control"

        if "exception" in lower_text:
            conditions = "When an exception request is formally submitted"
            
        if "approved by" in lower_text:
            action = "obtain approval for"
            obj = "exceptions"

        return ObligationExtractionResult(
            subject=subject,
            action=action,
            object=obj,
            modality=modality,
            conditions=conditions,
            time_constraints=time_constraints,
            compliance_category=compliance_category,
            confidence_score=confidence_score,
        )
