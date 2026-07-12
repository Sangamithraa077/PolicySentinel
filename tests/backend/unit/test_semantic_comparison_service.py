"""Unit tests for the SemanticComparisonService."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from backend.config.settings import Settings
from backend.services.comparison.semantic_comparison_service import (
    SemanticComparisonService,
    compute_cosine_similarity,
    _generate_mock_vector
)


def test_cosine_similarity_edge_cases() -> None:
    # Identical vectors
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert compute_cosine_similarity(v1, v2) == pytest.approx(1.0)

    # Orthogonal vectors
    v3 = [0.0, 1.0, 0.0]
    assert compute_cosine_similarity(v1, v3) == pytest.approx(0.0)

    # Empty vectors
    assert compute_cosine_similarity([], []) == pytest.approx(0.0)

    # Mismatched dimension length
    assert compute_cosine_similarity([1.0], [1.0, 2.0]) == pytest.approx(0.0)


def test_mock_vector_generation() -> None:
    # Deterministic output
    vec_1 = _generate_mock_vector("Test obligation text")
    vec_2 = _generate_mock_vector("Test obligation text")
    assert vec_1 == vec_2
    assert len(vec_1) == 768

    # Vectors for different texts should not be identical
    vec_3 = _generate_mock_vector("Different text here")
    assert vec_1 != vec_3


def test_semantic_comparison_service_mock_embedding(db_session: Session) -> None:
    # Initialize service with settings where GEMINI_API_KEY is not configured
    settings = Settings(GEMINI_API_KEY="changeme")
    service = SemanticComparisonService(db_session, settings=settings)

    # Calling get_embedding should produce the fallback mock vector
    vec = service.get_embedding("Verify mock embedding generator")
    assert len(vec) == 768
    assert vec == _generate_mock_vector("Verify mock embedding generator")


def test_semantic_comparison_service_live_mock_client(db_session: Session) -> None:
    # Simulate a configured Gemini Client returning expected response structure
    settings = Settings(GEMINI_API_KEY="valid_key")
    service = SemanticComparisonService(db_session, settings=settings)

    mock_client = MagicMock()
    mock_embedding_values = [0.1] * 768
    
    mock_response = MagicMock()
    mock_response.embeddings = [MagicMock(values=mock_embedding_values)]
    mock_client.models.embed_content.return_value = mock_response
    service._client = mock_client

    vec = service.get_embedding("Query embedded text")
    assert vec == mock_embedding_values
    mock_client.models.embed_content.assert_called_once_with(
        model="text-embedding-004",
        contents="Query embedded text"
    )
