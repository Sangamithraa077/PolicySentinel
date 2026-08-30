import time
from datetime import datetime
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.company import Company
from backend.models.user import User
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation
from backend.models.compliance_audit_log import ComplianceAuditLog
from backend.models.enums import PolicyDocumentFileType
from backend.services.compliance_dashboard_service import ComplianceDashboardService, record_compliance_audit_log
from backend.services.recommendation_management_service import RecommendationManagementService
from backend.services.compliance_report_generator import ComplianceReportGenerator


def test_dashboard_workflow_verification(db_session: Session, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user
    company_id = company.id

    # 1. Profile execution time & Setup mock compliance data
    start_time = time.perf_counter()
    
    # Policies
    policy = Policy(
        company_id=company_id,
        title="Verification Security Policy",
        status="active"
    )
    db_session.add(policy)
    db_session.flush()

    version = PolicyVersion(
        policy=policy,
        version_number=1,
        source_file_reference="uploads/policies/verification.pdf",
        file_hash="fake-hash",
        uploaded_by_user_id=user.id,
        status="published",
        original_filename="verification.pdf",
        size_bytes=1024,
        file_type=PolicyDocumentFileType.PDF,
        extracted_text="All developers must complete security training.",
        uploaded_at=datetime.utcnow()
    )
    policy.current_version = version
    db_session.add(version)
    db_session.flush()

    # Clauses & Obligations
    clause = Clause(policy_id=policy.id, policy_version_id=version.id, clause_number="1.0", text="All developers must complete security training.", order_index=1)
    db_session.add(clause)
    db_session.flush()

    ob = Obligation(
        clause_id=clause.id, policy_id=policy.id,
        subject="developers", action="complete security training", object="developers",
        modality="Must", compliance_category="Security", confidence_score=0.95, ai_model="mock"
    )
    db_session.add(ob)
    db_session.flush()

    # Conflict
    conflict = Conflict(
        source_policy_id=policy.id,
        target_policy_id=policy.id,
        source_obligation_id=ob.id,
        target_obligation_id=ob.id,
        conflict_type="duplicate",
        similarity_score=0.99,
        severity="High",
        ai_explanation="Identical obligation detected.",
        status="Open"
    )
    db_session.add(conflict)
    db_session.flush()

    # Recommendation
    recommendation = Recommendation(
        conflict_id=conflict.id,
        recommendation_summary="Remove duplicate obligation.",
        suggested_action="Deduplicate",
        reason="Reduces policy redundancy.",
        ai_model="mock",
        confidence_score=0.98,
        status="Pending"
    )
    db_session.add(recommendation)
    db_session.commit()

    # Record Policy sentinel events for audit trail verification
    record_compliance_audit_log(db_session, company_id, "Policy Upload", user.email, "Verification Policy uploaded")
    record_compliance_audit_log(db_session, company_id, "Text Extraction", user.email, "Verification Policy text extracted")
    record_compliance_audit_log(db_session, company_id, "Clause Segmentation", user.email, "Verification Policy segmented")
    record_compliance_audit_log(db_session, company_id, "Obligation Extraction", user.email, "Verification Policy obligations extracted")
    record_compliance_audit_log(db_session, company_id, "Conflict Detection", user.email, "Verification Policy conflicts evaluated")
    record_compliance_audit_log(db_session, company_id, "Recommendation Generation", user.email, "Verification Policy resolution recommendations generated")
    db_session.commit()

    # 2. Verify Metrics & Scoring Engine
    dashboard_service = ComplianceDashboardService(db_session)
    summary = dashboard_service.get_executive_summary(company_id)
    
    assert summary["total_policies"] > 0
    assert summary["active_conflicts"] > 0
    assert summary["pending_recommendations"] > 0
    assert summary["compliance_score"] < 100.0  # deductions for High severity conflict + Pending recommendation

    # 3. Verify Review Workflow
    rec_service = RecommendationManagementService(db_session)
    updated_rec = rec_service.update_recommendation_status(
        rec_id=recommendation.id,
        status="accepted",
        reviewer_name="Ava Thornton",
        review_comments="Deduplication approved."
    )
    assert updated_rec.status == "Accepted"
    assert updated_rec.reviewer_name == "Ava Thornton"
    assert updated_rec.review_comments == "Deduplication approved."
    assert updated_rec.reviewed_at is not None

    # Verify that a status change records a Recommendation Approval/Rejection event
    audit_logs, audit_total = dashboard_service.list_audit_history(company_id)
    assert audit_total > 0
    
    review_event = [l for l in audit_logs if l.event_type == "Recommendation Approval/Rejection"]
    assert len(review_event) > 0
    assert "Ava Thornton" in review_event[0].user_identifier

    # 4. Verify PDF report generation
    report_service = ComplianceReportGenerator(db_session)
    pdf_bytes = report_service.generate_report(company_id)
    assert len(pdf_bytes) > 0
    assert b"%PDF" in pdf_bytes[:10]

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    # 5. Write Markdown verification report
    import os
    artifact_dir = (__import__("os").environ.get("ANTIGRAVITY_ARTIFACT_DIR") or str(__import__("pathlib").Path(__import__("os").environ.get("USERPROFILE") or __import__("os").environ.get("HOME", "")) / ".gemini" / "antigravity" / "brain" / __import__("os").environ.get("ANTIGRAVITY_CONVERSATION_ID", "")))
    os.makedirs(artifact_dir, exist_ok=True)
    
    report_path = f"{artifact_dir}/dashboard_verification_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Executive Compliance Dashboard & Report Generator Verification Report\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("Verification Status: SUCCESS\n\n")
        
        f.write("## Execution Statistics\n")
        f.write(f"- **Processing Time**: {duration_ms:.2f} ms\n")
        f.write(f"- **Calculated Compliance Score**: {summary['compliance_score']}\n")
        f.write(f"- **Assessed Risk Level**: {summary['risk_level']}\n\n")
        
        f.write("## Inventory Totals\n")
        f.write(f"- **Total Policies**: {summary['total_policies']}\n")
        f.write(f"- **Total Clauses**: {summary['total_clauses']}\n")
        f.write(f"- **Total Obligations**: {summary['total_obligations']}\n")
        f.write(f"- **Active Conflicts**: {summary['active_conflicts']}\n")
        f.write(f"- **Pending Recommendations**: {summary['pending_recommendations']}\n\n")

        f.write("## Audit History Verification (Last 5 Entries)\n")
        for log in audit_logs[:5]:
            f.write(f"- **[{log.event_type}]** (Actor: {log.user_identifier}): {log.description}\n")

    print(f"[Verification] Created dashboard verification report at {report_path}")
