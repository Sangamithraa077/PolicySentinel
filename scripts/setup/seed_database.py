"""Seed the PostgreSQL database with representative sample data for local
development — enough to exercise every relationship in the domain model
(company scoping, department hierarchy, policy versioning/supersession)
without yet touching the extraction-pipeline entities.

Inserts:
    2  Companies
    5  Departments   (one parent/child pair, to exercise the hierarchy)
    5  Users         (one of each `UserRole`)
    6  Policies
    12 PolicyVersions (2 per policy — v1 superseded by v2)
    3  RegulatoryFrameworks
    7  RegulatoryClauses

Deliberately does NOT insert Clauses, Obligations, or Findings — those
depend on the (not-yet-implemented) extraction pipeline and belong in a
follow-up seed script.

Idempotent: if the seed companies already exist, the script prints a
message and exits without changing anything, rather than duplicating
rows or wiping existing data.

Usage (from the repo root, with backend's dependencies installed):
    python scripts/setup/seed_database.py
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Running as a plain script (not a package), so make backend/'s modules
# importable the same way `alembic` and `main:app` already assume —
# rooted at backend/, not the repo root.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import bcrypt  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from database.session import SessionLocal  # noqa: E402
from models.company import Company  # noqa: E402
from models.department import Department  # noqa: E402
from models.enums import PolicyStatus, PolicyVersionStatus, UserRole  # noqa: E402
from models.policy import Policy  # noqa: E402
from models.policy_version import PolicyVersion  # noqa: E402
from models.regulatory_clause import RegulatoryClause  # noqa: E402
from models.regulatory_framework import RegulatoryFramework  # noqa: E402
from models.user import User  # noqa: E402

# Dev-only shared password for every seeded user. This has no bearing on
# any production path — there is no seed data outside a local/dev
# database, and nothing here is ever run against a real environment.
_DEV_PASSWORD = "ChangeMe123!"


def _hash_password(password: str) -> str:
    # Hashed directly with `bcrypt` rather than through passlib's
    # CryptContext: passlib 1.7.4's bcrypt backend-detection self-test is
    # incompatible with bcrypt>=4.1 (a known interop break, unrelated to
    # this project) and raises on the very first hash() call. auth/ can
    # still use passlib for its multi-scheme abstraction later; this is
    # a one-off dev seed hash, so the direct dependency is simpler anyway.
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def _fake_file_hash(seed_text: str) -> str:
    """A stand-in for a real uploaded file's checksum — deterministic, not random."""
    return hashlib.sha256(seed_text.encode("utf-8")).hexdigest()


