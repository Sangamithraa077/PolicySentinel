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


from backend.services.ai.gemini_client import create_gemini_client, is_circuit_broken, trip_circuit_breaker

class AIRegulatoryMappingService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self._db = db
        self._settings = settings or get_settings()
        self._client = create_gemini_client(self._settings)
        self._kb_service = RegulatoryKnowledgeBaseService(db)

    def map_obligation(self, obligation: Obligation) -> AIRegulatoryMappingResult:
        """Compares an obligation against the Regulatory Knowledge Base using Gemini AI or rule-based mapping."""
        # Ensure default regulatory knowledge base is seeded
        self._kb_service.seed_default_frameworks()
        
        if self._client is None or is_circuit_broken():
            return self._get_rule_based_mapping(obligation)

        # Retrieve all active regulatory clauses to form the prompt catalog
        clauses = self._kb_service.list_clauses()
        clauses_context = []
        for cl in clauses:
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
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc) or "quota" in str(exc).lower():
                trip_circuit_breaker("429 Quota Exceeded")
            logger.error("Failed to run AI regulatory mapping: %s. Falling back to rule-based engine.", exc)
            return self._get_rule_based_mapping(obligation)

    def _get_rule_based_mapping(self, obligation: Obligation) -> AIRegulatoryMappingResult:
        """Rules-based keyword engine to evaluate and map obligations to frameworks without AI overhead."""
        text_to_search = f"{obligation.subject} {obligation.action} {obligation.object} {obligation.compliance_category}".lower()

        # 1. ISO 27001 - Access Control
        if any(k in text_to_search for k in ["access", "credential", "password", "mfa", "authenticate", "privilege", "role-based", "login"]):
            return AIRegulatoryMappingResult(
                framework_name="ISO 27001",
                clause_number="A.9.1.1",
                confidence_score=0.94,
                explanation="Mapped to ISO 27001 A.9.1.1 Access Control Policy covering authentication, credentials, and user access authorization."
            )

        # 2. ISO 27001 - Event Logging & Audit
        if any(k in text_to_search for k in ["log", "logging", "audit trail", "event log", "monitoring", "siem"]):
            return AIRegulatoryMappingResult(
                framework_name="ISO 27001",
                clause_number="A.12.4.1",
                confidence_score=0.95,
                explanation="Mapped to ISO 27001 A.12.4.1 Event Logging requirement for producing, keeping, and reviewing security audit records."
            )

        # 3. GDPR - Security of Processing & Incident Response
        if any(k in text_to_search for k in ["incident", "breach", "vulnerability", "security event", "threat", "ciso", "notify"]):
            return AIRegulatoryMappingResult(
                framework_name="GDPR",
                clause_number="Article 32",
                confidence_score=0.92,
                explanation="Mapped to GDPR Article 32 (Security of Processing) requiring timely detection, reporting, and remediation of security incidents."
            )

        # 4. GDPR - Data Integrity, Encryption & Confidentiality
        if any(k in text_to_search for k in ["encrypt", "confidential", "integrity", "data security", "data protection", "dpo", "personal data"]):
            return AIRegulatoryMappingResult(
                framework_name="GDPR",
                clause_number="Article 5(1)(f)",
                confidence_score=0.93,
                explanation="Mapped to GDPR Article 5(1)(f) Integrity and Confidentiality principle for protecting data against unauthorized or unlawful processing."
            )

        # 5. GDPR - Right to Erasure / Data Subject Rights
        if any(k in text_to_search for k in ["erase", "erasure", "forget", "delete user", "data subject", "privacy"]):
            return AIRegulatoryMappingResult(
                framework_name="GDPR",
                clause_number="Article 17(1)",
                confidence_score=0.92,
                explanation="Mapped to GDPR Article 17(1) Right to Erasure ('right to be forgotten') and personal data retention limits."
            )

        # 6. RBI - Record Retention
        if any(k in text_to_search for k in ["retain", "retention", "transaction record", "store record", "preserve record", "5 years"]):
            return AIRegulatoryMappingResult(
                framework_name="RBI",
                clause_number="Clause 38",
                confidence_score=0.91,
                explanation="Mapped to RBI Clause 38 Maintenance of Records requiring preservation of records and transactions for compliance verification."
            )

        # 7. RBI - Customer Due Diligence / KYC
        if any(k in text_to_search for k in ["kyc", "cdd", "customer due diligence", "customer identification", "verify identity"]):
            return AIRegulatoryMappingResult(
                framework_name="RBI",
                clause_number="Clause 23",
                confidence_score=0.90,
                explanation="Mapped to RBI Clause 23 Customer Due Diligence (CDD) guidelines for customer onboarding and ongoing verification."
            )

        # 8. SEBI - Disclosure of Material Events & Anti-Corruption/Ethics
        if any(k in text_to_search for k in ["disclose", "disclosure", "material event", "lodr", "brib", "corruption", "gift", "hospitality", "whistleblow", "conflict of interest"]):
            return AIRegulatoryMappingResult(
                framework_name="SEBI",
                clause_number="Regulation 30",
                confidence_score=0.93,
                explanation="Mapped to SEBI Regulation 30 governing disclosure of material events, corporate governance, and anti-corruption transparency."
            )

        # 9. SEBI - Asset Inventory & Infrastructure Security
        if any(k in text_to_search for k in ["asset inventory", "hardware", "software", "network connection", "infrastructure", "system admin"]):
            return AIRegulatoryMappingResult(
                framework_name="SEBI",
                clause_number="Circular Clause 4",
                confidence_score=0.91,
                explanation="Mapped to SEBI Cybersecurity Circular Clause 4 requiring comprehensive asset inventory and risk management."
            )

        # 10. ISO 27001 - General Compliance & Statutory Identification
        if any(k in text_to_search for k in ["compliance", "legal", "statutory", "contractual", "standard", "policy"]):
            return AIRegulatoryMappingResult(
                framework_name="ISO 27001",
                clause_number="A.18.1.1",
                confidence_score=0.88,
                explanation="Mapped to ISO 27001 A.18.1.1 Identification of applicable legislation and compliance approach."
            )

        return AIRegulatoryMappingResult(
            framework_name="NONE",
            clause_number="NONE",
            confidence_score=0.0,
            explanation="No matching external regulatory control identified in the Regulatory Knowledge Base."
        )
from backend.models.regulatory_framework import RegulatoryFramework
