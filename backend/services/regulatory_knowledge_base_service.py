"""Service for managing external regulatory frameworks and external clauses in the Regulatory Knowledge Base."""
from __future__ import annotations

import logging
import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.regulatory_framework import RegulatoryFramework
from backend.models.regulatory_clause import RegulatoryClause

logger = logging.getLogger(__name__)

# Predefined standard frameworks and clauses to seed the Regulatory Knowledge Base
DEFAULT_REGULATORY_DATA = {
    "GDPR": {
        "jurisdiction": "European Union",
        "issuing_body": "European Parliament",
        "description": "General Data Protection Regulation (EU 2016/679)",
        "clauses": [
            {
                "clause_reference": "Article 5(1)(f)",
                "title": "Integrity and confidentiality",
                "text": "Personal data shall be processed in a manner that ensures appropriate security of the personal data, including protection against unauthorised or unlawful processing and against accidental loss, destruction or damage, using appropriate technical or organisational measures.",
                "category": "Data Security"
            },
            {
                "clause_reference": "Article 17(1)",
                "title": "Right to erasure ('right to be forgotten')",
                "text": "The data subject shall have the right to obtain from the controller the erasure of personal data concerning him or her without undue delay and the controller shall have the obligation to erase personal data without undue delay.",
                "category": "Data Privacy"
            },
            {
                "clause_reference": "Article 32",
                "title": "Security of processing",
                "text": "Taking into account the state of the art, the costs of implementation and the nature, scope, context and purposes of processing as well as the risk of varying likelihood and severity for the rights and freedoms of natural persons, the controller and the processor shall implement appropriate technical and organisational measures to ensure a level of security appropriate to the risk.",
                "category": "Security Standards"
            }
        ]
    },
    "ISO 27001": {
        "jurisdiction": "International",
        "issuing_body": "ISO/IEC",
        "description": "Information security management systems requirements",
        "clauses": [
            {
                "clause_reference": "A.12.4.1",
                "title": "Event logging",
                "text": "Event logs recording user activities, exceptions, faults and information security events shall be produced, kept and regularly reviewed.",
                "category": "Information Security"
            },
            {
                "clause_reference": "A.9.1.1",
                "title": "Access control policy",
                "text": "An access control policy shall be established, documented and reviewed based on business and information security requirements.",
                "category": "Access Control"
            },
            {
                "clause_reference": "A.18.1.1",
                "title": "Identification of applicable legislation and contractual requirements",
                "text": "All relevant legislative statutory, regulatory, contractual requirements and the organization's approach to meet these requirements shall be explicitly identified, documented and kept up to date for each information system and the organization.",
                "category": "Compliance"
            }
        ]
    },
    "RBI": {
        "jurisdiction": "India",
        "issuing_body": "Reserve Bank of India",
        "description": "RBI Master Directions and compliance requirements for financial institutions",
        "clauses": [
            {
                "clause_reference": "Clause 23",
                "title": "Customer Due Diligence (CDD) Procedure",
                "text": "REs (Regulated Entities) shall obtain Customer Acceptance Policy, Customer Identification Procedures, Monitoring of Transactions and Risk Management guidelines to identify customers.",
                "category": "KYC/AML"
            },
            {
                "clause_reference": "Clause 38",
                "title": "Maintenance of records of transactions",
                "text": "REs shall maintain all necessary records of transactions between REs and their customers, both domestic and international, for at least five years from the date of transaction.",
                "category": "Record Retention"
            }
        ]
    },
    "SEBI": {
        "jurisdiction": "India",
        "issuing_body": "Securities and Exchange Board of India",
        "description": "SEBI Listing Obligations and Disclosure Requirements (LODR) and Cyber Security Guidelines",
        "clauses": [
            {
                "clause_reference": "Regulation 30",
                "title": "Disclosure of material events or information",
                "text": "Every listed entity shall make disclosures of any events or information which, in the opinion of the board of directors of the listed company, is material.",
                "category": "Corporate Governance"
            },
            {
                "clause_reference": "Circular Clause 4",
                "title": "Asset Inventory and Risk Assessment",
                "text": "Stock brokers and depository participants shall maintain an up-to-date inventory of all their hardware, software devices, and network connections to identify potential security risks.",
                "category": "Cyber Security"
            }
        ]
    }
}


