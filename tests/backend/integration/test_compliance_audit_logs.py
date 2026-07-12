import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.company import Company
from backend.models.user import User
from backend.models.policy import Policy
from backend.models.policy_version import PolicyVersion
from backend.models.compliance_audit_log import ComplianceAuditLog
from backend.services.compliance_dashboard_service import record_compliance_audit_log, ComplianceDashboardService


def test_compliance_audit_logs_creation_and_query(db_session: Session, seeded_company_and_user):
    company, user = seeded_company_and_user
    company_id = company.id

    # 1. Record an audit log entry
    record_compliance_audit_log(
        db=db_session,
        company_id=company_id,
        event_type="Policy Upload",
        user_identifier="test_user@company.com",
        description="Uploaded test document v1"
    )
    db_session.commit()

    # 2. Query it via ComplianceDashboardService
    service = ComplianceDashboardService(db_session)
    items, total = service.list_audit_history(company_id=company_id, limit=10, offset=0)

    assert total > 0
    assert len(items) > 0
    
    # Verify properties
    entry = items[0]
    assert entry.company_id == company_id
    assert entry.event_type == "Policy Upload"
    assert entry.user_identifier == "test_user@company.com"
    assert entry.description == "Uploaded test document v1"
    assert entry.occurred_at is not None

    # Check Executive summary response structure
    summary = service.get_executive_summary(company_id=company_id)
    assert "total_policies" in summary
    assert "compliance_score" in summary
    assert "risk_level" in summary
