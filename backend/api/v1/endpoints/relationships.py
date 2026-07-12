"""FastAPI endpoints for listing, filtering, and detail retrieval of obligation relationship findings."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from backend.api.dependencies.database import get_db
from backend.schemas.relationships import RelationshipResponse, RelationshipListResponse
from backend.services.relationship_management_service import RelationshipManagementService

router = APIRouter()


def get_relationship_service(db: Session = Depends(get_db)) -> RelationshipManagementService:
    return RelationshipManagementService(db)


@router.get(
    "",
    response_model=RelationshipListResponse,
    status_code=status.HTTP_200_OK,
    summary="List and filter obligation relationships"
)
def list_relationships(
    policy_id: uuid.UUID | None = Query(None, description="Filter by policy ID involved in the relationship"),
    relationship_type: str | None = Query(None, description="Filter by relationship classification category (CONFLICT, REDUNDANT, COMPLEMENTARY, UNRELATED)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: RelationshipManagementService = Depends(get_relationship_service)
):
    """Retrieves a paginated list of relationship findings with policy search and type filtering."""
    items, total = service.search_relationships(
        policy_id=policy_id,
        relationship_type=relationship_type,
        limit=limit,
        offset=offset
    )
    return {
        "items": items,
        "total": total
    }


@router.get(
    "/{relationship_id}",
    response_model=RelationshipResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve relationship details"
)
def get_relationship(
    relationship_id: uuid.UUID,
    service: RelationshipManagementService = Depends(get_relationship_service)
):
    """Retrieves detailed attributes of a single obligation relationship finding."""
    relationship_record = service.get_relationship_details(relationship_id)
    if relationship_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship finding '{relationship_id}' not found."
        )
    return relationship_record
