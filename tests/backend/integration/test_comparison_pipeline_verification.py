"""Verification tests for the compliance policy comparison pipeline and auto-generation of verification report."""

from __future__ import annotations

import os
import pytest
import time
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
from backend.services.comparison.semantic_comparison_service import SemanticComparisonService
from backend.services.comparison.conflict_detection_engine import ConflictDetectionEngine


def test_comparison_pipeline_verification_report(db_session: Session, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    # 1. Pre-seed policies
    policy_a = Policy(company=company, title="Corporate Access Policy v1")
    policy_b = Policy(company=company, title="Corporate Access Policy v2")
    db_session.add_all([policy_a, policy_b])
    db_session.flush()

    version_a = PolicyVersion(
        policy=policy_a,
        version_number=1,
        source_file_reference="ref1.pdf",
        file_hash="hash1",
        uploaded_by=user,
        original_filename="v1.pdf",
        size_bytes=256,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    version_b = PolicyVersion(
        policy=policy_b,
        version_number=1,
        source_file_reference="ref2.pdf",
        file_hash="hash2",
        uploaded_by=user,
        original_filename="v2.pdf",
        size_bytes=256,
        file_type=PolicyDocumentFileType.PDF,
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add_all([version_a, version_b])
    db_session.flush()

    policy_a.current_version = version_a
    policy_b.current_version = version_b
    db_session.flush()

    c_a = Clause(policy_id=policy_a.id, policy_version_id=version_a.id, clause_number="1", text="Clause A text", order_index=1)
    c_b = Clause(policy_id=policy_b.id, policy_version_id=version_b.id, clause_number="1", text="Clause B text", order_index=1)
    db_session.add_all([c_a, c_b])
    db_session.flush()

    # Seed 3 obligations to test all 3 conflict categories:
    # Pair 1: Modality variance (Must vs Should) -> contradiction
    # Pair 2: Identical match -> duplicate
    # Pair 3: Missing in v2 (gap)
    ob_a1 = Obligation(
        clause_id=c_a.id, policy_id=policy_a.id,
        subject="Users", action="rotate passwords", object="every 90 days",
        modality="Must", compliance_category="Security", confidence_score=0.98, ai_model="mock"
    )
    ob_b1 = Obligation(
        clause_id=c_b.id, policy_id=policy_b.id,
        subject="Users", action="rotate passwords", object="every 90 days",
        modality="Should", compliance_category="Security", confidence_score=0.98, ai_model="mock"
    )

    ob_a2 = Obligation(
        clause_id=c_a.id, policy_id=policy_a.id,
        subject="Admins", action="review logs", object="daily logs",
        modality="Must", compliance_category="Audit", confidence_score=0.95, ai_model="mock"
    )
    ob_b2 = Obligation(
        clause_id=c_b.id, policy_id=policy_b.id,
        subject="Admins", action="review logs", object="daily logs",
        modality="Must", compliance_category="Audit", confidence_score=0.95, ai_model="mock"
    )

    ob_a3 = Obligation(
        clause_id=c_a.id, policy_id=policy_a.id,
        subject="Staff", action="sign NDA", object="NDA agreements",
        modality="Must", compliance_category="Legal", confidence_score=0.97, ai_model="mock"
    )

    db_session.add_all([ob_a1, ob_b1, ob_a2, ob_b2, ob_a3])
    db_session.commit()

    # 2. Run Pipeline & Profile Execution Time
    start_time = time.perf_counter()

    comp_service = SemanticComparisonService(db_session)
    comparisons = comp_service.compare_versions(version_a.id, version_b.id)

    conflict_engine = ConflictDetectionEngine(db_session)
    conflicts_detected = conflict_engine.detect_conflicts(version_a.id, version_b.id, comparisons)

    pipeline = ComparisonPipelineService(db_session)
    conflicts_stored = pipeline.run_pipeline(version_b.id)

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    # 3. Assertions
    # Verify embedding and similarity logic
    assert len(comparisons) > 0
    # Match accuracy check: Pair 2 must be an exact/duplicate match
    dup_comp = [c for c in comparisons if c["obligation_a"].id == ob_a2.id and c["obligation_b"].id == ob_b2.id]
    assert len(dup_comp) == 1
    assert dup_comp[0]["similarity_score"] >= 0.98

    # Verify conflict categories detected
    types_found = {c.conflict_type for c in conflicts_stored}
    assert "contradiction" in types_found
    assert "duplicate" in types_found
    assert "missing" in types_found

    # Verify db storage
    db_conflicts = db_session.scalars(
        select(Conflict).where(Conflict.target_policy_id == policy_b.id)
    ).all()
    assert len(db_conflicts) == len(conflicts_stored)

    # 4. Generate Verification Report Markdown
    report_content = f"""# Policy Comparison Pipeline Verification Report

Generated: {datetime.now(timezone.utc).isoformat()}
Verification Status: SUCCESS

## Execution Statistics
- **Processing Time**: {duration_ms:.2f} ms
- **Number of Compared Obligations**: {len(comparisons)}
- **Number of Detected Conflicts**: {len(conflicts_stored)}

## Detailed Comparisons
| Source Obligation ID | Target Obligation ID | Similarity Score | Match Class |
| --- | --- | --- | --- |
"""
    for c in comparisons:
        score = c["similarity_score"]
        match_class = "Exact" if score >= 0.98 else "Similar" if score >= 0.70 else "Different"
        report_content += f"| `{c['obligation_a'].id}` | `{c['obligation_b'].id}` | {score:.4f} | {match_class} |\n"

    report_content += """
## Detected Conflicts
| Conflict ID | Source Policy | Target Policy | Conflict Type | Severity | Status | AI Explanation |
| --- | --- | --- | --- | --- | --- | --- |
"""
    for con in conflicts_stored:
        report_content += (
            f"| `{con.id}` | {policy_a.title} | {policy_b.title} | {con.conflict_type} | "
            f"{con.severity} | {con.status} | {con.ai_explanation} |\n"
        )

    # Write the report to the artifacts directory
    artifact_path = "C:/Users/Santhoshkumar/.gemini/antigravity-ide/brain/2ea7d0ac-c388-4d80-b068-182b034c1145/verification_report.md"
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    with open(artifact_path, "w", encoding="utf-8") as f:
        f.write(report_content)
