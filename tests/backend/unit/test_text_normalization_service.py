"""Unit tests for TextNormalizationService — pure logic, no I/O, no
database, no HTTP. Covers whitespace normalization, page number/header/
footer/repeated-title removal, and preservation of headings, numbering,
and table text.
"""

from __future__ import annotations

import pytest

from backend.services.text_normalization_service import TextNormalizationService

pytestmark = pytest.mark.text_normalization


def normalize(text: str) -> str:
    return TextNormalizationService().normalize(text).text


def test_normalizes_internal_and_vertical_whitespace() -> None:
    result = normalize("Too   many    spaces\n\n\n\n\nNext paragraph")

    assert result == "Too many spaces\n\nNext paragraph"


def test_removes_bare_page_number_lines() -> None:
    text = "Section content.\n\n3\n\nMore content."

    assert normalize(text) == "Section content.\n\nMore content."


def test_removes_page_x_of_y_lines() -> None:
    text = "Section content.\n\nPage 3 of 12\n\nMore content."

    assert normalize(text) == "Section content.\n\nMore content."


def test_removes_dashed_and_slash_page_number_variants() -> None:
    text = "First.\n\n- 3 -\n\nSecond.\n\n3/12\n\nThird."

    assert normalize(text) == "First.\n\nSecond.\n\nThird."


def test_removes_repeated_header_keeping_first_occurrence() -> None:
    text = (
        "CONFIDENTIAL\nIntroduction text.\n\n"
        "CONFIDENTIAL\nBody text.\n\n"
        "CONFIDENTIAL\nClosing text."
    )

    result = normalize(text)

    assert result.count("CONFIDENTIAL") == 1
    assert result.startswith("CONFIDENTIAL\nIntroduction text.")
    assert "Body text." in result
    assert "Closing text." in result


def test_removes_repeated_document_title() -> None:
    text = (
        "Acme Corp Policy Manual\n\nIntroduction paragraph.\n\n"
        "Acme Corp Policy Manual\n\nScope paragraph.\n\n"
        "Acme Corp Policy Manual\n\nClosing paragraph."
    )

    result = normalize(text)

    assert result.count("Acme Corp Policy Manual") == 1


def test_keeps_line_repeated_only_twice() -> None:
    # Below the 3-occurrence threshold -- plausibly real content, not boilerplate.
    text = "Approved\n\nSection one.\n\nApproved\n\nSection two."

    result = normalize(text)

    assert result.count("Approved") == 2


def test_preserves_numbered_headings_even_when_repeated() -> None:
    text = (
        "1. Introduction\n\nSome text.\n\n1. Introduction\n\nMore text.\n\n1. Introduction\n\nEnd."
    )

    result = normalize(text)

    assert result.count("1. Introduction") == 3


def test_preserves_decimal_and_lettered_numbering() -> None:
    text = "1. Introduction\n\n1.2 Scope of policy\n\n(a) First condition\n\nb) Second condition"

    result = normalize(text)

    assert "1. Introduction" in result
    assert "1.2 Scope of policy" in result
    assert "(a) First condition" in result
    assert "b) Second condition" in result


def test_preserves_section_and_article_headings() -> None:
    text = "Section 1 - Definitions\n\nBody text.\n\nArticle IV - Termination"

    result = normalize(text)

    assert "Section 1 - Definitions" in result
    assert "Article IV - Termination" in result


def test_does_not_remove_short_numbering_alone_as_a_page_number() -> None:
    # A bare "1." (numbering marker with no trailing title on the same
    # line) must survive -- it isn't a page number (extra period) and
    # clause segmentation may still rely on it.
    text = "Heading block\n\n1.\n\nBody text."

    assert "1." in normalize(text)


def test_preserves_table_rows_as_readable_pipe_delimited_text() -> None:
    text = "Obligations table:\n\nName | Role | Deadline\nAlice | Owner | 2026-01-01"

    result = normalize(text)

    assert "Name | Role | Deadline" in result
    assert "Alice | Owner | 2026-01-01" in result


def test_collapses_excess_whitespace_around_table_pipes_without_breaking_them() -> None:
    text = "Name   |   Role\nAlice   |   Engineer"

    result = normalize(text)

    assert result == "Name | Role\nAlice | Engineer"


def test_removes_repeated_table_header_row_across_page_breaks() -> None:
    text = (
        "Name | Role\nAlice | Engineer\n\n"
        "Name | Role\nBob | Analyst\n\n"
        "Name | Role\nCara | Manager"
    )

    result = normalize(text)

    assert result.count("Name | Role") == 1
    assert "Alice | Engineer" in result
    assert "Bob | Analyst" in result
    assert "Cara | Manager" in result


def test_character_count_matches_returned_text_length() -> None:
    service = TextNormalizationService()

    result = service.normalize("Some   text\n\n\n\nwith noise.")

    assert result.character_count == len(result.text)


def test_full_pipeline_produces_clean_clause_segmentation_ready_text() -> None:
    text = (
        "Acme Corp Policy Manual\n\n"
        "1. Introduction\n\n"
        "This   policy   governs   employee   conduct.\n\n"
        "Page 1 of 3\n\n"
        "Acme Corp Policy Manual\n\n"
        "2. Scope\n\n"
        "Applies to all departments.\n\n"
        "Page 2 of 3\n\n"
        "Acme Corp Policy Manual\n\n"
        "3. Definitions\n\n"
        "Term | Meaning\nPolicy | A governing rule\n\n"
        "Page 3 of 3"
    )

    result = normalize(text)

    assert result.count("Acme Corp Policy Manual") == 1
    assert "Page 1 of 3" not in result
    assert "Page 2 of 3" not in result
    assert "Page 3 of 3" not in result
    assert "1. Introduction" in result
    assert "2. Scope" in result
    assert "3. Definitions" in result
    assert "This policy governs employee conduct." in result
    assert "Term | Meaning" in result
    assert "Policy | A governing rule" in result
