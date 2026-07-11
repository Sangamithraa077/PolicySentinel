"""Database session dependency.

`get_db` is the one place a router should ever obtain a `Session` —
never import `SessionLocal` directly in a route module. FastAPI calls
the generator, hands the yielded session to the endpoint, and resumes
it (running the `finally: session.close()`) once the response has been
sent, regardless of whether the endpoint raised.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db_session


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


# Usage: `def endpoint(db: DbSession) -> ...` instead of repeating
# `db: Session = Depends(get_db)` on every route signature.
DbSession = Annotated[Session, Depends(get_db)]
