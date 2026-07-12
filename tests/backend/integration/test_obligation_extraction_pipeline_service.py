"""Integration tests for ObligationExtractionPipelineService."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.enums import PolicyDocumentFileType
from backend.services.ai.obligation_extractor_service import ObligationExtractorService, ObligationExtractionResult
from backend.services.ai.obligation_extraction_pipeline_service import ObligationExtractionPipelineService


def test_obligation_pipeline_runs_and_stores_obligations(
    db_session: Session, seeded_company_and_user
) -> None:
    company, user = seeded_company_and_user

    # 1. Setup policy structures
    policy = Policy(company=company, title="Pipeline Policy")
    db_session.add(policy)
    db_session.flush()

    version = PolicyVersion(
        policy=policy,
        version_number=1,
        source_file_reference="dummy/path.pdf",
        file_hash="dummyhash",
        uploaded_by=user,
        original_filename="dummy.pdf",
        size_bytes=1024,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(version)
    db_session.flush()

    clause1 = Clause(
        policy_id=policy.id,
        policy_version_id=version.id,
        clause_number="1",
        heading="Scope",
        text="All employees must complete training.",
    )
    clause2 = Clause(
        policy_id=policy.id,
        policy_version_id=version.id,
        clause_number="2",
        heading="Exceptions",
        text="Exceptions must be logged by CISO.",
    )
    db_session.add_all([clause1, clause2])
    db_session.commit()

    # 2. Mock extractor service to return predictable responses
    extractor = MagicMock(spec=ObligationExtractorService)
    extractor._settings = MagicMock()
    extractor._settings.GEMINI_MODEL = "gemini-2.5-flash"
    
    res1 = ObligationExtractionResult(
        subject="All employees",
        action="complete",
        object="training",
        modality="Must",
        conditions=None,
        time_constraints=None,
        compliance_category="HR Training",
        confidence_score=0.95
    )
    res2 = ObligationExtractionResult(
        subject="CISO",
        action="log",
        object="exceptions",
        modality="Must",
        conditions=None,
        time_constraints=None,
        compliance_category="Security",
        confidence_score=0.90
    )
    extractor.extract_obligation.side_effect = [res1, res2]

    # 3. Run pipeline
    pipeline = ObligationExtractionPipelineService(db_session, extractor_service=extractor)
    obligations = pipeline.run_pipeline(version.id)

    # 4. Verify results
    assert len(obligations) == 2
    assert obligations[0].subject == "All employees"
    assert obligations[0].action == "complete"
    assert obligations[0].object == "training"
    assert obligations[0].modality == "Must"
    assert obligations[0].compliance_category == "HR Training"
    assert obligations[0].confidence_score == 0.95
    assert obligations[0].ai_model == "gemini-2.5-flash"

    assert obligations[1].subject == "CISO"
    assert obligations[1].action == "log"
    assert obligations[1].object == "exceptions"
    assert obligations[1].modality == "Must"
    assert obligations[1].compliance_category == "Security"
    assert obligations[1].confidence_score == 0.90
    assert obligations[1].ai_model == "gemini-2.5-flash"


def test_obligation_pipeline_resilient_to_individual_clause_failure(
    db_session: Session, seeded_company_and_user
) -> None:
    company, user = seeded_company_and_user

    # 1. Setup policy structures
    policy = Policy(company=company, title="Failover Policy")
    db_session.add(policy)
    db_session.flush()

    version = PolicyVersion(
        policy=policy,
        version_number=1,
        source_file_reference="dummy/path.pdf",
        file_hash="dummyhash",
        uploaded_by=user,
        original_filename="dummy.pdf",
        size_bytes=1024,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(version)
    db_session.flush()

    clause1 = Clause(
        policy_id=policy.id,
        policy_version_id=version.id,
        clause_number="1",
        heading="Failure Clause",
        text="This clause will fail extraction.",
    )
    clause2 = Clause(
        policy_id=policy.id,
        policy_version_id=version.id,
        clause_number="2",
        heading="Success Clause",
        text="This clause will succeed.",
    )
    db_session.add_all([clause1, clause2])
    db_session.commit()

    # 2. Mock extractor to raise error on first, succeed on second
    extractor = MagicMock(spec=ObligationExtractorService)
    extractor._settings = MagicMock()
    extractor._settings.GEMINI_MODEL = "gemini-2.5-flash"
    
    res2 = ObligationExtractionResult(
        subject="Users",
        action="succeed",
        object="obligations",
        modality="Should",
        conditions=None,
        time_constraints=None,
        compliance_category="Test",
        confidence_score=0.88
    )
    extractor.extract_obligation.side_effect = [RuntimeError("Gemini call limit exceeded"), res2]

    # 3. Run pipeline
    pipeline = ObligationExtractionPipelineService(db_session, extractor_service=extractor)
    obligations = pipeline.run_pipeline(version.id)

    # 4. Verify that only 1 obligation was stored, but the pipeline finished successfully!
    assert len(obligations) == 1
    assert obligations[0].subject == "Users"
    assert obligations[0].action == "succeed"
    assert obligations[0].object == "obligations"
    assert obligations[0].modality == "Should"
    assert obligations[0].compliance_category == "Test"
    assert obligations[0].confidence_score == 0.88
