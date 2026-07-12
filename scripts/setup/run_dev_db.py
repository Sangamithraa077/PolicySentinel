import os
import sys
import time
from pathlib import Path

# Setup paths to import backend and scripts correctly
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pgserver
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config

from scripts.setup.seed_database import seed

def ensure_database_exists(admin_uri: str, dbname: str) -> None:
    """Connect to default database and create dbname if it doesn't exist."""
    conn = psycopg2.connect(admin_uri)
    conn.autocommit = True
    with conn.cursor() as cur:
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if not cur.fetchone():
            print(f"Creating database '{dbname}'...")
            cur.execute(f'CREATE DATABASE "{dbname}"')
        else:
            print(f"Database '{dbname}' already exists.")
    conn.close()

def update_env_file(port: int, dbname: str) -> None:
    """Update POSTGRES_PORT and DATABASE_URL in the .env file with the dynamic port."""
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        print("Warning: .env file not found. Skipping auto-update.")
        return

    content = env_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    new_db_url = f"DATABASE_URL=postgresql://postgres:@127.0.0.1:{port}/{dbname}"
    new_postgres_port = f"POSTGRES_PORT={port}"
    
    updated_port = False
    updated_url = False
    
    for i, line in enumerate(lines):
        if line.startswith("POSTGRES_PORT="):
            lines[i] = new_postgres_port
            updated_port = True
        elif line.startswith("DATABASE_URL="):
            lines[i] = new_db_url
            updated_url = True
            
    if not updated_port:
        lines.append(new_postgres_port)
    if not updated_url:
        lines.append(new_db_url)
        
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated .env file with POSTGRES_PORT={port} and DATABASE_URL pointing to 127.0.0.1:{port}")

def main():
    db_dir = REPO_ROOT / "backend" / "dev_postgres_data"
    db_dir.mkdir(exist_ok=True)

    print(f"Starting development PostgreSQL in {db_dir}...")
    server = pgserver.PostgresServer(db_dir)
    server.ensure_postgres_running()

    # Get connection info
    admin_uri = server.get_uri()
    port = int(admin_uri.rsplit(":", 1)[-1].split("/")[0])
    dbname = "policysentinel"
    
    print(f"PostgreSQL server started on port {port}")
    
    # 1. Create database if not exists
    ensure_database_exists(admin_uri, dbname)
    
    # 2. Update .env file
    update_env_file(port, dbname)
    
    # 3. Build connection string
    db_url = f"postgresql://postgres:@127.0.0.1:{port}/{dbname}"
    
    # Set DATABASE_URL in environment for Alembic and SQLAlchemy initialization
    os.environ["DATABASE_URL"] = db_url
    from backend.config.settings import get_settings
    get_settings.cache_clear()
    
    # 4. Run migrations
    print("Running database migrations...")
    cfg = Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "backend" / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    try:
        command.upgrade(cfg, "head")
        print("Migrations complete.")
    except Exception as exc:
        if "extension" not in str(exc).lower():
            raise
        print(
            f"\nReal migration failed because a contrib extension "
            f"isn't available on this Postgres build ({exc!r}). Falling back "
            f"to a patched schema (CITEXT -> TEXT, no pgcrypto/citext).\n"
        )
        import io
        buffer = io.StringIO()
        offline_cfg = Config(str(REPO_ROOT / "backend" / "alembic.ini"), output_buffer=buffer)
        offline_cfg.set_main_option("script_location", str(REPO_ROOT / "backend" / "alembic"))
        offline_cfg.set_main_option("sqlalchemy.url", db_url)
        command.upgrade(offline_cfg, "head", sql=True)
        sql = buffer.getvalue()
        sql = sql.replace("CREATE EXTENSION IF NOT EXISTS pgcrypto;", "")
        sql = sql.replace("CREATE EXTENSION IF NOT EXISTS citext;", "")
        sql = sql.replace("CITEXT", "TEXT")

        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.close()
        print("Patched schema migrations applied successfully.")
    
    # 5. Seed database
    print("Seeding database with development data...")
    engine = create_engine(db_url, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = SessionLocal()
    try:
        seed(session)
    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
    finally:
        session.close()
        engine.dispose()
        
    print("\n-------------------------------------------------------------")
    print("DEVELOPMENT DATABASE IS ONLINE AND ACTIVE!")
    print(f"Database URL: {db_url}")
    print("Press Ctrl+C to shut down the database server.")
    print("-------------------------------------------------------------\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping database...")
        server.cleanup()
        print("Database stopped.")

if __name__ == "__main__":
    main()
