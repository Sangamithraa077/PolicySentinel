import uuid
import pytest
from fastapi.testclient import TestClient


def test_compliance_dashboard_endpoints(client: TestClient, db_session, seeded_company_and_user):
    company, user = seeded_company_and_user
    company_id = company.id

    # 1. Fetch Executive summary summary endpoint
    response = client.get(f"/api/v1/compliance-dashboard/summary?company_id={company_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_policies" in data
    assert "total_clauses" in data
    assert "total_obligations" in data
    assert "compliance_score" in data
    assert "risk_level" in data
    assert "risk_summary" in data

    # 2. Fetch Compliance audit logs endpoint
    response_logs = client.get(f"/api/v1/compliance-dashboard/audit-logs?company_id={company_id}")
    assert response_logs.status_code == 200
    
    logs_data = response_logs.json()
    assert "items" in logs_data
    assert "total" in logs_data
    assert isinstance(logs_data["items"], list)
