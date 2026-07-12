import time
import uuid
import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, date

from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.regulatory_mapping import RegulatoryMapping
from backend.models.regulatory_framework import RegulatoryFramework
from backend.models.regulatory_clause import RegulatoryClause
from backend.models.conflict import Conflict
from backend.models.recommendation import Recommendation
from backend.models.enums import PolicyDocumentFileType

from backend.services.regulatory_knowledge_base_service import RegulatoryKnowledgeBaseService
from backend.services.policy_health_score_engine import PolicyHealthScoreEngine, DEFAULT_WEIGHTS
from backend.services.compliance_dashboard_service import ComplianceDashboardService


def test_policy_health_score_and_dashboard_verification(db_session: Session, seeded_company_and_user, client: TestClient) -> None:
    company, user = seeded_company_and_user
    company_id = company.id
    
    start_time = time.perf_counter()

    # 1. Seed frameworks
    kb_service = RegulatoryKnowledgeBaseService(db_session)
    kb_service.seed_default_frameworks()

    # 2. Setup internal policy with:
    # - 1 mapped obligation (logging)
    # - 1 unmapped obligation (no mapping records exist or matches NONE)
    # - 1 stale policy version (effective date > 365 days ago)
    # - 1 active high severity conflict
    # - 1 approved recommendation offsetting the conflict
    policy = Policy(company_id=company_id, title="Corporate Health Score Test Policy", status="active")
    db_session.add(policy)
    db_session.flush()

    ver = PolicyVersion(
        policy=policy,
        version_number=1,
        source_file_reference="uploads/policies/health_test.pdf",
        file_hash="hash-health",
        uploaded_by_user_id=user.id,
        status="published",
        original_filename="health_test.pdf",
        size_bytes=1024,
        file_type=PolicyDocumentFileType.PDF,
        extracted_text="Corporate standard logs audit logs. Non-critical activities should be ignored.",
        uploaded_at=datetime.utcnow() - timedelta(days=400) # Stale policy version
    )
    ver.effective_date = date.today() - timedelta(days=400)
    policy.current_version = ver
    db_session.add(ver)
    db_session.flush()

    cl_1 = Clause(policy_id=policy.id, policy_version_id=ver.id, clause_number="1.0", text="Corporate standard logs audit logs.", order_index=1)
    cl_2 = Clause(policy_id=policy.id, policy_version_id=ver.id, clause_number="2.0", text="Non-critical activities should be ignored.", order_index=2)
    db_session.add_all([cl_1, cl_2])
    db_session.flush()

    # Obligation 1 (mapped to logging)
    ob_1 = Obligation(
        clause_id=cl_1.id, policy_id=policy.id,
        subject="Corporate standard", action="logs", object="audit logs",
        modality="Must", compliance_category="Security", confidence_score=0.98, ai_model="mock"
    )
    # Obligation 2 (unmapped)
    ob_2 = Obligation(
        clause_id=cl_2.id, policy_id=policy.id,
        subject="Non-critical activities", action="ignored", object="audit team",
        modality="Should", compliance_category="Operations", confidence_score=0.90, ai_model="mock"
    )
    db_session.add_all([ob_1, ob_2])
    db_session.flush()

    # Store mapping for ob_1 (mapped to ISO 27001)
    mapping_1 = RegulatoryMapping(
        policy_id=policy.id,
        obligation_id=ob_1.id,
        framework_name="ISO 27001",
        regulation_id="A.12.4.1",
        clause_number="A.12.4.1",
        confidence_score=0.95,
        ai_explanation="Event logging control matched"
    )
    # Store NONE mapping for ob_2 (unmapped/missing)
    mapping_2 = RegulatoryMapping(
        policy_id=policy.id,
        obligation_id=ob_2.id,
        framework_name="NONE",
        regulation_id="NONE",
        clause_number="NONE",
        confidence_score=0.0,
        ai_explanation="No match found"
    )
    db_session.add_all([mapping_1, mapping_2])
    db_session.flush()

    # Add a high-severity conflict involving this policy
    conflict = Conflict(
        source_policy_id=policy.id,
        target_policy_id=policy.id,
        source_obligation_id=ob_1.id,
        target_obligation_id=ob_2.id,
        conflict_type="contradiction",
        similarity_score=0.85,
        severity="high",
        ai_explanation="Mock conflict",
        status="Open"
    )
    db_session.add(conflict)
    db_session.flush()

    # Add an approved recommendation linked to the conflict
    recommendation = Recommendation(
        conflict_id=conflict.id,
        recommendation_summary="Consolidate logging guidelines.",
        suggested_action="Keep standard audit log rules active.",
        original_clause="Corporate standard logs audit logs.",
        revised_clause="Corporate logs audit logs.",
        reason="Simplification of modality terms.",
        ai_model="mock",
        confidence_score=0.90,
        status="Approved",
        reviewer_name="Ava Thornton",
        reviewed_at=datetime.utcnow()
    )
    db_session.add(recommendation)
    db_session.commit()

    # 3. Calculate Policy Health Score
    health_engine = PolicyHealthScoreEngine(db_session)
    health_res = health_engine.calculate_health_score(policy.id)
    
    # Expected deductions:
    # Base: 100
    # Penalty conflict (high): -10
    # Penalty missing mapping (ob_2 mapping framework = NONE): -5
    # Penalty stale version (age > 365 days): -8
    # Bonus approved recommendation: +5
    # Total score: 100 - 10 - 5 - 8 + 5 = 82.0
    assert health_res.score == 82.0
    assert health_res.grade == "B"
    assert len(health_res.risk_factors) == 3

    # 4. Verify API responses
    # Query health score API
    res_health = client.get(f"/api/v1/regulatory-mappings/health/{policy.id}")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["score"] == 82.0
    assert data_health["grade"] == "B"
    assert len(data_health["risk_factors"]) == 3

    # Query mapping details
    res_mapping = client.get(f"/api/v1/regulatory-mappings/{mapping_1.id}")
    assert res_mapping.status_code == 200
    data_mapping = res_mapping.json()
    assert data_mapping["framework_name"] == "ISO 27001"

    # Query list with framework search filter
    res_fw = client.get("/api/v1/regulatory-mappings?framework_name=ISO%2027001")
    assert res_fw.status_code == 200
    data_fw = res_fw.json()
    assert data_fw["total"] > 0
    assert any(m["framework_name"] == "ISO 27001" for m in data_fw["items"])

    # Query list with policy search filter
    res_pol = client.get(f"/api/v1/regulatory-mappings?policy_id={policy.id}")
    assert res_pol.status_code == 200
    data_pol = res_pol.json()
    assert data_pol["total"] == 2

    # 5. Verify Executive Dashboard automatically updates
    dashboard_service = ComplianceDashboardService(db_session)
    summary = dashboard_service.get_executive_summary(company_id)
    assert "average_policy_health_score" in summary
    assert summary["average_policy_health_score"] == 82.0

    # Query dashboard summary endpoint
    res_summary = client.get(f"/api/v1/compliance-dashboard/summary?company_id={company_id}")
    assert res_summary.status_code == 200
    data_summary = res_summary.json()
    assert data_summary["average_policy_health_score"] == 82.0

    # 6. Verify Regulatory Compliance Dashboard rendering
    import pathlib
    dashboard_path = pathlib.Path("frontend/src/pages/RegulatoryDashboardPage.tsx")
    assert dashboard_path.exists(), "RegulatoryDashboardPage React component must exist."
    dashboard_content = dashboard_path.read_text(encoding="utf-8")
    assert "RegulatoryDashboardPage" in dashboard_content
    assert "Policy Health Score" in dashboard_content
    assert "Compliance Grade" in dashboard_content
    assert "Regulatory Coverage" in dashboard_content

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    # 7. Generate Verification Report
    import os
    artifact_dir = "C:/Users/Santhoshkumar/.gemini/antigravity-ide/brain/2ea7d0ac-c388-4d80-b068-182b034c1145"
    os.makedirs(artifact_dir, exist_ok=True)
    report_path = f"{artifact_dir}/health_score_verification_report.md"
    
    # Calculate mapping statistics from database
    total_mappings = db_session.scalar(
        select(func.count(RegulatoryMapping.id)).where(RegulatoryMapping.deleted_at.is_(None))
    ) or 0
    
    mapped_obligations = db_session.scalar(
        select(func.count(RegulatoryMapping.id)).where(
            RegulatoryMapping.framework_name != "NONE",
            RegulatoryMapping.deleted_at.is_(None)
        )
    ) or 0
    
    avg_mapping_conf = db_session.scalar(
        select(func.avg(RegulatoryMapping.confidence_score)).where(
            RegulatoryMapping.framework_name != "NONE",
            RegulatoryMapping.deleted_at.is_(None)
        )
    ) or 0.0

    # Fetch framework distributions
    iso_cnt = db_session.scalar(select(func.count(RegulatoryMapping.id)).where(RegulatoryMapping.framework_name == "ISO 27001")) or 0
    gdpr_cnt = db_session.scalar(select(func.count(RegulatoryMapping.id)).where(RegulatoryMapping.framework_name == "GDPR")) or 0
    rbi_cnt = db_session.scalar(select(func.count(RegulatoryMapping.id)).where(RegulatoryMapping.framework_name == "RBI")) or 0
    sebi_cnt = db_session.scalar(select(func.count(RegulatoryMapping.id)).where(RegulatoryMapping.framework_name == "SEBI")) or 0

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Policy Health Score & Regulatory Mapping Verification Report\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("Verification Status: SUCCESS\n\n")
        
        f.write("## Regulatory Mapping Statistics\n")
        f.write(f"- **Total Mapped Obligations**: {mapped_obligations}\n")
        f.write(f"- **Average Mapping Confidence**: {avg_mapping_conf * 100:.1f}%\n")
        f.write(f"- **Regulatory Coverage**: {(mapped_obligations / total_mappings * 100) if total_mappings else 100.0:.1f}%\n\n")

        f.write("## Framework Distribution\n")
        f.write(f"- **ISO 27001 Mappings**: {iso_cnt}\n")
        f.write(f"- **GDPR Mappings**: {gdpr_cnt}\n")
        f.write(f"- **RBI Mappings**: {rbi_cnt}\n")
        f.write(f"- **SEBI Mappings**: {sebi_cnt}\n\n")

        f.write("## Policy Health Score Performance\n")
        f.write(f"- **Calculated Policy Health Score**: {health_res.score:.1f}/100.0\n")
        f.write(f"- **Compliance Grade**: {health_res.grade}\n")
        f.write(f"- **Health Summary**: {health_res.summary}\n\n")

        f.write("## Top Compliance Risk Factors\n")
        for factor in health_res.risk_factors:
            f.write(f"  - {factor}\n")
        
        f.write("\n## Executive Dashboard & UI Integrations\n")
        f.write("- **AI mapping database storage verification**: PASSED\n")
        f.write("- **API endpoint validation**: PASSED\n")
        f.write("- **Dashboard rendering components verification**: PASSED\n")
        f.write(f"- **Auto-updated Executive Dashboard Health Summary**: {data_summary['average_policy_health_score']:.1f}\n")
        f.write(f"- **Verification execution time**: {duration_ms:.2f} ms\n")
        
    print(f"[Verification] Created health score verification report at {report_path}")
