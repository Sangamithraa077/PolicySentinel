"""Use case: turn a parsed document's plain text into clause-segmentation-
ready text — the step between `services/document_parsing_service.py` and
the (future) clause segmentation use case.

Deliberately stops there — it does not identify or split clauses itself,
and does not call the AI layer; it only removes the noise that would
otherwise pollute clause boundaries and re-normalizes whitespace.

Beyond the whitespace collapsing already done by
`utils/text_cleaning.py::clean_extracted_text` (reused here as the first
and last step), this module removes two kinds of line-level noise that
survive plain-text extraction:

  - page numbers ("3", "Page 3 of 12", "- 3 -", "3/12") sitting alone on
    their own line
  - running headers/footers and repeated document titles — anything
    short that recurs verbatim three or more times through the document
    (e.g. "CONFIDENTIAL", "Acme Corp Policy Manual", printed on every
    page) — keeping only the first occurrence, since that's the one
    occurrence a reader would actually expect to see

Both passes explicitly skip anything that looks like a numbered/lettered
heading (see `_HEADING_RE`), so "Preserve headings and numbering" wins
over "remove repeats" whenever a line could plausibly be read either
way — clause segmentation depends on those markers surviving intact.

Tables are not specially detected here: `parsing/docx_parser.py` already
renders them as one " | "-joined line per row, and plain
whitespace-only cleanup never touches a single pipe character, so a
table that entered this function readable leaves it readable. (PDF text
extraction has no reliable table structure to preserve in the first
place — a `pypdf`-level limitation, not something this module can
recover.)
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from backend.utils.text_cleaning import clean_extracted_text

_MAX_BOILERPLATE_LINE_LENGTH = 100
_MIN_REPETITIONS_TO_TREAT_AS_BOILERPLATE = 3

_PAGE_NUMBER_RE = re.compile(
    r"""
    \d{1,4}                                 # bare number, e.g. "3"
    |page\s+\d+(?:\s+of\s+\d+)?             # "Page 3", "Page 3 of 12"
    |\d{1,4}\s*/\s*\d{1,4}                  # "3/12"
    |-\s*\d{1,4}\s*-                        # "- 3 -"
    """,
    re.IGNORECASE | re.VERBOSE,
)

_HEADING_RE = re.compile(
    r"""^(?:
        \d+(?:\.\d+)*\.?\s+\S               # "1. Introduction", "2.3 Scope"
        |[ivxlcdm]+\.\s+\S                  # "iv. Something"
        |\(?[a-z]\)\.?\s+\S                 # "(a) Something", "a) Something"
        |(section|article|chapter|appendix)\s+\S  # "Section 1 - Title"
    )""",
    re.IGNORECASE | re.VERBOSE,
)


@dataclass(frozen=True)
class NormalizedText:
    text: str
    character_count: int


class TextNormalizationService:
    def normalize(self, text: str) -> NormalizedText:
        lines = clean_extracted_text(text).split("\n")
        lines = _remove_page_number_lines(lines)
        lines = _remove_repeated_boilerplate_lines(lines)
        cleaned = clean_extracted_text("\n".join(lines))
        return NormalizedText(text=cleaned, character_count=len(cleaned))


def _is_heading_line(line: str) -> bool:
    return _HEADING_RE.match(line) is not None


def _remove_page_number_lines(lines: list[str]) -> list[str]:
    return [
        line
        for line in lines
        if not (line and _PAGE_NUMBER_RE.fullmatch(line) and not _is_heading_line(line))
    ]


def _remove_repeated_boilerplate_lines(lines: list[str]) -> list[str]:
    counts = Counter(
        line
        for line in lines
        if line and len(line) <= _MAX_BOILERPLATE_LINE_LENGTH and not _is_heading_line(line)
    )
    repeated = {
        line for line, count in counts.items() if count >= _MIN_REPETITIONS_TO_TREAT_AS_BOILERPLATE
    }

    seen: set[str] = set()
    kept: list[str] = []
    for line in lines:
        if line in repeated:
            if line in seen:
                continue
            seen.add(line)
        kept.append(line)
    return kept
