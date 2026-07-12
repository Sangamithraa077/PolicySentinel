import pytest
from backend.models.obligation import Obligation
from backend.services.ai.relationship_classification_service import (
    RelationshipClassificationService,
    RelationshipClassificationResult,
)


def test_mock_classification_fallback() -> None:
    # Service initialization
    service = RelationshipClassificationService()
    
    # 1. Unrelated obligations (missing overlap)
    ob1 = Obligation(
        subject="Developers",
        action="perform security training",
        object="training system",
        modality="Must",
        compliance_category="Security"
    )
    ob2 = Obligation(
        subject="Finance officers",
        action="reconcile bank statements",
        object="financial ledger",
        modality="Must",
        compliance_category="Finance"
    )
    res_unrelated = service.classify_relationship(ob1, ob2)
    assert res_unrelated.relationship_type == "UNRELATED"
    assert res_unrelated.confidence_score > 0.0
    assert len(res_unrelated.explanation) > 0

    # 2. Redundant obligations (identical actions)
    ob3 = Obligation(
        subject="Developers",
        action="perform security training",
        object="training system",
        modality="Must",
        compliance_category="Security"
    )
    res_redundant = service.classify_relationship(ob1, ob3)
    assert res_redundant.relationship_type == "REDUNDANT"
    assert res_redundant.confidence_score > 0.90

    # 3. Complementary obligations (related actions)
    ob4 = Obligation(
        subject="Developers",
        action="submit security training completion certificate",
        object="HR portal",
        modality="Must",
        compliance_category="Security"
    )
    res_complementary = service.classify_relationship(ob1, ob4)
    assert res_complementary.relationship_type == "COMPLEMENTARY"

    # 4. Conflicting obligations (modal contradictions)
    ob5 = Obligation(
        subject="Developers",
        action="perform security training",
        object="training system",
        modality="Must Not",
        compliance_category="Security"
    )
    res_conflict = service.classify_relationship(ob1, ob5)
    assert res_conflict.relationship_type == "CONFLICT"
    assert "contradict" in res_conflict.explanation.lower() or "modality" in res_conflict.explanation.lower()
