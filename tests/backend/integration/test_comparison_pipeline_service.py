"""Integration tests for the ComparisonPipelineService."""

from __future__ import annotations

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.company import Company
from backend.models.user import User
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.conflict import Conflict
from backend.models.enums import PolicyDocumentFileType
from backend.services.comparison.comparison_pipeline_service import ComparisonPipelineService


def test_comparison_pipeline_end_to_end(db_session: Session, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    # 1. Create two policies belonging to the same company
    policy_a = Policy(company=company, title="Existing Security Policy")
    policy_b = Policy(company=company, title="New Security Policy")
    db_session.add_all([policy_a, policy_b])
    db_session.flush()

    version_a = PolicyVersion(
        policy=policy_a,
        version_number=1,
        source_file_reference="path/a.pdf",
        file_hash="hasha",
        uploaded_by=user,
        original_filename="a.pdf",
        size_bytes=512,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    version_b = PolicyVersion(
        policy=policy_b,
        version_number=1,
        source_file_reference="path/b.pdf",
        file_hash="hashb",
        uploaded_by=user,
        original_filename="b.pdf",
        size_bytes=512,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add_all([version_a, version_b])
    db_session.flush()

    policy_a.current_version = version_a
    policy_b.current_version = version_b
    db_session.flush()

    # Create Clauses
    c_a = Clause(policy_id=policy_a.id, policy_version_id=version_a.id, clause_number="1.1", text="Existing clause body", order_index=1)
    c_b = Clause(policy_id=policy_b.id, policy_version_id=version_b.id, clause_number="1.1", text="New clause body", order_index=1)
    db_session.add_all([c_a, c_b])
    db_session.flush()

    # Create Obligations: Modality mismatch (Must vs May) representing contradiction
    ob_a = Obligation(
        clause_id=c_a.id,
        policy_id=policy_a.id,
        subject="Staff",
        action="attend training",
        object="security training",
        modality="Must",
        compliance_category="Security",
        confidence_score=0.98,
        ai_model="mock"
    )
    ob_b = Obligation(
        clause_id=c_b.id,
        policy_id=policy_b.id,
        subject="Staff",
        action="attend training",
        object="security training",
        modality="May",
        compliance_category="Security",
        confidence_score=0.98,
        ai_model="mock"
    )
    db_session.add_all([ob_a, ob_b])
    db_session.commit()

    # Run the comparison pipeline
    pipeline = ComparisonPipelineService(db_session)
    conflicts = pipeline.run_pipeline(version_b.id)

    # We expect 3 conflict records: 1 contradiction and 2 missing gaps (since mock similarity is low)
    assert len(conflicts) == 3
    
    contradictions = [c for c in conflicts if c.conflict_type == "contradiction"]
    assert len(contradictions) == 1
    conflict = contradictions[0]
    
    assert conflict.severity == "high"
    assert conflict.source_policy_id == policy_a.id
    assert conflict.target_policy_id == policy_b.id
    assert conflict.source_obligation_id == ob_a.id
    assert conflict.target_obligation_id == ob_b.id
    assert conflict.status == "Open"

    # Query DB directly to verify persistence
    db_conflicts = db_session.scalars(
        select(Conflict).where(Conflict.target_policy_id == policy_b.id)
    ).all()
    assert len(db_conflicts) == 3
