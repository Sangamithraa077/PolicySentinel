import time
import uuid
import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from datetime import datetime

from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.clause import Clause
from backend.models.obligation import Obligation
from backend.models.regulatory_mapping import RegulatoryMapping
from backend.models.regulatory_framework import RegulatoryFramework
from backend.models.regulatory_clause import RegulatoryClause
from backend.models.enums import PolicyDocumentFileType

from backend.services.regulatory_knowledge_base_service import RegulatoryKnowledgeBaseService
from backend.services.ai.regulatory_mapping_service import AIRegulatoryMappingService


def test_regulatory_knowledge_base_and_ai_mapping_verification(db_session: Session, seeded_company_and_user, client: TestClient) -> None:
    company, user = seeded_company_and_user
    company_id = company.id
    
    start_time = time.perf_counter()

    # 1. Verify Regulatory Knowledge Base seeding
    kb_service = RegulatoryKnowledgeBaseService(db_session)
    kb_service.seed_default_frameworks()
    
    # Assert frameworks are seeded
    frameworks = kb_service.list_frameworks()
    framework_names = {fw.name for fw in frameworks}
    assert "GDPR" in framework_names
    assert "ISO 27001" in framework_names
    assert "RBI" in framework_names
    assert "SEBI" in framework_names
    
    # Assert ISO 27001 clauses are present
    iso_fw = next(fw for fw in frameworks if fw.name == "ISO 27001")
    clauses = kb_service.list_clauses(iso_fw.id)
    clause_refs = {cl.clause_reference for cl in clauses}
    assert "A.12.4.1" in clause_refs

    # 2. Setup mock internal Policy & Obligation to trigger mapping
    policy = Policy(company_id=company_id, title="IT Security and Event Logging Policy", status="active")
    db_session.add(policy)
    db_session.flush()

    ver = PolicyVersion(
        policy=policy,
        version_number=1,
        source_file_reference="uploads/policies/sec_policy.pdf",
        file_hash="hash-sec",
        uploaded_by_user_id=user.id,
        status="published",
        original_filename="sec_policy.pdf",
        size_bytes=4096,
        file_type=PolicyDocumentFileType.PDF,
        extracted_text="The IT operations division shall establish system logging controls to log all audit activities.",
        uploaded_at=datetime.utcnow()
    )
    policy.current_version = ver
    db_session.add(ver)
    db_session.flush()

    cl = Clause(policy_id=policy.id, policy_version_id=ver.id, clause_number="5.2", text="The IT operations division shall establish system logging controls to log all audit activities.", order_index=1)
    db_session.add(cl)
    db_session.flush()

    ob = Obligation(
        clause_id=cl.id, policy_id=policy.id,
        subject="IT operations division", action="establish system logging controls", object="audit activities",
        modality="Shall", compliance_category="Security", confidence_score=0.99, ai_model="mock"
    )
    db_session.add(ob)
    db_session.commit()

    # 3. Test AIRegulatoryMappingService
    mapping_service = AIRegulatoryMappingService(db_session)
    mapping_res = mapping_service.map_obligation(ob)
    
    assert mapping_res.framework_name == "ISO 27001"
    assert mapping_res.clause_number == "A.12.4.1"
    assert mapping_res.confidence_score > 0.0
    assert "logging" in mapping_res.explanation.lower()

    # 4. Store mapping and verify DB persistence
    reg_mapping = RegulatoryMapping(
        policy_id=ob.policy_id,
        obligation_id=ob.id,
        framework_name=mapping_res.framework_name,
        regulation_id="A.12.4.1",
        clause_number=mapping_res.clause_number,
        confidence_score=mapping_res.confidence_score,
        ai_explanation=mapping_res.explanation
    )
    db_session.add(reg_mapping)
    db_session.commit()

    # Fetch stored mapping from database
    stored_mapping = db_session.scalar(
        select(RegulatoryMapping).where(RegulatoryMapping.obligation_id == ob.id)
    )
    assert stored_mapping is not None
    assert stored_mapping.framework_name == "ISO 27001"
    assert stored_mapping.clause_number == "A.12.4.1"

    # 5. Verify API responses
    # Query mappings list
    res_list = client.get("/api/v1/regulatory-mappings")
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert data_list["total"] > 0
    assert any(m["framework_name"] == "ISO 27001" for m in data_list["items"])

    # Query mapping for specific obligation
    res_ob = client.get(f"/api/v1/regulatory-mappings/obligation/{ob.id}")
    assert res_ob.status_code == 200
    data_ob = res_ob.json()
    assert len(data_ob) > 0
    assert data_ob[0]["framework_name"] == "ISO 27001"

    # Manual remap trigger API
    res_remap = client.post(f"/api/v1/regulatory-mappings/remap/{ob.id}")
    assert res_remap.status_code == 200
    data_remap = res_remap.json()
    assert data_remap["framework_name"] == "ISO 27001"

    # Query frameworks knowledge base
    res_fws = client.get("/api/v1/regulatory-mappings/frameworks")
    assert res_fws.status_code == 200
    data_fws = res_fws.json()
    assert len(data_fws) >= 4
    
    # Query clauses for specific framework
    res_cls = client.get(f"/api/v1/regulatory-mappings/frameworks/{iso_fw.id}/clauses")
    assert res_cls.status_code == 200
    data_cls = res_cls.json()
    assert len(data_cls) > 0

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    # 6. Generate Verification Report Markdown
    import os
    artifact_dir = (__import__("os").environ.get("ANTIGRAVITY_ARTIFACT_DIR") or str(__import__("pathlib").Path(__import__("os").environ.get("USERPROFILE") or __import__("os").environ.get("HOME", "")) / ".gemini" / "antigravity" / "brain" / __import__("os").environ.get("ANTIGRAVITY_CONVERSATION_ID", "")))
    os.makedirs(artifact_dir, exist_ok=True)
    report_path = f"{artifact_dir}/regulatory_mappings_verification_report.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# AI Regulatory Mapping & Knowledge Base Verification Report\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("Verification Status: SUCCESS\n\n")
        
        f.write("## Regulatory Knowledge Base Inventory\n")
        f.write(f"- **Total Frameworks registered**: {len(frameworks)}\n")
        for fw in frameworks:
            f.write(f"  - **{fw.name}** ({fw.jurisdiction}): {fw.description}\n")
        
        f.write("\n## AI Mapping Execution Metrics\n")
        f.write(f"- **Mapping test outcomes**: PASSED\n")
        f.write(f"- **Match target output**: ISO 27001 Control A.12.4.1 (Event logging)\n")
        f.write(f"- **Mapping Confidence**: {mapping_res.confidence_score * 100:.1f}%\n")
        f.write(f"- **API response validations**: ALL PASSED\n")
        f.write(f"- **Execution time**: {duration_ms:.2f} ms\n")
        
    print(f"[Verification] Created regulatory mappings verification report at {report_path}")
