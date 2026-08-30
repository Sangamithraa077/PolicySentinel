"""Shared pytest fixtures for the backend test suite.

Spins up a throwaway, fully self-contained PostgreSQL instance for the
test session via the `pgserver` embedded binary (no Docker or system
Postgres install required — see the "Testing" section of
backend/requirements.txt), applies the real Alembic migrations to it,
and wires FastAPI's dependency overrides so tests hit this database and
a temp-directory file store instead of whatever `Settings` would
otherwise point at.
"""

from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# The app resolves relative paths (logs/, uploads/) against its cwd, same
# as when run normally via `uvicorn backend.main:app` from the repo root
# (or the container's WORKDIR). Match that so tests don't scatter a stray
# logs/ directory somewhere else.
os.chdir(REPO_ROOT)

# Keep every test file comfortably under this so "file too large" is the
# only test that needs to actually build an oversized payload.
TEST_MAX_UPLOAD_SIZE_MB = 1

os.environ["GEMINI_API_KEY"] = "changeme"
os.environ["ANTHROPIC_API_KEY"] = "changeme"



def _apply_schema(admin_uri: str, dbname: str, port: int) -> None:
    """Creates `dbname` and brings it up to the latest Alembic revision.

    Tries the real migrations unmodified first — correct for any real
    Postgres (including the project's actual postgres:16-alpine). Falls
    back to a patched copy of the *same* migrations' generated SQL, with
    the pgcrypto/citext extension calls removed and CITEXT swapped for
    TEXT, only if those contrib extensions genuinely aren't installed on
    this Postgres build (true for the embedded pgserver binary used
    here, never for a real install/Docker image). That substitution
    only affects users.email case-insensitivity — nothing the policy
    upload/management flow being tested touches.
    """
    import psycopg2
    from alembic import command
    from alembic.config import Config

    from backend.config.settings import get_settings

    admin_conn = psycopg2.connect(admin_uri)
    admin_conn.autocommit = True
    with admin_conn.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{dbname}"')
    admin_conn.close()

    base_uri, _ = admin_uri.rsplit("/", 1)
    test_url = f"{base_uri}/{dbname}"

    # alembic/env.py deliberately ignores whatever sqlalchemy.url we pass
    # via Config and always rebuilds it from config.settings.get_settings()
    # (the app's single source of truth for DATABASE_URL). Point that at
    # the test database before invoking alembic, and clear the lru_cache
    # so it's actually re-read -- this also means database/session.py's
    # module-level engine (built the same way, whenever it's next
    # imported) targets the test database rather than the real one.
    os.environ["DATABASE_URL"] = test_url
    get_settings.cache_clear()

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", test_url)

    try:
        command.upgrade(cfg, "head")
        return
    except Exception as exc:
        if "extension" not in str(exc).lower():
            raise
        print(
            f"\n[conftest] Real migration failed because a contrib extension "
            f"isn't available on this Postgres build ({exc!r}). Falling back "
            f"to a patched schema (CITEXT -> TEXT, no pgcrypto/citext) for "
            f"this test run only.\n"
        )

    buffer = io.StringIO()
    offline_cfg = Config(str(BACKEND_DIR / "alembic.ini"), output_buffer=buffer)
    offline_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(offline_cfg, "head", sql=True)
    sql = buffer.getvalue()
    sql = sql.replace("CREATE EXTENSION IF NOT EXISTS pgcrypto;", "")
    sql = sql.replace("CREATE EXTENSION IF NOT EXISTS citext;", "")
    sql = sql.replace("CITEXT", "TEXT")

    conn = psycopg2.connect(test_url)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.close()


