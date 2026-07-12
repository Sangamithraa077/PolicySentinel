"""Verification test for the compliance obligation extraction pipeline."""

from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.enums import PolicyDocumentFileType
from backend.services.ai.obligation_extractor_service import ObligationExtractorService, ObligationExtractionResult
from backend.services.ai.obligation_extraction_pipeline_service import ObligationExtractionPipelineService


def test_obligation_pipeline_verification(client: TestClient, db_session: Session, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    # 1. Setup sample document outline
    policy = Policy(company=company, title="Obligation Verification Security Policy")
    db_session.add(policy)
    db_session.flush()

    version = PolicyVersion(
        policy=policy,
        version_number=1,
        source_file_reference="verification/path.pdf",
        file_hash="verificationhash",
        uploaded_by=user,
        original_filename="verification.pdf",
        size_bytes=2048,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(version)
    db_session.flush()

    # 4 clauses: 3 normal clauses, 1 empty clause that will be skipped
    clause1 = Clause(
        policy_id=policy.id,
        policy_version_id=version.id,
        clause_number="1",
        heading="Data Privacy",
        text="Administrators must encrypt all personal databases.",
        order_index=1,
    )
    clause2 = Clause(
        policy_id=policy.id,
        policy_version_id=version.id,
        clause_number="2",
        heading="Audit Logging",
        text="Access logs should be retained for 90 days.",
        order_index=2,
    )
    clause3 = Clause(
        policy_id=policy.id,
        policy_version_id=version.id,
        clause_number="3",
        heading="Invalid Clause",
        text="This clause text will fail to analyze due to API timeouts.",
        order_index=3,
    )
    clause4 = Clause(
        policy_id=policy.id,
        policy_version_id=version.id,
        clause_number="4",
        heading="Incident Management",
        text="Staff shall report data breaches within 72 hours.",
        order_index=4,
    )
    db_session.add_all([clause1, clause2, clause3, clause4])
    db_session.commit()

    # 2. Mock extractor service to simulate Gemini response validation
    extractor = MagicMock(spec=ObligationExtractorService)
    extractor._settings = MagicMock()
    extractor._settings.GEMINI_MODEL = "gemini-2.5-flash"
    
    res1 = ObligationExtractionResult(
        subject="Administrators",
        action="encrypt",
        object="all personal databases",
        modality="Must",
        conditions=None,
        time_constraints=None,
        compliance_category="Cryptography",
        confidence_score=0.98
    )
    res2 = ObligationExtractionResult(
        subject="Access logs",
        action="retain",
        object="logs",
        modality="Should",
        conditions=None,
        time_constraints="90 days",
        compliance_category="Retention",
        confidence_score=0.92
    )
    res4 = ObligationExtractionResult(
        subject="Staff",
        action="report",
        object="data breaches",
        modality="Shall",
        conditions=None,
        time_constraints="72 hours",
        compliance_category="Incident Management",
        confidence_score=0.95
    )
    extractor.extract_obligation.side_effect = [res1, res2, RuntimeError("Gemini error"), res4]

    # 3. Execute obligation extraction pipeline
    pipeline = ObligationExtractionPipelineService(db_session, extractor_service=extractor)
    obligations = pipeline.run_pipeline(version.id)

    # Verify database storage count and contents
    assert len(obligations) == 3
    assert obligations[0].subject == "Administrators"
    assert obligations[1].time_constraint == "90 days"
    assert obligations[2].modality == "Shall"

    # 4. Verify API response output
    api_response = client.get("/api/v1/obligations", params={"policy_id": str(policy.id)})
    assert api_response.status_code == 200
    api_data = api_response.json()["items"]
    assert len(api_data) == 3
    assert api_data[0]["subject"] == "Administrators"
    assert api_data[1]["compliance_category"] == "Retention"
    assert api_data[2]["confidence_score"] == 0.95

    # 5. Calculate pipeline metrics for verification report
    processed_clauses = 4
    extracted_count = len(obligations)
    failed_count = processed_clauses - extracted_count
    avg_score = sum(o.confidence_score for o in obligations) / extracted_count if extracted_count else 0.0

    report_data = {
        "processed_clauses": processed_clauses,
        "extracted_obligations": extracted_count,
        "failed_clauses": failed_count,
        "average_confidence_score": avg_score,
        "details": [
            {
                "clause_id": str(o.clause_id),
                "subject": o.subject,
                "action": o.action,
                "modality": o.modality,
                "compliance_category": o.compliance_category,
                "confidence_score": o.confidence_score
            }
            for o in obligations
        ]
    }
    print(f"OBLIGATION_PIPELINE_VERIFICATION_REPORT:{json.dumps(report_data)}")
