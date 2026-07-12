"""Pydantic schemas for Recommendation API resources."""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    conflict_id: uuid.UUID
    recommendation_summary: str
    suggested_action: str
    original_clause: str | None = None
    revised_clause: str | None = None
    reason: str
    ai_model: str
    confidence_score: float
    status: str
    created_at: datetime
    
    # Review fields
    reviewer_name: str | None = None
    reviewed_at: datetime | None = None
    review_comments: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RecommendationListResponse(BaseModel):
    items: list[RecommendationResponse]
    total: int


class UpdateRecommendationStatusRequest(BaseModel):
    status: str = Field(..., description="Accepted or Rejected status of the recommendation")
    reviewer_name: str | None = Field(None, description="Name of the compliance officer reviewing this item")
    review_comments: str | None = Field(None, description="Comments/notes regarding the decision")
