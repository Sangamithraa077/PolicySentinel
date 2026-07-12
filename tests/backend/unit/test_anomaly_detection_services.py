from datetime import date, datetime, timedelta
import pytest

from backend.models.obligation import Obligation
from backend.models.policy_version import PolicyVersion
from backend.models.enums import PolicyVersionStatus, PolicyDocumentFileType
from backend.services.ai.temporal_conflict_detection_service import TemporalConflictDetectionService
from backend.services.ai.strength_conflict_detection_service import StrengthConflictDetectionService
from backend.services.ai.staleness_detection_service import StalenessDetectionService


def test_temporal_conflict_detection_service() -> None:
    service = TemporalConflictDetectionService()

    # 1. Test numerical mismatch
    ob_a = Obligation(action="submit review", time_constraint="within 90 days")
    ob_b = Obligation(action="submit review", time_constraint="within 180 days")
    res1 = service.detect_temporal_conflict(ob_a, ob_b)
    assert res1.is_conflict is True
    assert res1.conflict_type == "deadline_mismatch"
    assert "90 days" in res1.detected_values

    # 2. Test frequency mismatch
    ob_c = Obligation(action="conduct safety drills", time_constraint="monthly basis")
    ob_d = Obligation(action="conduct safety drills", time_constraint="quarterly basis")
    res2 = service.detect_temporal_conflict(ob_c, ob_d)
    assert res2.is_conflict is True
    assert res2.conflict_type == "frequency_mismatch"
    assert "Monthly vs Quarterly" in res2.detected_values

    # 3. Test no conflict
    ob_e = Obligation(action="report gap", time_constraint="monthly")
    ob_f = Obligation(action="report gap", time_constraint="monthly")
    res3 = service.detect_temporal_conflict(ob_e, ob_f)
    assert res3.is_conflict is False
    assert res3.conflict_type == "none"


def test_strength_conflict_detection_service() -> None:
    service = StrengthConflictDetectionService()

    # 1. Test weakened modality (Must -> Should)
    ob_a = Obligation(modality="Must", action="backup databases")
    ob_b = Obligation(modality="Should", action="backup databases")
    res1 = service.detect_strength_conflict(ob_a, ob_b)
    assert res1.is_conflict is True
    assert res1.strength_conflict == "WEAKENED"

    # 2. Test strengthened modality (May -> Shall)
    ob_c = Obligation(modality="May", action="encrypt emails")
    ob_d = Obligation(modality="Shall", action="encrypt emails")
    res2 = service.detect_strength_conflict(ob_c, ob_d)
    assert res2.is_conflict is True
    assert res2.strength_conflict == "STRENGTHENED"

    # 3. Test identical modality
    ob_e = Obligation(modality="Shall", action="conduct drills")
    ob_f = Obligation(modality="Shall", action="conduct drills")
    res3 = service.detect_strength_conflict(ob_e, ob_f)
    assert res3.is_conflict is False
    assert res3.strength_conflict == "NONE"


def test_staleness_detection_service() -> None:
    service = StalenessDetectionService()

    today = date.today()

    # 1. Test superseded version
    pv_superseded = PolicyVersion(
        version_number=1,
        source_file_reference="a.pdf",
        file_hash="h1",
        uploaded_by_user_id=None, # not relevant for mock
        status=PolicyVersionStatus.PUBLISHED,
        effective_date=today - timedelta(days=50),
        uploaded_at=datetime.utcnow(),
        original_filename="a.pdf",
        size_bytes=100,
        file_type=PolicyDocumentFileType.PDF,
        superseded_by_version_id="88888888-8888-8888-8888-888888888888"
    )
    pv_superseded.created_at = datetime.utcnow()
    res1 = service.detect_staleness(pv_superseded)
    assert res1.status == "Outdated"
    assert "superseded" in res1.explanation.lower()

    # 2. Test version older than 2 years
    pv_outdated = PolicyVersion(
        version_number=2,
        source_file_reference="b.pdf",
        file_hash="h2",
        status=PolicyVersionStatus.PUBLISHED,
        effective_date=today - timedelta(days=750),
        uploaded_at=datetime.utcnow(),
        original_filename="b.pdf",
        size_bytes=100,
        file_type=PolicyDocumentFileType.PDF,
    )
    pv_outdated.created_at = datetime.utcnow() - timedelta(days=750)
    res2 = service.detect_staleness(pv_outdated)
    assert res2.status == "Outdated"
    assert "over 2 years" in res2.explanation.lower()

    # 3. Test version older than 1 year (Review Required)
    pv_review = PolicyVersion(
        version_number=3,
        source_file_reference="c.pdf",
        file_hash="h3",
        status=PolicyVersionStatus.PUBLISHED,
        effective_date=today - timedelta(days=400),
        uploaded_at=datetime.utcnow(),
        original_filename="c.pdf",
        size_bytes=100,
        file_type=PolicyDocumentFileType.PDF,
    )
    pv_review.created_at = datetime.utcnow() - timedelta(days=400)
    res3 = service.detect_staleness(pv_review)
    assert res3.status == "Review Required"
    assert "annual review cycle" in res3.explanation.lower()

    # 4. Test version missing effective date (Review Required)
    pv_missing_date = PolicyVersion(
        version_number=4,
        source_file_reference="d.pdf",
        file_hash="h4",
        status=PolicyVersionStatus.PUBLISHED,
        effective_date=None,
        uploaded_at=datetime.utcnow(),
        original_filename="d.pdf",
        size_bytes=100,
        file_type=PolicyDocumentFileType.PDF,
    )
    pv_missing_date.created_at = datetime.utcnow()
    res4 = service.detect_staleness(pv_missing_date)
    assert res4.status == "Review Required"
    assert "lacks an explicit effective date" in res4.explanation.lower()

    # 5. Test recent version (Current)
    pv_current = PolicyVersion(
        version_number=5,
        source_file_reference="e.pdf",
        file_hash="h5",
        status=PolicyVersionStatus.PUBLISHED,
        effective_date=today - timedelta(days=30),
        uploaded_at=datetime.utcnow(),
        original_filename="e.pdf",
        size_bytes=100,
        file_type=PolicyDocumentFileType.PDF,
    )
    pv_current.created_at = datetime.utcnow()
    res5 = service.detect_staleness(pv_current)
    assert res5.status == "Current"
    assert "within the last 12 months" in res5.explanation.lower()
