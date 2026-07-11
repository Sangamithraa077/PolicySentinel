"""Unit tests for ClauseSegmentationService — pure logic, no I/O, no
database, no HTTP. Covers marker detection (headings, subheadings,
numbered list items, bullet points), unique clause IDs, ordering,
parent-child hierarchy, section-number preservation, and body/table
text retention.
"""

from __future__ import annotations

import pytest

from backend.domain.entities.clause import ClauseMarkerType, PolicyClause
from backend.services.clause_segmentation_service import ClauseSegmentationService

pytestmark = pytest.mark.clause_segmentation


def segment(text: str) -> list[PolicyClause]:
    return ClauseSegmentationService().segment(text)


def by_number(clauses: list[PolicyClause], number: str) -> PolicyClause:
    return next(c for c in clauses if c.clause_number == number)


@pytest.mark.clause_ordering
def test_returns_ordered_list_matching_document_order() -> None:
    text = "1. Introduction\n\nIntro text.\n\n2. Scope\n\nScope text."

    clauses = segment(text)

    assert [c.order_index for c in clauses] == [0, 1]
    assert [c.clause_number for c in clauses] == ["1", "2"]


def test_every_clause_gets_a_unique_id() -> None:
    text = "1. Introduction\n\n2. Scope\n\n3. Definitions"

    clauses = segment(text)

    ids = [c.id for c in clauses]
    assert len(ids) == len(set(ids)) == 3


def test_detects_section_style_heading() -> None:
    clauses = segment("Section 1 - Definitions\n\nBody text.")

    clause = clauses[0]
    assert clause.marker_type is ClauseMarkerType.HEADING
    assert clause.clause_number == "Section 1"
    assert clause.heading == "Definitions"
    assert clause.level == 1


def test_detects_article_heading_with_roman_numeral() -> None:
    clauses = segment("Article IV - Termination")

    clause = clauses[0]
    assert clause.clause_number == "Article IV"
    assert clause.heading == "Termination"


def test_detects_top_level_numbered_heading() -> None:
    clauses = segment("1. Introduction\n\nBody text.")

    clause = clauses[0]
    assert clause.marker_type is ClauseMarkerType.HEADING
    assert clause.clause_number == "1"
    assert clause.heading == "Introduction"
    assert clause.level == 1


def test_detects_decimal_subheading() -> None:
    clauses = segment("1. Introduction\n\n1.2 Scope of policy\n\nBody.")

    subheading = by_number(clauses, "1.2")
    assert subheading.marker_type is ClauseMarkerType.SUBHEADING
    assert subheading.heading == "Scope of policy"
    assert subheading.level == 2


def test_deeper_decimal_numbering_produces_deeper_level() -> None:
    clauses = segment("1.2.3 Detail\n\nBody.")

    clause = clauses[0]
    assert clause.clause_number == "1.2.3"
    assert clause.level == 3


def test_detects_lettered_numbered_list_item() -> None:
    clauses = segment("1. Introduction\n\n(a) First condition\n\n(b) Second condition")

    first = by_number(clauses, "(a)")
    second = by_number(clauses, "(b)")
    assert first.marker_type is ClauseMarkerType.NUMBERED_LIST_ITEM
    assert first.text == "First condition"
    assert second.text == "Second condition"


def test_detects_parenthesized_digit_numbered_list_item() -> None:
    clauses = segment("1. Introduction\n\n(1) First item\n\n(2) Second item")

    first = by_number(clauses, "(1)")
    assert first.marker_type is ClauseMarkerType.NUMBERED_LIST_ITEM
    assert first.text == "First item"


def test_detects_bullet_points() -> None:
    clauses = segment("1. Introduction\n\n- point one\n- point two\n* point three")

    bullets = [c for c in clauses if c.marker_type is ClauseMarkerType.BULLET_POINT]
    assert [b.text for b in bullets] == ["point one", "point two", "point three"]
    assert all(b.clause_number is None for b in bullets)


