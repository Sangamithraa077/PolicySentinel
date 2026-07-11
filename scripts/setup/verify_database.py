"""Verify a PostgreSQL database is correctly set up for PolicySentinel.

Checks, in order:
    1. Database connectivity
    2. Migration status     (DB's stamped Alembic revision vs. the latest script)
    3. Table creation       (every model-backed table actually exists)
    4. Relationships        (expected FK constraints exist + a handful of
                              seeded relationships resolve correctly)
    5. Seed data            (expected seed rows from scripts/setup/seed_database.py
                              are present)

Each check degrades gracefully rather than crashing: if the database is
unreachable, every later check is reported as SKIPPED (not FAILED) with
the reason why, and if a specific seed row a relationship check depends
on isn't there, that check is SKIPPED rather than reported as a broken
relationship.

Prints a report to stdout and writes the same report to
backend/logs/db_verification_report.txt. Exits 0 if every check is
PASS/WARN/SKIP, exits 1 if any check FAILs — suitable as a CI/pre-flight
gate as well as an interactive sanity check.

Usage (from the repo root, with backend's dependencies installed):
    python scripts/setup/verify_database.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

# Running as a plain script (not a package), so make the `backend` package
# importable the same way `alembic` and `backend.main:app` already assume —
# rooted at the repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from alembic.config import Config  # noqa: E402
from alembic.runtime.migration import MigrationContext  # noqa: E402
from alembic.script import ScriptDirectory  # noqa: E402
from sqlalchemy import func, inspect, select, text  # noqa: E402
from sqlalchemy.engine import Inspector  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import backend.models  # noqa: E402,F401 -- import populates Base.metadata as a side effect
from backend.database.base import Base  # noqa: E402
from backend.database.session import SessionLocal, engine  # noqa: E402
from backend.models.clause import Clause  # noqa: E402
from backend.models.company import Company  # noqa: E402
from backend.models.department import Department  # noqa: E402
from backend.models.finding import Finding  # noqa: E402
from backend.models.obligation import Obligation  # noqa: E402
from backend.models.policy import Policy  # noqa: E402
from backend.models.policy_version import PolicyVersion  # noqa: E402
from backend.models.regulatory_clause import RegulatoryClause  # noqa: E402
from backend.models.regulatory_framework import RegulatoryFramework  # noqa: E402
from backend.models.user import User  # noqa: E402

Status = Literal["PASS", "WARN", "FAIL", "SKIP"]
_SEVERITY: dict[Status, int] = {"PASS": 0, "SKIP": 1, "WARN": 2, "FAIL": 3}


@dataclass
class CheckResult:
    section: str
    status: Status
    lines: list[str] = field(default_factory=list)


def _combine(section: str, subchecks: list[tuple[str, Status]]) -> CheckResult:
    """Fold a list of (message, status) sub-checks into one section result —
    the section's overall status is the worst of its sub-checks."""
    overall: Status = "PASS"
    lines = []
    for message, status in subchecks:
        lines.append(f"[{status}] {message}")
        if _SEVERITY[status] > _SEVERITY[overall]:
            overall = status
    return CheckResult(section, overall, lines)


# ============================================================= 1. connectivity
def check_connectivity() -> CheckResult:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return CheckResult("Database connectivity", "FAIL", [f"Could not connect: {exc}"])

    safe_url = engine.url.render_as_string(hide_password=True)
    return CheckResult("Database connectivity", "PASS", [f"Connected to {safe_url}"])


# =========================================================== 2. migration status
def check_migration_status() -> CheckResult:
    try:
        alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        head_revision = script_dir.get_current_head()

        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_revision = context.get_current_revision()
    except Exception as exc:  # alembic raises a variety of its own error types
        return CheckResult(
            "Migration status", "FAIL", [f"Could not determine migration status: {exc}"]
        )

    lines = [
        f"Latest migration script:      {head_revision}",
        f"Revision stamped in database: {current_revision}",
    ]
    if current_revision is None:
        lines.append("No migrations have been applied — run `alembic upgrade head`.")
        return CheckResult("Migration status", "FAIL", lines)
    if current_revision != head_revision:
        lines.append("Database is behind the latest migration — run `alembic upgrade head`.")
        return CheckResult("Migration status", "FAIL", lines)
    return CheckResult("Migration status", "PASS", lines)


