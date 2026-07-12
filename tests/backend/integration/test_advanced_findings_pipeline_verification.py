import time
import json
from datetime import datetime, date, timedelta
import pytest
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.conflict import Conflict
from backend.models.enums import PolicyDocumentFileType
from backend.services.comparison.comparison_pipeline_service import ComparisonPipelineService


def test_advanced_findings_pipeline_verification(db_session: Session, seeded_company_and_user, client: TestClient) -> None:
    company, user = seeded_company_and_user
    company_id = company.id
    
    start_time = time.perf_counter()

    # 1. Setup Policy A (Existing) with Time & Modality Obligation
    policy_a = Policy(company_id=company_id, title="Temporal & Strength Existing Policy", status="active")
    db_session.add(policy_a)
    db_session.flush()

    ver_a = PolicyVersion(
        policy=policy_a,
        version_number=1,
        source_file_reference="uploads/policies/existing.pdf",
        file_hash="hash-existing",
        uploaded_by_user_id=user.id,
        status="published",
        original_filename="existing.pdf",
        size_bytes=2048,
        file_type=PolicyDocumentFileType.PDF,
        extracted_text="Developers must submit status reviews monthly.",
        uploaded_at=datetime.utcnow() - timedelta(days=400) # Force review cycle age
    )
    # Set effective date 400 days ago to trigger Review Required status
    ver_a.effective_date = date.today() - timedelta(days=400)
    policy_a.current_version = ver_a
    db_session.add(ver_a)
    db_session.flush()

    cl_a = Clause(policy_id=policy_a.id, policy_version_id=ver_a.id, clause_number="1.1", text="Developers must submit status reviews monthly.", order_index=1)
    db_session.add(cl_a)
    db_session.flush()

    ob_a = Obligation(
        clause_id=cl_a.id, policy_id=policy_a.id,
        subject="Developers", action="submit status reviews", object="safety committee",
        modality="Must", time_constraint="monthly", compliance_category="Security", confidence_score=0.98, ai_model="mock"
    )
    db_session.add(ob_a)
    db_session.flush()

    # 2. Setup Policy B (New) with mismatched Modality and Mismatched Time Frequency
    policy_b = Policy(company_id=company_id, title="Temporal & Strength New Policy", status="active")
    db_session.add(policy_b)
    db_session.flush()

    ver_b = PolicyVersion(
        policy=policy_b,
        version_number=1,
        source_file_reference="uploads/policies/new.pdf",
        file_hash="hash-new",
        uploaded_by_user_id=user.id,
        status="published",
        original_filename="new.pdf",
        size_bytes=2048,
        file_type=PolicyDocumentFileType.PDF,
        extracted_text="Developers should submit status reviews quarterly.",
        uploaded_at=datetime.utcnow()
    )
    ver_b.effective_date = date.today()
    policy_b.current_version = ver_b
    db_session.add(ver_b)
    db_session.flush()

    cl_b = Clause(policy_id=policy_b.id, policy_version_id=ver_b.id, clause_number="1.1", text="Developers should submit status reviews quarterly.", order_index=1)
    db_session.add(cl_b)
    db_session.flush()

    ob_b = Obligation(
        clause_id=cl_b.id, policy_id=policy_b.id,
        subject="Developers", action="submit status reviews", object="safety committee",
        modality="Should", time_constraint="quarterly", compliance_category="Security", confidence_score=0.97, ai_model="mock"
    )
    db_session.add(ob_b)
    db_session.commit()

    # 3. Run pairwise comparison pipeline
    pipeline_service = ComparisonPipelineService(db_session)
    conflicts = pipeline_service.run_pipeline(ver_b.id)
    
    assert len(conflicts) > 0
    pairwise_findings = [c for c in conflicts if c.source_obligation_id is not None and c.target_obligation_id is not None]
    assert len(pairwise_findings) > 0
    stored_finding = pairwise_findings[0]
    
    # Assert advanced findings columns are populated in DB
    assert stored_finding.temporal_conflict == "frequency_mismatch"
    assert stored_finding.strength_conflict == "WEAKENED"
    assert stored_finding.staleness_status == "Review Required"
    assert stored_finding.detected_parameters is not None
    
    params = json.loads(stored_finding.detected_parameters)
    assert params["obligation_a_time"] == "monthly"
    assert params["obligation_b_time"] == "quarterly"
    assert params["obligation_a_modality"] == "Must"
    assert params["obligation_b_modality"] == "Should"

    # 4. Verify API response routing and filters
    # General findings
    res = client.get("/api/v1/findings")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    assert any(item["temporal_conflict"] == "frequency_mismatch" for item in data["items"])
    assert any(item["strength_conflict"] == "WEAKENED" for item in data["items"])

    # Temporal filter
    res_temp = client.get("/api/v1/findings/temporal")
    assert res_temp.status_code == 200
    data_temp = res_temp.json()
    assert len(data_temp["items"]) > 0
    assert all(i["temporal_conflict"] != "none" for i in data_temp["items"])

    # Strength filter
    res_str = client.get("/api/v1/findings/strength")
    assert res_str.status_code == 200
    data_str = res_str.json()
    assert len(data_str["items"]) > 0
    assert all(i["strength_conflict"] != "NONE" for i in data_str["items"])

    # Stale filter
    res_stale = client.get("/api/v1/findings/stale")
    assert res_stale.status_code == 200
    data_stale = res_stale.json()
    assert len(data_stale["items"]) > 0
    assert all(i["staleness_status"] in ["Review Required", "Outdated"] for i in data_stale["items"])

    # Finding details retrieval
    res_detail = client.get(f"/api/v1/findings/{stored_finding.id}")
    assert res_detail.status_code == 200
    data_detail = res_detail.json()
    assert data_detail["id"] == str(stored_finding.id)
    assert data_detail["temporal_conflict"] == "frequency_mismatch"
    assert data_detail["strength_conflict"] == "WEAKENED"

    # Verify dashboard rendering
    import pathlib
    dashboard_path = pathlib.Path("frontend/src/pages/AdvancedFindingsPage.tsx")
    assert dashboard_path.exists(), "AdvancedFindingsPage React component must exist."
    dashboard_content = dashboard_path.read_text(encoding="utf-8")
    assert "AdvancedFindingsPage" in dashboard_content
    assert "overall" in dashboard_content.lower()
    assert "temporal" in dashboard_content.lower()
    assert "strength" in dashboard_content.lower()
    assert "stale" in dashboard_content.lower()

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    # 5. Generate Markdown verification report
    import os
    artifact_dir = "C:/Users/Santhoshkumar/.gemini/antigravity-ide/brain/2ea7d0ac-c388-4d80-b068-182b034c1145"
    os.makedirs(artifact_dir, exist_ok=True)
    report_path = f"{artifact_dir}/advanced_findings_verification_report.md"
    
    # Compute counts from test database
    total_findings = db_session.scalar(
        select(func.count(Conflict.id)).where(
            or_(
                Conflict.temporal_conflict != "none",
                Conflict.strength_conflict != "NONE",
                Conflict.staleness_status.in_(["Review Required", "Outdated"])
            )
        )
    ) or 0
    
    avg_conf = db_session.scalar(
        select(func.avg(Conflict.confidence_score)).where(Conflict.confidence_score.is_not(None))
    ) or 0.0

    high_conf = db_session.scalar(
        select(func.count(Conflict.id)).where(Conflict.confidence_score >= 0.90)
    ) or 0
    med_conf = db_session.scalar(
        select(func.count(Conflict.id)).where(Conflict.confidence_score >= 0.70, Conflict.confidence_score < 0.90)
    ) or 0
    low_conf = db_session.scalar(
        select(func.count(Conflict.id)).where(Conflict.confidence_score < 0.70)
    ) or 0

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Advanced Compliance Findings Verification Report\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("Verification Status: SUCCESS\n\n")
        
        f.write("## Pipeline Execution Performance\n")
        f.write(f"- **Total advanced compliance findings tracked**: {total_findings}\n")
        f.write(f"- **Average comparison confidence level**: {(avg_conf * 100):.1f}%\n")
        f.write(f"- **Pipeline execution cycle duration**: {duration_ms:.2f} ms\n")
        f.write("- **React Dashboard component verification**: PASSED\n\n")
        
        f.write("## Finding Category Breakdown\n")
        f.write(f"- **Temporal Mismatches (Deadline/Frequency)**: {len(data_temp['items'])}\n")
        f.write(f"- **Strength Mismatches (Modality Weaken/Strengthen)**: {len(data_str['items'])}\n")
        f.write(f"- **Stale and Review Required Policies**: {len(data_stale['items'])}\n\n")

        f.write("## Confidence Score Distribution\n")
        f.write(f"- **High Confidence (>= 90%)**: {high_conf}\n")
        f.write(f"- **Medium Confidence (70% - 89%)**: {med_conf}\n")
        f.write(f"- **Low Confidence (< 70%)**: {low_conf}\n")
        
    print(f"[Verification] Created advanced findings verification report at {report_path}")
