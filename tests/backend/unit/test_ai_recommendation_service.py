"""Unit tests for the AIRecommendationService and AIRedlineGenerator."""

from __future__ import annotations

import pytest
from backend.models.obligation import Obligation
from backend.services.ai.ai_recommendation_service import AIRecommendationService, RecommendationAIResult, RedlineAIResult


def test_mock_recommendation_generation() -> None:
    service = AIRecommendationService()
    
    ob_a = Obligation(
        subject="Staff",
        action="attend training",
        object="security training",
        modality="Must",
        compliance_category="Security"
    )
    ob_b = Obligation(
        subject="Staff",
        action="attend training",
        object="security training",
        modality="May",
        compliance_category="Security"
    )

    # 1. Contradiction Type
    rec_contra = service.generate_recommendation(
        conflict_type="contradiction",
        severity="high",
        source_ob=ob_a,
        target_ob=ob_b
    )
    assert isinstance(rec_contra, RecommendationAIResult)
    assert len(rec_contra.conflict_summary) > 0
    assert len(rec_contra.suggested_action) > 0

    # 2. Duplicate Type
    rec_dup = service.generate_recommendation(
        conflict_type="duplicate",
        severity="low",
        source_ob=ob_a,
        target_ob=ob_a
    )
    assert len(rec_dup.conflict_summary) > 0
    assert len(rec_dup.suggested_action) > 0


def test_mock_redline_generation() -> None:
    service = AIRecommendationService()
    
    source_text = "Staff must attend training."
    target_text = "Staff should attend training."

    # Contradiction Redline
    redline = service.generate_redline(
        source_clause_text=source_text,
        target_clause_text=target_text,
        recommendation_summary="Modality mismatch: Must contradicts should.",
        suggested_action="Align modalities"
    )

    assert isinstance(redline, RedlineAIResult)
    assert redline.original_clause == target_text
    assert "must" in redline.revised_clause.lower()
    assert len(redline.reason_for_change) > 0
