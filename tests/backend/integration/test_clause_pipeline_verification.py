"""Verification test for the complete clause segmentation pipeline.

Simulates uploading a structured PDF, runs text extraction and clause
segmentation, stores clauses in the database, and validates retrieval via API.
"""

from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.backend.unit.test_pdf_text_extractor import make_large_pdf

pytestmark = pytest.mark.api_response


def test_complete_clause_pipeline_verification(client: TestClient, seeded_company_and_user) -> None:
    company, user = seeded_company_and_user

    # 1. Create a structured PDF document representing a real policy outline
    pdf_bytes = make_large_pdf(
        "1. Purpose and Policy Statement",
        "This policy defines the security boundaries.",
        "1.1 Scope and Enforcement",
        "This applies to all staff members.",
        "1.1.1 Exceptions",
        "Exceptions must be approved by the CISO.",
        "(a) First Exception Rule",
        "First exception description text.",
        "- Special Bullet point exceptions"
    )

    # 2. Trigger the automated upload pipeline
    upload_data = {
        "company_id": str(company.id),
        "uploaded_by_user_id": str(user.id),
        "policy_title": "Pipeline Verification Security Policy",
        "version_number": "1",
    }
    files = {"file": ("verification_policy.pdf", pdf_bytes, "application/pdf")}
    
    upload_response = client.post("/api/v1/uploads/policies", data=upload_data, files=files)
    assert upload_response.status_code == 201
    policy_id = upload_response.json()["policy_id"]

    # 3. Retrieve the segmented clauses via the Clause API
    clauses_response = client.get("/api/v1/clauses", params={"policy_id": policy_id})
    assert clauses_response.status_code == 200
    
    body = clauses_response.json()
    clauses = body["items"]
    
    # 4. Verify extraction count and ordering
    # Expected structure:
    # 0. HEADING: 1. Purpose and Policy Statement (level 1)
    #    Text: This policy defines the security boundaries.
    # 1. SUBHEADING: 1.1 Scope and Enforcement (level 2)
    #    Text: This applies to all staff members.
    # 2. SUBHEADING: 1.1.1 Exceptions (level 3)
    #    Text: Exceptions must be approved by the CISO.
    # 3. NUMBERED_LIST_ITEM: (a) First Exception Rule (level 4)
    #    Text: First exception description text.
    # 4. BULLET_POINT: Special Bullet point exceptions (level 5)
    
    assert len(clauses) == 5, f"Expected 5 clauses, got {len(clauses)}"
    
    # Assert Order index and values
    for idx, c in enumerate(clauses):
        assert c["order_index"] == idx
        assert c["policy_id"] == policy_id
        
    # Assert Hierarchy Fields
    assert clauses[0]["clause_number"] == "1"
    assert clauses[0]["heading"] == "Purpose and Policy Statement"
    assert clauses[0]["text"] == "Purpose and Policy Statement\n\nThis policy defines the security boundaries."

    assert clauses[1]["clause_number"] == "1.1"
    assert clauses[1]["heading"] == "Scope and Enforcement"
    assert clauses[1]["text"] == "Scope and Enforcement\n\nThis applies to all staff members."

    assert clauses[2]["clause_number"] == "1.1.1"
    assert clauses[2]["heading"] == "Exceptions"
    assert clauses[2]["text"] == "Exceptions\n\nExceptions must be approved by the CISO."

    assert clauses[3]["clause_number"] == "(a)"
    assert clauses[3]["text"] == "First Exception Rule\n\nFirst exception description text."

    assert clauses[4]["clause_number"] is None
    assert clauses[4]["text"] == "Special Bullet point exceptions"

    # Assert Parent Links match outline nesting
    # 1.1 (clauses[1]) parent is 1 (clauses[0])
    assert clauses[1]["parent_clause_id"] == clauses[0]["id"]
    # 1.1.1 (clauses[2]) parent is 1.1 (clauses[1])
    assert clauses[2]["parent_clause_id"] == clauses[1]["id"]
    # (a) list item (clauses[3]) parent is 1.1.1 (clauses[2])
    assert clauses[3]["parent_clause_id"] == clauses[2]["id"]
    # bullet point (clauses[4]) parent is (a) list item (clauses[3])
    assert clauses[4]["parent_clause_id"] == clauses[3]["id"]
    
    # 5. Retrieve the extracted obligations via the Obligation API
    obligations_response = client.get("/api/v1/obligations", params={"policy_id": policy_id})
    assert obligations_response.status_code == 200
    
    obligations_body = obligations_response.json()
    obligations = obligations_body["items"]
    assert len(obligations) > 0, "No obligations were extracted"
    
    # Save a JSON file with test output for reporting
    report_data = {
        "success": True,
        "policy_id": policy_id,
        "clauses_count": len(clauses),
        "obligations_count": len(obligations),
        "samples": [
            {
                "number": c["clause_number"],
                "heading": c["heading"],
                "text": c["text"],
                "order_index": c["order_index"]
            }
            for c in clauses
        ],
        "obligations": [
            {
                "subject": o["subject"],
                "action": o["action"],
                "object": o["object"],
                "modality": o["modality"],
                "compliance_category": o["compliance_category"],
                "confidence_score": o["confidence_score"]
            }
            for o in obligations
        ]
    }
    print(f"PIPELINE_VERIFICATION_REPORT:{json.dumps(report_data)}")
