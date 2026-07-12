"""AI Regulatory Mapping Service matching obligations against the Regulatory Knowledge Base."""
from __future__ import annotations

import logging
import json
from pydantic import BaseModel, Field, ConfigDict
from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from backend.config.settings import Settings, get_settings
from backend.models.obligation import Obligation
from backend.services.regulatory_knowledge_base_service import RegulatoryKnowledgeBaseService
from backend.services.ai.prompts import REGULATORY_MAPPING_SYSTEM_INSTRUCTION, REGULATORY_MAPPING_USER_PROMPT

logger = logging.getLogger(__name__)


class AIRegulatoryMappingResult(BaseModel):
    framework_name: str = Field(..., description="The name of the matching framework (e.g., GDPR, ISO 27001, RBI, SEBI, or NONE)")
    clause_number: str = Field(..., description="The clause number of the matching clause (e.g., Article 17(1), A.12.4.1, Clause 38, or NONE)")
    confidence_score: float = Field(..., description="Match confidence score between 0.0 and 1.0")
    explanation: str = Field(..., description="Clear explanation of why this mapping was chosen or why no match exists")

    model_config = ConfigDict(from_attributes=True)


class AIRegulatoryMappingService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self._db = db
        self._settings = settings or get_settings()
        self._client = None
        self._kb_service = RegulatoryKnowledgeBaseService(db)

        if self._settings.GEMINI_API_KEY and self._settings.GEMINI_API_KEY != "changeme":
            try:
                self._client = genai.Client(api_key=self._settings.GEMINI_API_KEY)
            except Exception as exc:
                logger.error("Failed to initialize Google GenAI client in AIRegulatoryMappingService: %s", exc)

    def map_obligation(self, obligation: Obligation) -> AIRegulatoryMappingResult:
        """Compares an obligation against the Regulatory Knowledge Base using Gemini AI or rule-based mapping."""
        # Ensure default regulatory knowledge base is seeded
        self._kb_service.seed_default_frameworks()
        
        if self._client is None:
            logger.info("No Gemini API key configured. Falling back to rule-based regulatory mapping.")
            return self._get_rule_based_mapping(obligation)

        # Retrieve all active regulatory clauses to form the prompt catalog
        clauses = self._kb_service.list_clauses()
        clauses_context = []
        for cl in clauses:
            # We want to represent the framework name along with each clause
            framework_name = self._db.scalars(
                self._db.query(RegulatoryFramework.name).filter(RegulatoryFramework.id == cl.regulatory_framework_id)
            ).first() or "Unknown"
            clauses_context.append(
                f"- Framework: {framework_name}\n"
                f"  Clause: {cl.clause_reference}\n"
                f"  Title: {cl.title}\n"
                f"  Text: {cl.text}\n"
            )
        regulatory_clauses_str = "\n".join(clauses_context)

        user_prompt = REGULATORY_MAPPING_USER_PROMPT.format(
            subject=obligation.subject,
            action=obligation.action,
            object=obligation.object,
            modality=obligation.modality,
            time_constraint=obligation.time_constraint or "N/A",
            compliance_category=obligation.compliance_category,
            regulatory_clauses=regulatory_clauses_str
        )

        try:
            response = self._client.models.generate_content(
                model=self._settings.GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=REGULATORY_MAPPING_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=AIRegulatoryMappingResult,
                    temperature=0.1,
                )
            )
            data = json.loads(response.text)
            return AIRegulatoryMappingResult(**data)
        except Exception as exc:
            logger.error("Failed to run AI regulatory mapping: %s. Falling back to rule-based engine.", exc)
            return self._get_rule_based_mapping(obligation)

    def _get_rule_based_mapping(self, obligation: Obligation) -> AIRegulatoryMappingResult:
        """Rules-based keyword engine to evaluate and map obligations to frameworks without AI overhead."""
        text_to_search = f"{obligation.subject} {obligation.action} {obligation.object} {obligation.compliance_category}".lower()

        # ISO 27001 - Logging Control
        if "log" in text_to_search or "logging" in text_to_search or "audit event" in text_to_search:
            return AIRegulatoryMappingResult(
                framework_name="ISO 27001",
                clause_number="A.12.4.1",
                confidence_score=0.95,
                explanation="Automatically mapped based on system logging, audit trails, and event logging security controls."
            )

        # GDPR - Erasure / Privacy
        if "erase" in text_to_search or "erasure" in text_to_search or "forget" in text_to_search or "delete user" in text_to_search or "privacy" in text_to_search:
            return AIRegulatoryMappingResult(
                framework_name="GDPR",
                clause_number="Article 17(1)",
                confidence_score=0.92,
                explanation="Automatically mapped based on data subject rights, right to erasure ('right to be forgotten'), and personal data retention."
            )

        # RBI - Customer verification / CDD
        if "kyc" in text_to_search or "cdd" in text_to_search or "customer due diligence" in text_to_search or "identify customer" in text_to_search:
            return AIRegulatoryMappingResult(
                framework_name="RBI",
                clause_number="Clause 23",
                confidence_score=0.88,
                explanation="Automatically mapped based on Reserve Bank of India Customer Due Diligence (CDD) guidelines."
            )

        # RBI - Record retention
        if "retain" in text_to_search or "retention" in text_to_search or "transaction record" in text_to_search:
            return AIRegulatoryMappingResult(
                framework_name="RBI",
                clause_number="Clause 38",
                confidence_score=0.90,
                explanation="Automatically mapped based on financial transaction record keeping and five-year minimum retention rules."
            )

        # SEBI - Disclosure of material events
        if "disclose" in text_to_search or "disclosure" in text_to_search or "material event" in text_to_search or "lodr" in text_to_search:
            return AIRegulatoryMappingResult(
                framework_name="SEBI",
                clause_number="Regulation 30",
                confidence_score=0.94,
                explanation="Automatically mapped based on Securities and Exchange Board of India Listing Obligations and Disclosure Requirements."
            )

        # SEBI - Asset inventory
        if "asset inventory" in text_to_search or "inventory of all" in text_to_search or "hardware inventory" in text_to_search:
            return AIRegulatoryMappingResult(
                framework_name="SEBI",
                clause_number="Circular Clause 4",
                confidence_score=0.91,
                explanation="Automatically mapped based on SEBI cybersecurity requirements for maintaining asset inventories."
            )

        return AIRegulatoryMappingResult(
            framework_name="NONE",
            clause_number="NONE",
            confidence_score=0.0,
            explanation="No matching external regulatory control identified in the Regulatory Knowledge Base."
        )
from backend.models.regulatory_framework import RegulatoryFramework
