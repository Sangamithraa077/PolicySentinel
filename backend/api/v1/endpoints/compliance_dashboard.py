"""FastAPI controller for executive metrics and paginated audit trail query retrieval."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.api.dependencies.database import get_db
from backend.schemas.compliance_dashboard import ExecutiveSummaryResponse, ComplianceAuditLogListResponse
from backend.services.compliance_dashboard_service import ComplianceDashboardService

router = APIRouter()


def get_dashboard_service(db: Session = Depends(get_db)) -> ComplianceDashboardService:
    return ComplianceDashboardService(db)


@router.get(
    "/summary",
    response_model=ExecutiveSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Executive compliance metrics and risk score"
)
def get_executive_summary(
    company_id: uuid.UUID = Query(..., description="The ID of the company to analyze"),
    service: ComplianceDashboardService = Depends(get_dashboard_service)
):
    """Calculates overall compliance score and aggregates totals across policies, clauses, and recommendations."""
    return service.get_executive_summary(company_id)


@router.get(
    "/audit-logs",
    response_model=ComplianceAuditLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve paginated compliance audit trail"
)
def list_compliance_audit_logs(
    company_id: uuid.UUID = Query(..., description="The ID of the company"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ComplianceDashboardService = Depends(get_dashboard_service)
):
    """Retrieves an immutable list of log history events corresponding to policy sentinel actions."""
    items, total = service.list_audit_history(company_id, limit, offset)
    return {
        "items": items,
        "total": total
    }
