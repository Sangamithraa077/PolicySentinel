import os
import shutil
import sys
from pathlib import Path

# Root the repository path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import bcrypt
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.database.session import SessionLocal
from backend.models.company import Company
from backend.models.user import User
from backend.models.enums import UserRole
from backend.graph.neo4j_client import Neo4jClient


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def reset_database():
    print("[Reset] Connecting to PostgreSQL database...")
    db: Session = SessionLocal()
    
    # 1. Truncate all relational tables
    print("[Reset] Truncating all PostgreSQL tables...")
    try:
        db.execute(text(
            "TRUNCATE TABLE companies, users, policies, policy_versions, clauses, "
            "obligations, regulatory_mappings, conflicts, recommendations, compliance_audit_logs CASCADE;"
        ))
        db.commit()
        print("[Reset] Relational database reset successful.")
    except Exception as exc:
        db.rollback()
        print(f"[Reset] Relational database truncate failed: {exc}")
        sys.exit(1)

    # 2. Seed single clean company & administrator
    print("[Reset] Seeding clean demo tenant company and admin user...")
    try:
        co = Company(name="Acme Global Corporation")
        db.add(co)
        db.flush()

        password_hash = hash_password("DemoPassword123!")
        admin_user = User(
            company_id=co.id,
            email="admin@acmeglobal.com",
            password_hash=password_hash,
            full_name="Compliance Administrator",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print(f"[Reset] Seeded Company ID: {co.id}")
        print(f"[Reset] Seeded User ID: {admin_user.id}")
    except Exception as exc:
        db.rollback()
        print(f"[Reset] Failed to seed demo user: {exc}")
        sys.exit(1)

    # 3. Wipe local upload file storage
    print("[Reset] Cleaning local uploaded files folder...")
    upload_dir = REPO_ROOT / "uploads"
    if upload_dir.exists():
        try:
            shutil.rmtree(upload_dir)
            print("[Reset] Uploads directory cleared.")
        except Exception as exc:
            print(f"[Reset] Failed to delete uploads folder (it may be locked): {exc}")

    # 4. Wipe Neo4j Graph DB data
    print("[Reset] Connecting to Neo4j to purge graph nodes...")
    neo4j = Neo4jClient()
    if neo4j.verify_connectivity():
        try:
            with neo4j.get_session() as session:
                session.run("MATCH (n) DETACH DELETE n;")
            print("[Reset] Purged all nodes and relationships in Neo4j.")
        except Exception as exc:
            print(f"[Reset] Neo4j graph purge query failed: {exc}")
    else:
        print("[Reset] Warning: Neo4j server offline or connectivity check failed. Skipping Neo4j purge.")

    print("\n[Reset] Application clean demo environment reset successfully!")


if __name__ == "__main__":
    reset_database()
