"""Stateless text-cleanup helpers shared by document parsing.

No business meaning of its own (see utils/README.md) — just normalizing
whitespace noise that extraction libraries commonly introduce (repeated
spaces from PDF layout reconstruction, trailing spaces from DOCX
paragraphs, runs of blank lines) without touching the actual words.
"""

from __future__ import annotations

import re

_INTERNAL_WHITESPACE_RE = re.compile(r"[ \t\f\v]+")
_EXCESS_BLANK_LINES_RE = re.compile(r"\n{3,}")


def clean_extracted_text(text: str) -> str:
    """Collapse redundant whitespace while preserving paragraph structure.

    - Runs of spaces/tabs within a line collapse to a single space, and
      each line is stripped of leading/trailing whitespace.
    - Three or more consecutive newlines (multiple blank lines) collapse
      to exactly one blank line, so paragraph breaks survive but excess
      vertical whitespace doesn't.
    - Leading/trailing whitespace on the whole document is stripped.
    """
    lines = [_INTERNAL_WHITESPACE_RE.sub(" ", line).strip() for line in text.split("\n")]
    collapsed = "\n".join(lines)
    collapsed = _EXCESS_BLANK_LINES_RE.sub("\n\n", collapsed)
    return collapsed.strip()