class RegulatoryKnowledgeBaseService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def seed_default_frameworks(self) -> None:
        """Seeds standard regulatory frameworks and external clauses if not already populated."""
        logger.info("Checking and seeding Regulatory Knowledge Base standard frameworks...")
        for name, data in DEFAULT_REGULATORY_DATA.items():
            # Check if framework already exists
            framework = self._db.scalar(
                select(RegulatoryFramework).where(RegulatoryFramework.name == name, RegulatoryFramework.deleted_at.is_(None))
            )
            if not framework:
                logger.info("Seeding framework: %s", name)
                framework = RegulatoryFramework(
                    name=name,
                    jurisdiction=data["jurisdiction"],
                    issuing_body=data["issuing_body"],
                    description=data["description"],
                    effective_date=date(2026, 1, 1)
                )
                self._db.add(framework)
                self._db.flush()

            # Seed clauses for this framework
            for cl in data["clauses"]:
                clause_ref = cl["clause_reference"]
                existing_clause = self._db.scalar(
                    select(RegulatoryClause).where(
                        RegulatoryClause.regulatory_framework_id == framework.id,
                        RegulatoryClause.clause_reference == clause_ref,
                        RegulatoryClause.deleted_at.is_(None)
                    )
                )
                if not existing_clause:
                    logger.info("Seeding clause %s under framework %s", clause_ref, name)
                    clause = RegulatoryClause(
                        regulatory_framework_id=framework.id,
                        clause_reference=clause_ref,
                        title=cl["title"],
                        text=cl["text"],
                        category=cl["category"]
                    )
                    self._db.add(clause)
        self._db.commit()
        logger.info("Regulatory Knowledge Base seeding completed.")

    def list_frameworks(self) -> list[RegulatoryFramework]:
        """Returns all active regulatory frameworks."""
        return list(self._db.scalars(
            select(RegulatoryFramework).where(RegulatoryFramework.deleted_at.is_(None)).order_by(RegulatoryFramework.name)
        ).all())

    def list_clauses(self, framework_id: uuid.UUID | None = None) -> list[RegulatoryClause]:
        """Returns active external regulatory clauses, optionally filtered by framework."""
        stmt = select(RegulatoryClause).where(RegulatoryClause.deleted_at.is_(None))
        if framework_id:
            stmt = stmt.where(RegulatoryClause.regulatory_framework_id == framework_id)
        return list(self._db.scalars(stmt.order_by(RegulatoryClause.clause_reference)).all())

    def get_clause_by_ref(self, framework_name: str, clause_reference: str) -> RegulatoryClause | None:
        """Retrieves a single external clause by framework name and reference."""
        return self._db.scalar(
            select(RegulatoryClause)
            .join(RegulatoryFramework)
            .where(
                RegulatoryFramework.name == framework_name,
                RegulatoryClause.clause_reference == clause_reference,
                RegulatoryClause.deleted_at.is_(None),
                RegulatoryFramework.deleted_at.is_(None)
            )
        )

    def add_framework(
        self, name: str, jurisdiction: str | None = None, issuing_body: str | None = None, description: str | None = None
    ) -> RegulatoryFramework:
        """Dynamically registers a new regulatory framework to allow easy future expansions."""
        framework = RegulatoryFramework(
            name=name,
            jurisdiction=jurisdiction,
            issuing_body=issuing_body,
            description=description,
            effective_date=date.today()
        )
        self._db.add(framework)
        self._db.commit()
        return framework

    def add_clause(
        self, framework_id: uuid.UUID, clause_reference: str, title: str, text: str, category: str | None = None
    ) -> RegulatoryClause:
        """Dynamically registers a new regulatory clause under a framework to allow easy future expansions."""
        clause = RegulatoryClause(
            regulatory_framework_id=framework_id,
            clause_reference=clause_reference,
            title=title,
            text=text,
            category=category
        )
        self._db.add(clause)
        self._db.commit()
        return clause
