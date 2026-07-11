"""PolicyClause — a structural clause produced by clause segmentation: a
heading, subheading, numbered list item, bullet point, or body
paragraph, positioned in the document and in the clause hierarchy.

Plain dataclass, no framework/ORM dependency (see domain/entities/README.md)
— the shared shape between `services/clause_segmentation_service.py`
(the producer) and `domain/interfaces/clause_repository_interface.py`
(the consumer, implemented by `repositories/clause_repository.py`), so
persistence can depend on segmentation's output without either layer
importing the other's implementation.

Distinct from the persisted `models.clause.Clause` ORM row: `level` and
`marker_type` exist only to build correct hierarchy at segmentation/
write time and are not columns in the `clauses` table (see
`domain/interfaces/clause_repository_interface.py::StoredClause` for
the shape that actually round-trips through the database).
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass


class ClauseMarkerType(enum.StrEnum):
    HEADING = "heading"
    SUBHEADING = "subheading"
    NUMBERED_LIST_ITEM = "numbered_list_item"
    BULLET_POINT = "bullet_point"
    BODY = "body"


@dataclass(frozen=True)
class PolicyClause:
    id: uuid.UUID
    parent_id: uuid.UUID | None
    order_index: int
    level: int
    marker_type: ClauseMarkerType
    clause_number: str | None
    heading: str | None
    text: str