@pytest.fixture(scope="session")
def postgres_url() -> Generator[str, None, None]:
    use_pgserver = False
    try:
        import pgserver
        use_pgserver = True
    except ImportError:
        pass

    if use_pgserver:
        data_root = Path(tempfile.mkdtemp())
        server = pgserver.get_server(str(data_root / "pgdata"))
        try:
            port = int(server.get_uri().rsplit(":", 1)[-1].split("/")[0])
            dbname = f"policysentinel_test_{uuid.uuid4().hex[:8]}"
            _apply_schema(server.get_uri(), dbname, port)
            yield f"postgresql://postgres:@127.0.0.1:{port}/{dbname}"
        finally:
            server.cleanup()
            shutil.rmtree(data_root, ignore_errors=True)
    else:
        # Fall back to using the running Docker database or local PostgreSQL instance
        import psycopg2
        
        # We can construct the admin URI from the environment's DATABASE_URL or defaults.
        db_user = os.environ.get("POSTGRES_USER", "policysentinel")
        db_pass = os.environ.get("POSTGRES_PASSWORD", "changeme")
        db_host = os.environ.get("POSTGRES_HOST", "127.0.0.1")
        db_port = os.environ.get("POSTGRES_PORT", "5433")
        
        # Admin URI (typically connecting to the default postgres or template1 DB)
        admin_uri = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/postgres"
        
        dbname = f"policysentinel_test_{uuid.uuid4().hex[:8]}"
        try:
            _apply_schema(admin_uri, dbname, int(db_port))
            # Test postgres URL needs the right credentials:
            yield f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{dbname}"
            
            # Clean up the test database after the test session
            admin_conn = psycopg2.connect(admin_uri)
            admin_conn.autocommit = True
            with admin_conn.cursor() as cur:
                cur.execute(f'DROP DATABASE IF EXISTS "{dbname}"')
            admin_conn.close()
        except Exception as exc:
            pytest.skip(f"pgserver not installed and local Postgres connection failed: {exc}")


@pytest.fixture(scope="session")
def db_engine(postgres_url: str) -> Generator[Engine, None, None]:
    engine = create_engine(postgres_url, future=True)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    # Clear all database tables to guarantee test isolation
    from sqlalchemy import MetaData
    meta = MetaData()
    meta.reflect(bind=db_engine)
    
    session_factory = sessionmaker(
        bind=db_engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = session_factory()
    
    # Delete child tables before parent tables to avoid foreign key violations
    for table in reversed(meta.sorted_tables):
        session.execute(table.delete())
    session.commit()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    return tmp_path / "uploads"


@pytest.fixture
def file_storage_service(upload_dir: Path) -> Any:
    from backend.repositories.local_file_storage_repository import LocalFileStorageRepository
    from backend.services.file_storage_service import FileStorageService

    return FileStorageService(LocalFileStorageRepository(upload_dir))


@pytest.fixture
def client(db_session: Session, file_storage_service: Any) -> Generator[TestClient, None, None]:
    from backend.api.dependencies.database import get_db
    from backend.api.dependencies.uploads import (
        get_file_storage_service,
        get_validate_policy_document_service,
    )
    from backend.main import app
    from backend.services.validate_policy_document_service import ValidatePolicyDocumentService

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_file_storage_service() -> Any:
        return file_storage_service

    def override_get_validate_policy_document_service() -> ValidatePolicyDocumentService:
        return ValidatePolicyDocumentService(max_upload_size_mb=TEST_MAX_UPLOAD_SIZE_MB)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_file_storage_service] = override_get_file_storage_service
    app.dependency_overrides[get_validate_policy_document_service] = (
        override_get_validate_policy_document_service
    )
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def seeded_company_and_user(db_session: Session) -> Any:
    """A fresh Company + User per test — avoids relying on shared/global
    seed data so tests never collide with each other."""
    import bcrypt

    from backend.models.company import Company
    from backend.models.enums import UserRole
    from backend.models.user import User

    unique = uuid.uuid4().hex[:8]
    company = Company(
        name=f"Test Company {unique}",
        industry="Testing",
        jurisdiction="Testland",
        registration_number=f"TEST-{unique}",
    )
    user = User(
        company=company,
        email=f"tester-{unique}@example.com",
        password_hash=bcrypt.hashpw(b"irrelevant", bcrypt.gensalt()).decode("ascii"),
        full_name="Test User",
        role=UserRole.ADMIN,
    )
    db_session.add(company)
    db_session.add(user)
    db_session.commit()
    return company, user
