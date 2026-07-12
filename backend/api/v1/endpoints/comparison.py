"""FastAPI router for policy comparison and conflict detection endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies.database import get_db
from backend.schemas.comparison import CompareRequest, CompareResponse
from backend.services.comparison.semantic_comparison_service import SemanticComparisonService
from backend.services.comparison.conflict_detection_engine import ConflictDetectionEngine

router = APIRouter()


@router.post(
    "/compare",
    response_model=CompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare two policy versions semantically and detect conflicts"
)
def compare_policy_versions(
    payload: CompareRequest,
    db: Session = Depends(get_db)
):
    """Semantically compares all obligations between two policy versions
    and runs conflict analysis rules to detect duplicates, contradictions, and gaps.
    """
    from backend.models.policy_version import PolicyVersion
    
    version_a = db.get(PolicyVersion, payload.version_a_id)
    if version_a is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy version A '{payload.version_a_id}' not found."
        )
        
    version_b = db.get(PolicyVersion, payload.version_b_id)
    if version_b is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy version B '{payload.version_b_id}' not found."
        )

    # Instantiate services
    comp_service = SemanticComparisonService(db)
    conflict_engine = ConflictDetectionEngine(db)

    # 1. Perform pairwise semantic comparisons
    comparisons = comp_service.compare_versions(payload.version_a_id, payload.version_b_id)

    # 2. Feed comparisons to detection engine
    conflicts = conflict_engine.detect_conflicts(payload.version_a_id, payload.version_b_id, comparisons)

    # Format pairwise results for validation schema
    formatted_comparisons = [
        {
            "obligation_a_id": item["obligation_a"].id,
            "obligation_b_id": item["obligation_b"].id,
            "similarity_score": item["similarity_score"],
            "category": item["category"]
        }
        for item in comparisons
    ]

    return {
        "version_a_id": payload.version_a_id,
        "version_b_id": payload.version_b_id,
        "comparisons": formatted_comparisons,
        "conflicts": conflicts
    }