# ============================================================== 3. table creation
_AUXILIARY_TABLES = {"alembic_version"}


def check_tables() -> CheckResult:
    try:
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
    except SQLAlchemyError as exc:
        return CheckResult("Table creation", "FAIL", [f"Could not inspect database: {exc}"])

    expected = set(Base.metadata.tables.keys())
    missing = sorted(expected - existing)
    unexpected = sorted(existing - expected - _AUXILIARY_TABLES)

    lines = [f"{len(expected & existing)}/{len(expected)} expected tables present."]
    if missing:
        lines.append(f"Missing: {', '.join(missing)}")
    if unexpected:
        lines.append(
            f"Unrecognized tables present (not necessarily a problem): {', '.join(unexpected)}"
        )

    if missing:
        return CheckResult("Table creation", "FAIL", lines)
    if unexpected:
        return CheckResult("Table creation", "WARN", lines)
    return CheckResult("Table creation", "PASS", lines)


# ================================================================ 4. relationships
FKTuple = tuple[str, tuple[str, ...], str]


def _expected_foreign_keys() -> set[FKTuple]:
    expected: set[FKTuple] = set()
    for table_name, table in Base.metadata.tables.items():
        for fk_constraint in table.foreign_key_constraints:
            local_columns = tuple(sorted(column.name for column in fk_constraint.columns))
            expected.add((table_name, local_columns, fk_constraint.referred_table.name))
    return expected


def _actual_foreign_keys(inspector: Inspector) -> set[FKTuple]:
    actual: set[FKTuple] = set()
    for table_name in inspector.get_table_names():
        for fk in inspector.get_foreign_keys(table_name):
            local_columns = tuple(sorted(fk["constrained_columns"]))
            actual.add((table_name, local_columns, fk["referred_table"]))
    return actual


def _check_foreign_keys() -> tuple[str, Status]:
    try:
        inspector = inspect(engine)
        expected = _expected_foreign_keys()
        actual = _actual_foreign_keys(inspector)
    except SQLAlchemyError as exc:
        return (f"Could not inspect foreign keys: {exc}", "FAIL")

    missing = expected - actual
    if missing:
        described = ", ".join(f"{table}.{cols} -> {ref}" for table, cols, ref in sorted(missing))
        return (
            f"{len(expected) - len(missing)}/{len(expected)} expected foreign keys present; missing: {described}",
            "FAIL",
        )
    return (f"All {len(expected)} expected foreign key constraints are present", "PASS")


def _check_department_hierarchy(session: Session) -> tuple[str, Status]:
    label = "Department hierarchy (Regulatory Affairs reports to Compliance)"
    dept = session.scalar(select(Department).where(Department.name == "Regulatory Affairs"))
    if dept is None:
        return (f"{label}: seed department not found", "SKIP")
    if dept.parent is not None and dept.parent.name == "Compliance":
        return (f"{label}: resolved correctly", "PASS")
    return (f"{label}: parent_department_id does not resolve to Compliance", "FAIL")


def _check_policy_supersession(session: Session) -> tuple[str, Status]:
    label = "Policy version supersession (POL-AML-001 v1 superseded by v2)"
    policy = session.scalar(select(Policy).where(Policy.policy_code == "POL-AML-001"))
    if policy is None or policy.current_version is None:
        return (f"{label}: seed policy or its current version not found", "SKIP")
    if policy.current_version.version_number != 2:
        return (f"{label}: current_version is not version 2", "FAIL")
    v1 = session.scalar(
        select(PolicyVersion).where(
            PolicyVersion.policy_id == policy.id, PolicyVersion.version_number == 1
        )
    )
    if v1 is None:
        return (f"{label}: version 1 not found", "SKIP")
    if v1.superseded_by_version_id == policy.current_version.id:
        return (f"{label}: resolved correctly", "PASS")
    return (f"{label}: v1.superseded_by_version_id does not point at the current version", "FAIL")


def _check_regulatory_clause_link(session: Session) -> tuple[str, Status]:
    label = "Regulatory clause -> framework (Art. 17 -> GDPR)"
    clause = session.scalar(
        select(RegulatoryClause).where(RegulatoryClause.clause_reference == "Art. 17")
    )
    if clause is None:
        return (f"{label}: seed clause not found", "SKIP")
    if clause.framework is not None and "General Data Protection" in clause.framework.name:
        return (f"{label}: resolved correctly", "PASS")
    return (f"{label}: regulatory_framework_id does not resolve to GDPR", "FAIL")


