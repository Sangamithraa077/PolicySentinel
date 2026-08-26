"""Use case: split a normalized policy document's text into an ordered,
hierarchical list of clauses — the step between
`services/text_normalization_service.py` and the (future) obligation
extraction use case.

Deliberately stops there — it does not decide what a clause *means*
(no `ClauseType`/obligation extraction, that's a later, likely
AI-assisted step); it only decides where one clause ends and the next
begins, and how they nest.

Purely rule-based (regex + a stack, no AI), matching four structural
markers commonly found in policy documents, in this precedence order:

  1. HEADING              "Section 1", "Article IV", or top-level "1."
  2. SUBHEADING            nested decimal numbering, e.g. "1.2", "1.2.3"
  3. NUMBERED_LIST_ITEM    parenthesized enumeration: "(a)", "b)", "(iv)", "(1)"
  4. BULLET_POINT          "-", "*", "•", "‣", "▪", "◦" prefixed lines

Any line that matches none of these is BODY content: consecutive such
lines (no blank line, no marker, between them — e.g. a table's rows)
accumulate into one paragraph, flushed as a unit into whichever clause
most recently opened (or into a "preamble" clause of its own if nothing
has opened yet) on the next blank line or marker — so no text from the
input is ever dropped, including table rows rendered by
`parsing/docx_parser.py` as " | "-joined lines, which never match a
marker pattern and pass through untouched. Critically, a marker line
always flushes the *previous* clause's pending paragraph before opening
the new clause — otherwise consecutive markers with no blank line
between them (e.g. a tight bullet list) would be swallowed as trailing
text of the first item instead of becoming siblings.

Hierarchy is resolved with a single left-to-right scan and a stack of
open ancestors, popping any ancestor at the same or deeper level before
attaching a new clause — the same algorithm an outline/TOC renderer
uses. HEADING/SUBHEADING levels come directly from decimal depth (or 1
for a keyword heading); NUMBERED_LIST_ITEM and BULLET_POINT have no
intrinsic depth of their own, so each nests one level below the nearest
enclosing heading/subheading (bullets may additionally nest under a
numbered list item) rather than under a same-kind sibling — which is
what keeps consecutive "(a)", "(b)", "(c)" items as siblings instead of
drifting one level deeper with each item.

Known limitation: because whitespace normalization already strips
per-line indentation, this engine cannot tell "(a)" and a deeper "(i)"
apart from indentation the way a layout-aware parser could — all
NUMBERED_LIST_ITEM markers under one heading/subheading are treated as
siblings at a single flat level. Good enough for clause boundaries and
numbering, not a substitute for a layout-aware outline extractor.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from backend.domain.entities.clause import ClauseMarkerType, PolicyClause

_SECTION_HEADING_RE = re.compile(
    r"^(section|article|chapter|appendix|rule|requirement|directive|policy|control|guideline)\s+([0-9a-z]+(?:\.[0-9a-z]+)*)\b[\s:.\-–—]*(.*)$",
    re.IGNORECASE,
)
_ROMAN_HEADING_RE = re.compile(
    r"^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV)\.[\s:.\-–—]+(.*)$",
    re.IGNORECASE,
)
_LETTER_HEADING_RE = re.compile(r"^([A-Z])\.[\s:.\-–—]+([A-Z0-9\s:,\-–—]{2,})$")
_DECIMAL_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$")
_NUMBERED_LIST_ITEM_RE = re.compile(r"^\(?([a-z0-9]{1,4})\)\.?\s+(.*)$", re.IGNORECASE)
_BULLET_RE = re.compile(r"^[-*•‣▪◦]\s+(.*)$")

_KNOWN_SECTION_TITLES = frozenset(
    {
        "PURPOSE",
        "SCOPE",
        "OVERVIEW",
        "BACKGROUND",
        "DEFINITIONS",
        "POLICY STATEMENT",
        "ROLES AND RESPONSIBILITIES",
        "RESPONSIBILITIES",
        "REQUIREMENTS",
        "PROCEDURES",
        "COMPLIANCE AND ENFORCEMENT",
        "ENFORCEMENT",
        "EXCEPTIONS",
        "REVISION HISTORY",
        "REFERENCES",
        "APPLICABILITY",
        "DATA PRIVACY",
        "INFORMATION SECURITY",
        "ACCESS CONTROL",
    }
)


@dataclass(frozen=True)
class _Marker:
    kind: ClauseMarkerType
    level_hint: int
    clause_number: str | None
    content: str


@dataclass(frozen=True)
class _StackEntry:
    level: int
    clause_id: uuid.UUID
    kind: ClauseMarkerType


@dataclass
class _ClauseBuilder:
    id: uuid.UUID
    parent_id: uuid.UUID | None
    order_index: int
    level: int
    marker_type: ClauseMarkerType
    clause_number: str | None
    heading: str | None
    text_parts: list[str] = field(default_factory=list)


_HEADING_LEVEL_KINDS = frozenset({ClauseMarkerType.HEADING, ClauseMarkerType.SUBHEADING})
_LIST_ANCHOR_KINDS = _HEADING_LEVEL_KINDS | {ClauseMarkerType.NUMBERED_LIST_ITEM}


class ClauseSegmentationService:
    def segment(self, text: str, use_ai_fallback: bool = True) -> list[PolicyClause]:
        clauses = self._segment_rules(text)

        # Evaluate quality of rule-based segmentation:
        # AI fallback is only needed if rule-based segmentation completely failed to find structure
        # (i.e. zero headings/numbers found for a long document, or the entire doc is one single BODY clause).
        num_structured_clauses = sum(1 for c in clauses if c.heading or c.clause_number)
        is_poor_segmentation = (
            len(clauses) == 0
            or (len(clauses) == 1 and clauses[0].marker_type is ClauseMarkerType.BODY and len(text) > 200)
            or (num_structured_clauses == 0 and len(text) > 500)
        )

        if is_poor_segmentation and use_ai_fallback:
            try:
                from backend.services.ai.ai_clause_segmentation_service import AIClauseSegmentationService

                ai_segmenter = AIClauseSegmentationService()
                ai_clauses = ai_segmenter.segment_with_ai(text)
                if len(ai_clauses) >= 1:
                    return ai_clauses
            except Exception as exc:
                pass

        return clauses

    def _segment_rules(self, text: str) -> list[PolicyClause]:
        builders: list[_ClauseBuilder] = []
        stack: list[_StackEntry] = []
        paragraph: list[str] = []

        def flush_paragraph() -> None:
            if paragraph:
                _append_body(builders, "\n".join(paragraph))
                paragraph.clear()

        for raw_line in text.strip().split("\n"):
            line = raw_line.strip()
            if not line:
                flush_paragraph()
                continue

            marker = _match_marker(line)
            if marker is None:
                paragraph.append(line)
                continue

            flush_paragraph()

            level = _resolve_level(marker, stack)
            while stack and stack[-1].level >= level:
                stack.pop()
            parent_id = stack[-1].clause_id if stack else None

            clean_heading = marker.content
            body_part = None
            if marker.kind in _HEADING_LEVEL_KINDS and marker.content:
                for sep in (": ", " - ", " – ", " — "):
                    if sep in marker.content:
                        parts = marker.content.split(sep, 1)
                        if len(parts[0].strip()) < 80 and len(parts[1].strip()) > 0:
                            clean_heading = parts[0].strip()
                            body_part = parts[1].strip()
                            break

            clause_id = uuid.uuid4()
            builders.append(
                _ClauseBuilder(
                    id=clause_id,
                    parent_id=parent_id,
                    order_index=len(builders),
                    level=level,
                    marker_type=marker.kind,
                    clause_number=marker.clause_number,
                    heading=clean_heading if (marker.kind in _HEADING_LEVEL_KINDS and clean_heading) else None,
                )
            )
            stack.append(_StackEntry(level=level, clause_id=clause_id, kind=marker.kind))
            if body_part:
                paragraph.append(body_part)
            elif marker.content:
                paragraph.append(marker.content)

        flush_paragraph()

        return [
            PolicyClause(
                id=b.id,
                parent_id=b.parent_id,
                order_index=b.order_index,
                level=b.level,
                marker_type=b.marker_type,
                clause_number=b.clause_number,
                heading=b.heading,
                text="\n\n".join(b.text_parts),
            )
            for b in builders
        ]


def _append_body(builders: list[_ClauseBuilder], block: str) -> None:
    if builders:
        builders[-1].text_parts.append(block)
        return
    builders.append(
        _ClauseBuilder(
            id=uuid.uuid4(),
            parent_id=None,
            order_index=0,
            level=1,
            marker_type=ClauseMarkerType.BODY,
            clause_number=None,
            heading=None,
            text_parts=[block],
        )
    )


def _match_marker(line: str) -> _Marker | None:
    if not line:
        return None

    match = _SECTION_HEADING_RE.match(line)
    if match:
        keyword, designator, content = match.groups()
        formatted_designator = designator.upper() if designator.isalpha() else designator
        return _Marker(
            ClauseMarkerType.HEADING,
            level_hint=1,
            clause_number=f"{keyword.title()} {formatted_designator}",
            content=content.strip(),
        )

    match = _ROMAN_HEADING_RE.match(line)
    if match:
        numeral, content = match.groups()
        return _Marker(
            ClauseMarkerType.HEADING,
            level_hint=1,
            clause_number=f"Section {numeral.upper()}",
            content=content.strip(),
        )

    match = _LETTER_HEADING_RE.match(line)
    if match:
        letter, content = match.groups()
        return _Marker(
            ClauseMarkerType.HEADING,
            level_hint=1,
            clause_number=f"Section {letter.upper()}",
            content=content.strip(),
        )

    match = _DECIMAL_RE.match(line)
    if match:
        number, content = match.groups()
        # Guard against single-digit wrapped sentence false positives (e.g. "15 days notice...")
        is_single_num = "." not in number
        if is_single_num and content and content[0].islower():
            pass
        else:
            depth = number.count(".") + 1
            kind = ClauseMarkerType.HEADING if depth == 1 else ClauseMarkerType.SUBHEADING
            return _Marker(kind, level_hint=depth, clause_number=number, content=content.strip())

    # Check unnumbered uppercase or known section title heading
    upper_line = line.strip().upper()
    if len(line) <= 80 and not line.endswith((".", ";", ",")):
        if upper_line in _KNOWN_SECTION_TITLES or (len(line) >= 4 and line.isupper() and line.isalpha()):
            return _Marker(
                ClauseMarkerType.HEADING,
                level_hint=1,
                clause_number=None,
                content=line.strip(),
            )

    match = _NUMBERED_LIST_ITEM_RE.match(line)
    if match:
        label, content = match.groups()
        return _Marker(
            ClauseMarkerType.NUMBERED_LIST_ITEM,
            level_hint=0,
            clause_number=f"({label.lower()})",
            content=content.strip(),
        )

    match = _BULLET_RE.match(line)
    if match:
        (content,) = match.groups()
        return _Marker(
            ClauseMarkerType.BULLET_POINT, level_hint=0, clause_number=None, content=content.strip()
        )

    return None


def _resolve_level(marker: _Marker, stack: list[_StackEntry]) -> int:
    if marker.kind in _HEADING_LEVEL_KINDS:
        return marker.level_hint
    if marker.kind is ClauseMarkerType.NUMBERED_LIST_ITEM:
        return _nearest_ancestor_level(stack, _HEADING_LEVEL_KINDS) + 1
    return _nearest_ancestor_level(stack, _LIST_ANCHOR_KINDS) + 1


def _nearest_ancestor_level(stack: list[_StackEntry], kinds: frozenset[ClauseMarkerType]) -> int:
    for entry in reversed(stack):
        if entry.kind in kinds:
            return entry.level
    return 0

