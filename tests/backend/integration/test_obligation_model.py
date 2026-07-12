"""Integration tests for the new AI-based Obligation database model."""

from __future__ import annotations

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from datetime import datetime, timezone

from backend.models.company import Company
from backend.models.user import User
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.enums import PolicyDocumentFileType


def test_obligation_database_persistence_and_relationships(
    db_session: Session, seeded_company_and_user
) -> None:
    company, user = seeded_company_and_user

    # 1. Setup nested structures
    policy = Policy(company=company, title="Obligation Verification Policy")
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

    clause = Clause(
        policy_id=policy.id,
        policy_version_id=version.id,
        clause_number="1.2",
        heading="Security Requirements",
        text="All users must change passwords every 90 days.",
    )
    db_session.add(clause)
    db_session.flush()

    # 2. Instantiate and persist the new Obligation model
    obligation = Obligation(
        clause_id=clause.id,
        policy_id=policy.id,
        subject="All users",
        action="change",
        object="passwords",
        modality="Must",
        conditions="On password expiry",
        time_constraint="Every 90 days",
        compliance_category="Access Control",
        confidence_score=0.98,
        ai_model="gemini-2.5-flash",
    )
    db_session.add(obligation)
    db_session.commit()

    # 3. Retrieve and assert
    retrieved = db_session.get(Obligation, obligation.id)
    assert retrieved is not None
    assert retrieved.clause_id == clause.id
    assert retrieved.policy_id == policy.id
    assert retrieved.subject == "All users"
    assert retrieved.action == "change"
    assert retrieved.object == "passwords"
    assert retrieved.modality == "Must"
    assert retrieved.conditions == "On password expiry"
    assert retrieved.time_constraint == "Every 90 days"
    assert retrieved.compliance_category == "Access Control"
    assert retrieved.confidence_score == 0.98
    assert retrieved.ai_model == "gemini-2.5-flash"
    assert retrieved.created_at is not None
    assert retrieved.updated_at is not None

    # Verify relationships
    assert retrieved.clause.id == clause.id
    assert retrieved.clause.heading == "Security Requirements"
    assert retrieved.policy.id == policy.id
    assert retrieved.policy.title == "Obligation Verification Policy"
