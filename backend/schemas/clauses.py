"""DTOs for clause endpoints.

One shape covers both the list and detail responses — unlike
`schemas/policies.py`'s Summary/Detail split, there's no trimmed vs.
full view here: `text` (the clause's actual content) is exactly what a
list or search result is browsed for, so there's nothing meaningful to
omit from a list item.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class ClauseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    policy_id: uuid.UUID
    policy_version_id: uuid.UUID
    parent_clause_id: uuid.UUID | None
    clause_number: str | None
    heading: str | None
    text: str
    order_index: int


class ClauseListResponse(BaseModel):
    items: list[ClauseResponse]
    total: int
    limit: int
    offset: int
