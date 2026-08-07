"""FileBlob — raw bytes of an uploaded document, persisted in Postgres.

Backs `repositories/postgres_file_storage_repository.py`, the production
implementation of `FileStorageInterface`. Exists because Render's
free-tier web services have ephemeral local disk: anything written under
`LocalFileStorageRepository`'s storage root is silently lost on the next
deploy/restart, while `PolicyVersion.source_file_reference` (in Postgres)
survives — the file and the row that points to it fall out of sync, and
downloads start 500ing with "Stored file not found". Storing the bytes in
the same Postgres database as the rest of the app's data means they
survive deploys for free, at the cost of bloating the database with
binary content — acceptable at hackathon/demo scale; would need
revisiting (e.g. real object storage) before handling any real volume of
large files.

`storage_path` (the same relative-path string every `FileStorageInterface`
caller already generates, e.g. "companies/{id}/policies/{id}/{uuid}.pdf")
is the primary key directly — no separate surrogate id, since nothing
ever looks this table up any other way.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, LargeBinary, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from backend.database.base import Base


class FileBlob(Base):
    __tablename__ = "stored_files"

    storage_path: Mapped[str] = mapped_column(Text, primary_key=True)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