def test_consecutive_bullets_with_no_blank_line_are_siblings_not_nested() -> None:
    clauses = segment("1. Introduction\n\n- point one\n- point two\n- point three")

    bullets = [c for c in clauses if c.marker_type is ClauseMarkerType.BULLET_POINT]
    heading = by_number(clauses, "1")
    assert all(b.level == bullets[0].level for b in bullets)
    assert all(b.parent_id == heading.id for b in bullets)


def test_preserves_parent_child_hierarchy_across_heading_and_subheading() -> None:
    text = (
        "1. Introduction\n\nIntro.\n\n1.1 Purpose\n\nPurpose text.\n\n"
        "1.2 Audience\n\nAudience text."
    )

    clauses = segment(text)

    heading = by_number(clauses, "1")
    purpose = by_number(clauses, "1.1")
    audience = by_number(clauses, "1.2")
    assert heading.parent_id is None
    assert purpose.parent_id == heading.id
    assert audience.parent_id == heading.id  # sibling of 1.1, not nested under it


def test_numbered_list_items_nest_under_nearest_heading() -> None:
    text = "1. Introduction\n\n1.1 Scope\n\n(a) First\n\n(b) Second"

    clauses = segment(text)

    subheading = by_number(clauses, "1.1")
    first_item = by_number(clauses, "(a)")
    second_item = by_number(clauses, "(b)")
    assert first_item.parent_id == subheading.id
    assert second_item.parent_id == subheading.id


def test_bullets_nest_under_enclosing_numbered_list_item() -> None:
    text = "1. Introduction\n\n(a) Requirements\n\n- detail one\n- detail two"

    clauses = segment(text)

    item = by_number(clauses, "(a)")
    bullets = [c for c in clauses if c.marker_type is ClauseMarkerType.BULLET_POINT]
    assert all(b.parent_id == item.id for b in bullets)


def test_sibling_headings_pop_deeper_ancestors_off_the_stack() -> None:
    text = "1. Introduction\n\n1.1 Purpose\n\n2. Scope"

    clauses = segment(text)

    scope = by_number(clauses, "2")
    assert scope.parent_id is None
    assert scope.level == 1


def test_preserves_section_numbers_across_marker_types() -> None:
    text = "Section 1 - Definitions\n\n1.1 Term A\n\n(a) Detail\n\n- note"

    clauses = segment(text)

    assert by_number(clauses, "Section 1").clause_number == "Section 1"
    assert by_number(clauses, "1.1").clause_number == "1.1"
    assert by_number(clauses, "(a)").clause_number == "(a)"


def test_preamble_text_before_first_heading_becomes_its_own_top_level_clause() -> None:
    text = "Acme Corp Policy Manual\n\n1. Introduction\n\nBody."

    clauses = segment(text)

    preamble = clauses[0]
    assert preamble.marker_type is ClauseMarkerType.BODY
    assert preamble.text == "Acme Corp Policy Manual"
    assert preamble.parent_id is None
    heading = by_number(clauses, "1")
    assert heading.parent_id is None  # not nested under the preamble


def test_body_paragraphs_are_appended_to_the_most_recently_opened_clause() -> None:
    text = "1. Introduction\n\nFirst paragraph.\n\nSecond paragraph."

    clause = segment(text)[0]

    assert clause.text == "Introduction\n\nFirst paragraph.\n\nSecond paragraph."


def test_table_rows_are_preserved_as_readable_text_within_a_clause() -> None:
    text = "1. Definitions\n\nTerm | Meaning\nPolicy | A governing rule"

    clause = segment(text)[0]

    assert "Term | Meaning" in clause.text
    assert "Policy | A governing rule" in clause.text


def test_does_not_perform_obligation_extraction() -> None:
    # The output dataclass has no notion of obligations/clause type --
    # only structural fields. This test exists to pin that contract.
    clause = segment("1. Employees must comply with this policy.")[0]

    fields = clause.__dataclass_fields__.keys()
    assert "clause_type" not in fields
    assert "obligation" not in fields


def test_empty_text_returns_empty_list() -> None:
    assert segment("") == []
    assert segment("   \n\n   ") == []
