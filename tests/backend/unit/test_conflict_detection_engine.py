"""Unit tests for the ConflictDetectionEngine."""

from __future__ import annotations

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.models.company import Company
from backend.models.user import User
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.enums import PolicyDocumentFileType
from backend.services.comparison.conflict_detection_engine import ConflictDetectionEngine


def test_conflict_detection_logic(db_session: Session, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    policy = Policy(company=company, title="Conflict Logic Test Policy")
    db_session.add(policy)
    db_session.flush()

    version_a = PolicyVersion(
        policy=policy,
        version_number=1,
        source_file_reference="path/a.pdf",
        file_hash="hasha",
        uploaded_by=user,
        original_filename="a.pdf",
        size_bytes=1024,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    version_b = PolicyVersion(
        policy=policy,
        version_number=2,
        source_file_reference="path/b.pdf",
        file_hash="hashb",
        uploaded_by=user,
        original_filename="b.pdf",
        size_bytes=1024,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add_all([version_a, version_b])
    db_session.flush()

    # Create Clauses for Version A
    c_a1 = Clause(policy_id=policy.id, policy_version_id=version_a.id, clause_number="1", text="Clause 1", order_index=1)
    c_a2 = Clause(policy_id=policy.id, policy_version_id=version_a.id, clause_number="2", text="Clause 2", order_index=2)
    # Create Clauses for Version B
    c_b1 = Clause(policy_id=policy.id, policy_version_id=version_b.id, clause_number="1", text="Clause 1", order_index=1)
    c_b2 = Clause(policy_id=policy.id, policy_version_id=version_b.id, clause_number="2", text="Clause 2", order_index=2)
    db_session.add_all([c_a1, c_a2, c_b1, c_b2])
    db_session.flush()

    # Create Obligations for Version A
    ob_a1 = Obligation(
        clause_id=c_a1.id,
        policy_id=policy.id,
        subject="Users",
        action="change passwords",
        object="accounts",
        modality="Must",
        time_constraint="90 days",
        compliance_category="Identity",
        confidence_score=0.95,
        ai_model="mock"
    )
    ob_a2 = Obligation(
        clause_id=c_a2.id,
        policy_id=policy.id,
        subject="Admins",
        action="review logs",
        object="audit log files",
        modality="Should",
        time_constraint=None,
        compliance_category="Logging",
        confidence_score=0.95,
        ai_model="mock"
    )
    # Create Obligations for Version B
    # Duplicate (Identical modality)
    ob_b1 = Obligation(
        clause_id=c_b1.id,
        policy_id=policy.id,
        subject="Users",
        action="change passwords",
        object="accounts",
        modality="Must",
        time_constraint="90 days",
        compliance_category="Identity",
        confidence_score=0.95,
        ai_model="mock"
    )
    # Contradiction (Opposing modality: Should vs Must)
    ob_b2 = Obligation(
        clause_id=c_b2.id,
        policy_id=policy.id,
        subject="Admins",
        action="review logs",
        object="audit log files",
        modality="Must",
        time_constraint=None,
        compliance_category="Logging",
        confidence_score=0.95,
        ai_model="mock"
    )
    db_session.add_all([ob_a1, ob_a2, ob_b1, ob_b2])
    db_session.commit()

    # Fake pairwise comparison results
    comparisons = [
        # Match ob_a1 vs ob_b1 (Duplicate)
        {
            "obligation_a": ob_a1,
            "obligation_b": ob_b1,
            "similarity_score": 0.99,
            "category": "Exact Match"
        },
        # Match ob_a2 vs ob_b2 (Contradiction)
        {
            "obligation_a": ob_a2,
            "obligation_b": ob_b2,
            "similarity_score": 0.85,
            "category": "Similar"
        }
    ]

    engine = ConflictDetectionEngine(db_session)
    conflicts = engine.detect_conflicts(version_a.id, version_b.id, comparisons)

    # We expect:
    # 1. Duplicate for a1 vs b1 (low severity)
    # 2. Contradiction for a2 vs b2 (medium severity because Should -> Must, no strict/soft inversion)
    # Wait, let's look at the result counts
    duplicates = [c for c in conflicts if c["type"] == "duplicate"]
    contradictions = [c for c in conflicts if c["type"] == "contradiction"]
    missing = [c for c in conflicts if c["type"] == "missing"]

    assert len(duplicates) == 1
    assert duplicates[0]["severity"] == "low"
    assert duplicates[0]["obligation_a_id"] == ob_a1.id

    assert len(contradictions) == 1
    assert contradictions[0]["severity"] == "high"
    assert contradictions[0]["obligation_b_id"] == ob_b2.id
