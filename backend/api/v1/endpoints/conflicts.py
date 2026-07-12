"""FastAPI endpoints for listing, details, and status updates of compliance conflicts."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid
from pydantic import BaseModel, Field

from backend.api.dependencies.database import get_db
from backend.schemas.conflicts import ConflictResponse, ConflictListResponse
from backend.services.conflict_management_service import ConflictManagementService

router = APIRouter()


class UpdateStatusRequest(BaseModel):
    status: str = Field(..., description="Status of the conflict (Open, Reviewed, Resolved)")


def get_conflict_service(db: Session = Depends(get_db)) -> ConflictManagementService:
    return ConflictManagementService(db)


@router.get(
    "",
    response_model=ConflictListResponse,
    status_code=status.HTTP_200_OK,
    summary="List and search compliance conflicts"
)
def list_conflicts(
    policy_id: uuid.UUID | None = Query(None, description="Filter by either source or target policy ID"),
    severity: str | None = Query(None, description="Filter by severity level (low, medium, high)"),
    conflict_type: str | None = Query(None, description="Filter by conflict type (duplicate, contradiction, missing)"),
    status: str | None = Query(None, description="Filter by status (Open, Reviewed, Resolved)"),
    search: str | None = Query(None, description="Search keyword in explanations or obligation details"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ConflictManagementService = Depends(get_conflict_service)
):
    """Retrieves a paginated list of compliance conflicts with filtering and search capabilities."""
    items, total = service.search_conflicts(
        policy_id=policy_id,
        severity=severity,
        conflict_type=conflict_type,
        status=status,
        search=search,
        limit=limit,
        offset=offset
    )
    return {
        "items": items,
        "total": total
    }


@router.get(
    "/{conflict_id}",
    response_model=ConflictResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve conflict details"
)
def get_conflict(
    conflict_id: uuid.UUID,
    service: ConflictManagementService = Depends(get_conflict_service)
):
    """Retrieves full details of a specific conflict record."""
    conflict = service.get_conflict_details(conflict_id)
    if conflict is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict '{conflict_id}' not found."
        )
    return conflict


@router.patch(
    "/{conflict_id}/status",
    response_model=ConflictResponse,
    status_code=status.HTTP_200_OK,
    summary="Update conflict status"
)
def update_conflict_status(
    conflict_id: uuid.UUID,
    payload: UpdateStatusRequest,
    service: ConflictManagementService = Depends(get_conflict_service)
):
    """Updates the status of a conflict record (e.g. Open, Reviewed, Resolved)."""
    try:
        conflict = service.update_conflict_status(conflict_id, payload.status)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

    if conflict is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict '{conflict_id}' not found."
        )
    return conflict
