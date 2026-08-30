"""Verification tests for the AI Recommendation pipeline and status updating endpoints."""

from __future__ import annotations

import time
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation
from backend.services.comparison.comparison_pipeline_service import ComparisonPipelineService
from backend.models.enums import PolicyDocumentFileType


def test_recommendation_pipeline_verification(db_session: Session, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    # 1. Pre-seed policies and versions
    policy_a = Policy(company=company, title="Global Security Policy v1")
    policy_b = Policy(company=company, title="Global Security Policy v2")
    db_session.add_all([policy_a, policy_b])
    db_session.flush()

    version_a = PolicyVersion(
        policy=policy_a,
        version_number=1,
        source_file_reference="ref_a.pdf",
        file_hash="hash_a",
        uploaded_by=user,
        original_filename="a.pdf",
        size_bytes=512,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    version_b = PolicyVersion(
        policy=policy_b,
        version_number=1,
        source_file_reference="ref_b.pdf",
        file_hash="hash_b",
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

    # Clauses
    c_a = Clause(policy_id=policy_a.id, policy_version_id=version_a.id, clause_number="2.1", text="All servers must run TLS 1.3.", order_index=1)
    c_b = Clause(policy_id=policy_b.id, policy_version_id=version_b.id, clause_number="2.1", text="All servers should run TLS 1.2 or TLS 1.3.", order_index=1)
    db_session.add_all([c_a, c_b])
    db_session.flush()

    # Obligations
    ob_a = Obligation(
        clause_id=c_a.id, policy_id=policy_a.id,
        subject="servers", action="run TLS 1.3", object="all servers",
        modality="Must", compliance_category="Security", confidence_score=0.98, ai_model="mock"
    )
    ob_b = Obligation(
        clause_id=c_b.id, policy_id=policy_b.id,
        subject="servers", action="run TLS 1.2 or TLS 1.3", object="all servers",
        modality="Should", compliance_category="Security", confidence_score=0.95, ai_model="mock"
    )
    db_session.add_all([ob_a, ob_b])
    db_session.commit()

    # 2. Run Pipeline & Profile Execution Time
    start_time = time.perf_counter()
    pipeline = ComparisonPipelineService(db_session)
    conflicts_stored = pipeline.run_pipeline(version_b.id)
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    # 3. Assertions
    # Verify conflicts and corresponding recommendations are successfully stored in db
    assert len(conflicts_stored) > 0
    
    # Query Recommendations for conflicts in this pipeline run
    conflict_ids = [c.id for c in conflicts_stored]
    recommendations = db_session.scalars(
        select(Recommendation).where(
            Recommendation.conflict_id.in_(conflict_ids),
            Recommendation.deleted_at.is_(None)
        )
    ).all()

    assert len(recommendations) > 0
    rec = recommendations[0]
    assert rec.status == "Pending"
    assert rec.confidence_score >= 0.90

    # 4. Perform Accept status transition
    rec.status = "Accepted"
    db_session.commit()

    # Calculate statistics for the report
    total_recs = len(recommendations)
    avg_confidence = sum(r.confidence_score for r in recommendations) / total_recs if total_recs > 0 else 0.0
    accepted_count = sum(1 for r in recommendations if r.status == "Accepted")
    rejected_count = sum(1 for r in recommendations if r.status == "Rejected")

    # 5. Write Report
    report_content = f"""# AI Recommendation Pipeline Verification Report

Generated: {datetime.now(timezone.utc).isoformat()}
Verification Status: SUCCESS

## Execution Statistics
- **Processing Time**: {duration_ms:.2f} ms
- **Number of Generated Recommendations**: {total_recs}
- **Average Recommendation Confidence Score**: {avg_confidence:.2f}
- **Accepted Recommendations**: {accepted_count}
- **Rejected Recommendations**: {rejected_count}

## Detailed Recommendation Records
"""
    for r in recommendations:
        report_content += f"""
### Recommendation ID: `{r.id}`
- **Conflict ID**: `{r.conflict_id}`
- **Suggested Action**: **{r.suggested_action}**
- **Confidence Score**: {r.confidence_score:.2f}
- **Status**: {r.status}
- **AI Model**: `{r.ai_model}`
- **Summary**: {r.recommendation_summary}
- **Reasoning**: {r.reason}
- **Original Clause**: *"{r.original_clause}"*
- **Revised Clause Suggestion**: *"{r.revised_clause}"*
---
"""

    report_path = (__import__("os").environ.get("ANTIGRAVITY_ARTIFACT_DIR") or str(__import__("pathlib").Path(__import__("os").environ.get("USERPROFILE") or __import__("os").environ.get("HOME", "")) / ".gemini" / "antigravity" / "brain" / __import__("os").environ.get("ANTIGRAVITY_CONVERSATION_ID", ""))) + "/recommendation_verification_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n[Verification] Created recommendation report at {report_path}")
