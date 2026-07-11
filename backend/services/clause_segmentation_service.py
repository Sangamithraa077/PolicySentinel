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
    r"^(section|article|chapter|appendix)\s+(\d+|[ivxlcdm]+|[a-z])\b[\s:.\-–—]*(.*)$",
    re.IGNORECASE,
)
_DECIMAL_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$")
_NUMBERED_LIST_ITEM_RE = re.compile(r"^\(?([a-z0-9]{1,4})\)\.?\s+(.*)$", re.IGNORECASE)
_BULLET_RE = re.compile(r"^[-*•‣▪◦]\s+(.*)$")


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
    def segment(self, text: str) -> list[PolicyClause]:
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

            is_heading_with_content = marker.kind in _HEADING_LEVEL_KINDS and marker.content
            clause_id = uuid.uuid4()
            builders.append(
                _ClauseBuilder(
                    id=clause_id,
                    parent_id=parent_id,
                    order_index=len(builders),
                    level=level,
                    marker_type=marker.kind,
                    clause_number=marker.clause_number,
                    heading=marker.content if is_heading_with_content else None,
                )
            )
            stack.append(_StackEntry(level=level, clause_id=clause_id, kind=marker.kind))
            if marker.content:
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

    match = _DECIMAL_RE.match(line)
    if match:
        number, content = match.groups()
        depth = number.count(".") + 1
        kind = ClauseMarkerType.HEADING if depth == 1 else ClauseMarkerType.SUBHEADING
        return _Marker(kind, level_hint=depth, clause_number=number, content=content.strip())

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