def _days_ago(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


@dataclass
class SeedObjects:
    companies: list[Company] = field(default_factory=list)
    departments: list[Department] = field(default_factory=list)
    users: list[User] = field(default_factory=list)
    policies: list[Policy] = field(default_factory=list)
    policy_versions: list[PolicyVersion] = field(default_factory=list)
    regulatory_frameworks: list[RegulatoryFramework] = field(default_factory=list)
    regulatory_clauses: list[RegulatoryClause] = field(default_factory=list)


def build_seed_objects() -> SeedObjects:
    """Construct the full in-memory object graph (no session/DB access).

    Kept separate from `seed()` so the object graph itself — counts,
    relationships, enum coverage — can be inspected or unit-tested
    without a database connection.
    """
    seed = SeedObjects()

    # ================================================================= companies
    northbridge = Company(
        name="Northbridge Financial Group",
        industry="Banking",
        jurisdiction="United States",
        registration_number="NFG-100234",
    )
    solane = Company(
        name="Solane Insurance Holdings",
        industry="Insurance",
        jurisdiction="European Union",
        registration_number="SIH-887701",
    )
    seed.companies = [northbridge, solane]

    # =============================================================== departments
    compliance = Department(
        company=northbridge, name="Compliance", code="COMP", description="Group compliance function"
    )
    regulatory_affairs = Department(
        company=northbridge,
        name="Regulatory Affairs",
        code="COMP-REG",
        description="Reports into Compliance; owns regulator-facing filings",
        parent=compliance,
    )
    risk_management = Department(
        company=northbridge,
        name="Risk Management",
        code="RISK",
        description="Credit and operational risk oversight",
    )
    legal_compliance = Department(
        company=solane,
        name="Legal & Compliance",
        code="LEGAL",
        description="Legal and regulatory compliance",
    )
    underwriting = Department(
        company=solane, name="Underwriting", code="UW", description="Policy underwriting standards"
    )
    seed.departments = [
        compliance,
        regulatory_affairs,
        risk_management,
        legal_compliance,
        underwriting,
    ]

    # ===================================================================== users
    admin = User(
        company=northbridge,
        department=None,
        email="ava.thornton@northbridge-fg.com",
        password_hash=_hash_password(_DEV_PASSWORD),
        full_name="Ava Thornton",
        role=UserRole.ADMIN,
    )
    compliance_officer = User(
        company=northbridge,
        department=compliance,
        email="marcus.webb@northbridge-fg.com",
        password_hash=_hash_password(_DEV_PASSWORD),
        full_name="Marcus Webb",
        role=UserRole.COMPLIANCE_OFFICER,
    )
    department_head = User(
        company=northbridge,
        department=risk_management,
        email="priya.nair@northbridge-fg.com",
        password_hash=_hash_password(_DEV_PASSWORD),
        full_name="Priya Nair",
        role=UserRole.DEPARTMENT_HEAD,
    )
    auditor = User(
        company=solane,
        department=legal_compliance,
        email="elena.rossi@solane-insurance.eu",
        password_hash=_hash_password(_DEV_PASSWORD),
        full_name="Elena Rossi",
        role=UserRole.AUDITOR,
    )
    viewer = User(
        company=solane,
        department=underwriting,
        email="tom.becker@solane-insurance.eu",
        password_hash=_hash_password(_DEV_PASSWORD),
        full_name="Tom Becker",
        role=UserRole.VIEWER,
    )
    seed.users = [admin, compliance_officer, department_head, auditor, viewer]

    # ================================================================== policies
    # (title, code, category, department, status, uploader)
    policy_specs = [
        (
            "Anti-Money Laundering Policy",
            "POL-AML-001",
            "AML/CFT",
            compliance,
            PolicyStatus.ACTIVE,
            compliance_officer,
        ),
        (
            "Data Retention and Privacy Policy",
            "POL-PRIV-002",
            "Data Protection",
            regulatory_affairs,
            PolicyStatus.ACTIVE,
            compliance_officer,
        ),
        (
            "Credit Risk Management Policy",
            "POL-RISK-003",
            "Risk Management",
            risk_management,
            PolicyStatus.ACTIVE,
            department_head,
        ),
        (
            "Third-Party Vendor Risk Policy",
            "POL-VEND-004",
            "Vendor Management",
            risk_management,
            PolicyStatus.DRAFT,
            department_head,
        ),
        (
            "Underwriting Guidelines Policy",
            "POL-UW-005",
            "Underwriting",
            underwriting,
            PolicyStatus.ACTIVE,
            auditor,
        ),
        (
            "Claims Handling and Conduct Policy",
            "POL-CLM-006",
            "Conduct Risk",
            legal_compliance,
            PolicyStatus.ACTIVE,
            auditor,
        ),
    ]

    for title, code, category, department, status, uploader in policy_specs:
        policy = Policy(
            company=department.company,
            owning_department=department,
            title=title,
            policy_code=code,
            category=category,
            status=status,
        )
        seed.policies.append(policy)

        v1 = PolicyVersion(
            policy=policy,
            version_number=1,
            source_file_reference=f"uploads/policies/{code.lower()}-v1.pdf",
            file_hash=_fake_file_hash(f"{code}-v1"),
            uploaded_by=uploader,
            status=PolicyVersionStatus.SUPERSEDED,
            effective_date=date.today() - timedelta(days=380),
            ai_summary=f"Initial published version of the {title.lower()}.",
            uploaded_at=_days_ago(380),
        )
        v2_status = (
            PolicyVersionStatus.UNDER_REVIEW
            if status == PolicyStatus.DRAFT
            else PolicyVersionStatus.PUBLISHED
        )
        v2 = PolicyVersion(
            policy=policy,
            version_number=2,
            source_file_reference=f"uploads/policies/{code.lower()}-v2.pdf",
            file_hash=_fake_file_hash(f"{code}-v2"),
            uploaded_by=uploader,
            status=v2_status,
            effective_date=date.today() - timedelta(days=14),
            ai_summary=f"Revised version of the {title.lower()}, incorporating the latest regulatory guidance.",
            uploaded_at=_days_ago(14),
        )
        v1.superseded_by = v2
        policy.current_version = v2

        seed.policy_versions.extend([v1, v2])

    # ==================================================== regulatory frameworks
    gdpr = RegulatoryFramework(
        name="General Data Protection Regulation",
        jurisdiction="European Union",
        issuing_body="European Parliament and Council",
        edition_or_version="Regulation (EU) 2016/679",
        effective_date=date(2018, 5, 25),
        description="EU framework governing the processing of personal data.",
    )
    bsa_aml = RegulatoryFramework(
        name="Bank Secrecy Act / Anti-Money Laundering",
        jurisdiction="United States",
        issuing_body="FinCEN, U.S. Department of the Treasury",
        edition_or_version="31 U.S.C. § 5311 et seq.",
        effective_date=date(1970, 10, 26),
        description="U.S. framework requiring AML programs, recordkeeping, and reporting.",
    )
    basel_iii = RegulatoryFramework(
        name="Basel III: International Regulatory Framework for Banks",
        jurisdiction="International (Basel Committee)",
        issuing_body="Basel Committee on Banking Supervision",
        edition_or_version="Basel III finalization (2017)",
        effective_date=date(2023, 1, 1),
        description="International capital adequacy, stress testing, and liquidity standards.",
    )
    seed.regulatory_frameworks = [gdpr, bsa_aml, basel_iii]

    clause_specs = [
        (gdpr, "Art. 5", "Principles relating to processing of personal data", "Data Protection"),
        (gdpr, "Art. 17", "Right to erasure ('right to be forgotten')", "Data Protection"),
        (gdpr, "Art. 32", "Security of processing", "Data Protection"),
        (bsa_aml, "31 CFR 1020.210", "Customer Identification Program requirements", "AML/CFT"),
        (bsa_aml, "31 CFR 1010.311", "Currency transaction reporting", "AML/CFT"),
        (basel_iii, "Basel III Part 2", "Minimum capital requirements", "Capital Adequacy"),
        (basel_iii, "Basel III Part 4", "Liquidity Coverage Ratio requirement", "Liquidity"),
    ]
    for framework, reference, title, category in clause_specs:
        seed.regulatory_clauses.append(
            RegulatoryClause(
                framework=framework,
                clause_reference=reference,
                title=title,
                text=f"See {framework.name} ({reference}): {title}.",
                category=category,
            )
        )

    return seed


def seed(session: Session) -> SeedObjects | None:
    """Insert the seed data if it isn't already present. Returns the
    inserted objects, or None if seeding was skipped."""
    already_seeded = (
        session.query(Company).filter(Company.registration_number == "NFG-100234").first()
    )
    if already_seeded is not None:
        print("Seed data already present (Northbridge Financial Group found) — skipping.")
        return None

    objects = build_seed_objects()
    session.add_all(objects.companies)
    session.add_all(objects.regulatory_frameworks)
    # Departments/users/policies/policy_versions/regulatory_clauses all
    # cascade in via their relationships to the objects above.
    session.commit()
    return objects


def main() -> None:
    session = SessionLocal()
    try:
        objects = seed(session)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    if objects is None:
        return

    print(
        "Seed complete: "
        f"{len(objects.companies)} companies, "
        f"{len(objects.departments)} departments, "
        f"{len(objects.users)} users, "
        f"{len(objects.policies)} policies, "
        f"{len(objects.policy_versions)} policy versions, "
        f"{len(objects.regulatory_frameworks)} regulatory frameworks, "
        f"{len(objects.regulatory_clauses)} regulatory clauses."
    )
    print(f"Dev login password for every seeded user: {_DEV_PASSWORD}")


if __name__ == "__main__":
    main()
