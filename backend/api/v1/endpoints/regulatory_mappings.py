"""FastAPI endpoints for querying and triggering AI regulatory mappings against the Regulatory Knowledge Base."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import uuid

from backend.api.dependencies.database import get_db
from backend.models.regulatory_mapping import RegulatoryMapping
from backend.models.regulatory_framework import RegulatoryFramework
from backend.models.regulatory_clause import RegulatoryClause
from backend.models.obligation import Obligation
from backend.schemas.regulatory_mapping import (
    RegulatoryMappingResponse,
    RegulatoryMappingListResponse,
    RegulatoryFrameworkResponse,
    RegulatoryFrameworkClauseResponse,
    PolicyHealthScoreResponse
)
from backend.services.ai.regulatory_mapping_service import AIRegulatoryMappingService
from backend.services.regulatory_knowledge_base_service import RegulatoryKnowledgeBaseService

router = APIRouter()


@router.get(
    "",
    response_model=RegulatoryMappingListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all AI regulatory mappings"
)
def list_regulatory_mappings(
    policy_id: uuid.UUID | None = Query(None),
    framework_name: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Retrieves all stored AI obligations-to-regulations mappings."""
    conditions = [RegulatoryMapping.deleted_at.is_(None)]
    if policy_id:
        conditions.append(RegulatoryMapping.policy_id == policy_id)
    if framework_name:
        conditions.append(RegulatoryMapping.framework_name == framework_name)

    query = select(RegulatoryMapping).where(*conditions)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(RegulatoryMapping.created_at.desc()).limit(limit).offset(offset)).all()

    return {
        "items": items,
        "total": total
    }


@router.get(
    "/obligation/{obligation_id}",
    response_model=list[RegulatoryMappingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get regulatory mappings for an obligation"
)
def get_mappings_for_obligation(
    obligation_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Retrieves all regulatory mappings matching a single obligation ID."""
    mappings = db.scalars(
        select(RegulatoryMapping)
        .where(RegulatoryMapping.obligation_id == obligation_id, RegulatoryMapping.deleted_at.is_(None))
    ).all()
    return mappings


@router.post(
    "/remap/{obligation_id}",
    response_model=RegulatoryMappingResponse,
    status_code=status.HTTP_200_OK,
    summary="Manually trigger AI regulatory mapping for an obligation"
)
def remap_obligation(
    obligation_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Manually re-runs AI regulatory mapping for the specified obligation and commits updates."""
    obligation = db.scalar(
        select(Obligation).where(Obligation.id == obligation_id, Obligation.deleted_at.is_(None))
    )
    if not obligation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Obligation with ID '{obligation_id}' not found."
        )

    mapping_service = AIRegulatoryMappingService(db)
    mapping_res = mapping_service.map_obligation(obligation)

    # Fetch Regulation ID
    regulation_id = "NONE"
    if mapping_res.framework_name != "NONE":
        reg_clause = db.scalar(
            select(RegulatoryClause)
            .join(RegulatoryFramework)
            .where(
                RegulatoryFramework.name == mapping_res.framework_name,
                RegulatoryClause.clause_reference == mapping_res.clause_number,
                RegulatoryClause.deleted_at.is_(None),
                RegulatoryFramework.deleted_at.is_(None)
            )
        )
        if reg_clause:
            regulation_id = reg_clause.clause_reference

    # Check if a mapping record already exists for this obligation
    existing_mapping = db.scalar(
        select(RegulatoryMapping)
        .where(RegulatoryMapping.obligation_id == obligation_id, RegulatoryMapping.deleted_at.is_(None))
    )

    if existing_mapping:
        existing_mapping.framework_name = mapping_res.framework_name
        existing_mapping.regulation_id = regulation_id
        existing_mapping.clause_number = mapping_res.clause_number
        existing_mapping.confidence_score = mapping_res.confidence_score
        existing_mapping.ai_explanation = mapping_res.explanation
        db.flush()
        reg_mapping = existing_mapping
    else:
        reg_mapping = RegulatoryMapping(
            policy_id=obligation.policy_id,
            obligation_id=obligation.id,
            framework_name=mapping_res.framework_name,
            regulation_id=regulation_id,
            clause_number=mapping_res.clause_number,
            confidence_score=mapping_res.confidence_score,
            ai_explanation=mapping_res.explanation
        )
        db.add(reg_mapping)
        db.flush()

    db.commit()
    return reg_mapping


@router.get(
    "/frameworks",
    response_model=list[RegulatoryFrameworkResponse],
    status_code=status.HTTP_200_OK,
    summary="List all regulatory frameworks"
)
def list_regulatory_frameworks(
    db: Session = Depends(get_db)
):
    """Retrieves all registered regulatory frameworks inside the knowledge base."""
    kb_service = RegulatoryKnowledgeBaseService(db)
    kb_service.seed_default_frameworks()
    frameworks = kb_service.list_frameworks()
    return frameworks


@router.get(
    "/frameworks/{framework_id}/clauses",
    response_model=list[RegulatoryFrameworkClauseResponse],
    status_code=status.HTTP_200_OK,
    summary="List clauses for a regulatory framework"
)
def list_framework_clauses(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Retrieves all clauses mapped to a single regulatory framework ID."""
    kb_service = RegulatoryKnowledgeBaseService(db)
    clauses = kb_service.list_clauses(framework_id=framework_id)
    return clauses


@router.get(
    "/health/{policy_id}",
    response_model=PolicyHealthScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Policy Health Score"
)
def get_policy_health(
    policy_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Calculates and returns the Policy Health Score for the specified policy."""
    from backend.services.policy_health_score_engine import PolicyHealthScoreEngine
    engine = PolicyHealthScoreEngine(db)
    health_res = engine.calculate_health_score(policy_id)
    return health_res.to_dict()


@router.get(
    "/{mapping_id}",
    response_model=RegulatoryMappingResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve regulatory mapping details"
)
def get_regulatory_mapping(
    mapping_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Retrieves details of a specific regulatory mapping by ID."""
    mapping = db.scalar(
        select(RegulatoryMapping)
        .where(RegulatoryMapping.id == mapping_id, RegulatoryMapping.deleted_at.is_(None))
    )
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Regulatory mapping '{mapping_id}' not found."
        )
    return mapping
