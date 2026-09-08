"""Unit tests for ObligationExtractorService."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from backend.services.ai.obligation_extractor_service import ObligationExtractorService, ObligationExtractionResult
from backend.config.settings import Settings


def test_extract_obligation_empty_input() -> None:
    service = ObligationExtractorService()
    with pytest.raises(ValueError, match="Clause text cannot be empty"):
        service.extract_obligation("")


def test_extract_obligation_mock_fallback_ciso() -> None:
    settings = Settings(GEMINI_API_KEY="changeme")
    service = ObligationExtractorService(settings=settings)
    
    result = service.extract_obligation("Exceptions must be approved by the CISO.")
    
    assert isinstance(result, ObligationExtractionResult)
    assert result.subject == "CISO"
    assert result.action == "comply with standard guidelines"
    assert result.object == "policy requirements"
    assert result.modality == "Must"
    assert result.compliance_category == "Operational Governance"
    assert 0.7 <= result.confidence_score <= 1.0


def test_extract_obligation_mock_fallback_access() -> None:
    settings = Settings(GEMINI_API_KEY="changeme")
    service = ObligationExtractorService(settings=settings)
    
    result = service.extract_obligation("Users shall authenticate securely before accessing passwords.")
    
    assert isinstance(result, ObligationExtractionResult)
    assert result.subject == "Authorized Users"
    assert result.action == "enforce multi-factor authentication"
    assert result.object == "network infrastructure and credential access"
    assert result.modality == "Shall"
    assert result.compliance_category == "Access Control"


def test_extract_obligation_with_mocked_gemini_client() -> None:
    settings = Settings(GEMINI_API_KEY="fake-valid-key")
    
    with patch("google.genai.Client") as MockClient:
        mock_client_instance = MockClient.return_value
        mock_response = MagicMock()
        mock_response.text = (
            '{"subject": "Staff", "action": "report breach", "object": "incident report", '
            '"modality": "Must", "conditions": "Immediately", "time_constraints": "24 hours", '
            '"compliance_category": "Data Protection", "confidence_score": 0.99}'
        )
        mock_client_instance.models.generate_content.return_value = mock_response
        
        service = ObligationExtractorService(settings=settings)
        service._client = mock_client_instance
        
        result = service.extract_obligation("Staff must report breaches immediately within 24 hours.")
        
        assert isinstance(result, ObligationExtractionResult)
        assert result.subject == "Staff"
        assert result.action == "report breach"
        assert result.object == "incident report"
        assert result.modality == "Must"
        assert result.conditions == "Immediately"
        assert result.time_constraints == "24 hours"
        assert result.compliance_category == "Data Protection"
        assert result.confidence_score == 0.99
        
        mock_client_instance.models.generate_content.assert_called_once()