def _check_user_scoping(session: Session) -> tuple[str, Status]:
    label = "User -> company/department (Marcus Webb -> Northbridge/Compliance)"
    user = session.scalar(select(User).where(User.email == "marcus.webb@northbridge-fg.com"))
    if user is None:
        return (f"{label}: seed user not found", "SKIP")
    if (
        user.company is not None
        and user.department is not None
        and user.department.name == "Compliance"
    ):
        return (f"{label}: resolved correctly", "PASS")
    return (f"{label}: company_id/department_id do not resolve as expected", "FAIL")


def check_relationships(session: Session) -> CheckResult:
    subchecks = [
        _check_foreign_keys(),
        _check_department_hierarchy(session),
        _check_policy_supersession(session),
        _check_regulatory_clause_link(session),
        _check_user_scoping(session),
    ]
    return _combine("Relationships", subchecks)


# =================================================================== 5. seed data
def check_seed_data(session: Session) -> CheckResult:
    subchecks: list[tuple[str, Status]] = []

    minimum_counts = [
        (Company, 2, "Companies"),
        (Department, 5, "Departments"),
        (User, 5, "Users"),
        (Policy, 6, "Policies"),
        (PolicyVersion, 12, "Policy versions"),
        (RegulatoryFramework, 3, "Regulatory frameworks"),
        (RegulatoryClause, 7, "Regulatory clauses"),
    ]
    for model, minimum, label in minimum_counts:
        count = session.scalar(select(func.count()).select_from(model)) or 0
        status: Status = "PASS" if count >= minimum else "FAIL"
        subchecks.append((f"{label}: {count} present (expected at least {minimum})", status))

    known_markers = [
        (Company.registration_number == "NFG-100234", "Northbridge Financial Group"),
        (Company.registration_number == "SIH-887701", "Solane Insurance Holdings"),
    ]
    for condition, label in known_markers:
        found = session.scalar(select(Company).where(condition)) is not None
        subchecks.append((f"Seed marker present: {label}", "PASS" if found else "FAIL"))

    # Informational: these entities are intentionally not part of this seed
    # script yet (see scripts/setup/seed_database.py) — a non-zero count
    # here isn't wrong, just worth surfacing rather than silently ignoring.
    for model, label in [(Clause, "Clauses"), (Obligation, "Obligations"), (Finding, "Findings")]:
        count = session.scalar(select(func.count()).select_from(model)) or 0
        pipeline_status: Status = "PASS" if count == 0 else "WARN"
        subchecks.append(
            (
                f"{label}: {count} present (not seeded yet by design; 0 expected for now)",
                pipeline_status,
            )
        )

    return _combine("Seed data", subchecks)


# ======================================================================= runner
def run_all_checks() -> list[CheckResult]:
    results = [check_connectivity()]
    if results[0].status == "FAIL":
        for section in ("Migration status", "Table creation", "Relationships", "Seed data"):
            results.append(CheckResult(section, "SKIP", ["Skipped — database is unreachable."]))
        return results

    results.append(check_migration_status())
    results.append(check_tables())

    session = SessionLocal()
    try:
        results.append(check_relationships(session))
        results.append(check_seed_data(session))
    finally:
        session.close()

    return results


def _overall_status(results: list[CheckResult]) -> Status:
    overall: Status = "PASS"
    for result in results:
        if _SEVERITY[result.status] > _SEVERITY[overall]:
            overall = result.status
    return overall


def render_report(results: list[CheckResult]) -> str:
    lines = [
        "PolicySentinel — Database Verification Report",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "=" * 64,
    ]
    for result in results:
        lines.append("")
        lines.append(f"[{result.status}] {result.section}")
        lines.extend(f"    {line}" for line in result.lines)

    lines.append("")
    lines.append("=" * 64)
    lines.append(f"Overall: {_overall_status(results)}")
    return "\n".join(lines)


def main() -> int:
    results = run_all_checks()
    report = render_report(results)
    print(report)

    log_dir = BACKEND_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    report_path = log_dir / "db_verification_report.txt"
    report_path.write_text(report + "\n", encoding="utf-8")
    print(f"\nReport written to {report_path}")

    return 0 if _overall_status(results) != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
