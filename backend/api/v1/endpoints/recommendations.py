"""FastAPI endpoints for listing, detail queries, and status actions on AI compliance recommendations."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from backend.api.dependencies.database import get_db
from backend.schemas.recommendations import RecommendationResponse, RecommendationListResponse, UpdateRecommendationStatusRequest
from backend.services.recommendation_management_service import RecommendationManagementService

router = APIRouter()


def get_recommendation_service(db: Session = Depends(get_db)) -> RecommendationManagementService:
    return RecommendationManagementService(db)


@router.get(
    "",
    response_model=RecommendationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List and filter AI recommendations"
)
def list_recommendations(
    status: str | None = Query(None, description="Filter by status (Pending, Accepted, Rejected)"),
    confidence_score: float | None = Query(None, description="Filter by minimum confidence score"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: RecommendationManagementService = Depends(get_recommendation_service)
):
    """Retrieves a paginated list of AI compliance recommendations with status and confidence filters."""
    items, total = service.search_recommendations(
        status=status,
        confidence_score=confidence_score,
        limit=limit,
        offset=offset
    )
    return {
        "items": items,
        "total": total
    }


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve recommendation details"
)
def get_recommendation(
    recommendation_id: uuid.UUID,
    service: RecommendationManagementService = Depends(get_recommendation_service)
):
    """Retrieves detailed attributes for a single compliance recommendation."""
    recommendation = service.get_recommendation_details(recommendation_id)
    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found."
        )
    return recommendation


@router.patch(
    "/{recommendation_id}/status",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update recommendation status (Accept/Reject)"
)
def update_recommendation_status(
    recommendation_id: uuid.UUID,
    payload: UpdateRecommendationStatusRequest,
    service: RecommendationManagementService = Depends(get_recommendation_service)
):
    """Updates the status of a recommendation (Accepted, Rejected, Pending)."""
    try:
        recommendation = service.update_recommendation_status(recommendation_id, payload.status)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found."
        )
    return recommendation
