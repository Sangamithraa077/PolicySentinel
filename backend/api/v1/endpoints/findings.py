"""FastAPI endpoints for listing, filtering, and detail retrieval of advanced compliance findings."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from backend.api.dependencies.database import get_db
from backend.schemas.findings import FindingResponse, FindingListResponse
from backend.services.findings_management_service import FindingsManagementService

router = APIRouter()


def get_findings_service(db: Session = Depends(get_db)) -> FindingsManagementService:
    return FindingsManagementService(db)


@router.get(
    "",
    response_model=FindingListResponse,
    status_code=status.HTTP_200_OK,
    summary="List and filter advanced compliance findings"
)
def list_findings(
    policy_id: uuid.UUID | None = Query(None, description="Filter by policy ID involved in findings"),
    finding_type: str | None = Query(None, description="Filter by finding category (temporal, strength, stale)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: FindingsManagementService = Depends(get_findings_service)
):
    """Retrieves a paginated list of advanced findings filterable by type and policy search."""
    items, total = service.search_findings(
        policy_id=policy_id,
        finding_type=finding_type,
        limit=limit,
        offset=offset
    )
    return {
        "items": items,
        "total": total
    }


@router.get(
    "/temporal",
    response_model=FindingListResponse,
    status_code=status.HTTP_200_OK,
    summary="List temporal conflict findings"
)
def list_temporal_findings(
    policy_id: uuid.UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: FindingsManagementService = Depends(get_findings_service)
):
    """Retrieves only findings containing a time-based/temporal conflict."""
    items, total = service.search_findings(
        policy_id=policy_id,
        finding_type="temporal",
        limit=limit,
        offset=offset
    )
    return {
        "items": items,
        "total": total
    }


@router.get(
    "/strength",
    response_model=FindingListResponse,
    status_code=status.HTTP_200_OK,
    summary="List strength/modality conflict findings"
)
def list_strength_findings(
    policy_id: uuid.UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: FindingsManagementService = Depends(get_findings_service)
):
    """Retrieves only findings containing a modality strength conflict."""
    items, total = service.search_findings(
        policy_id=policy_id,
        finding_type="strength",
        limit=limit,
        offset=offset
    )
    return {
        "items": items,
        "total": total
    }


@router.get(
    "/stale",
    response_model=FindingListResponse,
    status_code=status.HTTP_200_OK,
    summary="List staleness and review required findings"
)
def list_stale_findings(
    policy_id: uuid.UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: FindingsManagementService = Depends(get_findings_service)
):
    """Retrieves policy versions classified as Outdated or Review Required."""
    items, total = service.search_findings(
        policy_id=policy_id,
        finding_type="stale",
        limit=limit,
        offset=offset
    )
    return {
        "items": items,
        "total": total
    }


@router.get(
    "/{finding_id}",
    response_model=FindingResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve finding details"
)
def get_finding(
    finding_id: uuid.UUID,
    service: FindingsManagementService = Depends(get_findings_service)
):
    """Retrieves full details of a specific compliance finding."""
    finding = service.get_finding_details(finding_id)
    if finding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding '{finding_id}' not found."
        )
    return finding
