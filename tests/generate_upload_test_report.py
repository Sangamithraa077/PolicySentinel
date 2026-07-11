"""Run the Policy Upload module's test suite and generate a verification
report grouped by the six categories requested for this module:

    File upload, Metadata storage, File retrieval, File deletion,
    Validation, Error handling

These map onto the pytest markers declared in pytest.ini and applied
across tests/backend/{unit,integration,e2e}/. A test may carry more than
one marker (e.g. an oversized-file test is both "validation" and
"error_handling") and will appear under every category it's marked with.

Prints a report to stdout and writes the same report to
backend/logs/policy_upload_verification_report.txt. Exits 0 if every
category is all-PASS, exits 1 otherwise — suitable as a CI gate as well
as an interactive check.

Usage (from the repo root, with backend's dependencies installed):
    python tests/generate_upload_test_report.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"

Status = Literal["PASS", "FAIL", "SKIP"]
_SEVERITY: dict[Status, int] = {"PASS": 0, "SKIP": 1, "FAIL": 2}

_CATEGORIES: list[tuple[str, str]] = [
    ("file_upload", "File upload"),
    ("metadata_storage", "Metadata storage"),
    ("file_retrieval", "File retrieval"),
    ("file_deletion", "File deletion"),
    ("validation", "Validation"),
    ("error_handling", "Error handling"),
]
_CATEGORY_MARKERS = {marker for marker, _ in _CATEGORIES}


@dataclass
class TestOutcome:
    nodeid: str
    outcome: Status
    markers: list[str]
    detail: str | None = None


@dataclass
class CheckResult:
    section: str
    status: Status
    lines: list[str] = field(default_factory=list)


class _UploadTestCollector:
    """pytest plugin: records each test's final outcome plus which of the
    six category markers it carries, keyed by nodeid."""

    def __init__(self) -> None:
        self.markers_by_nodeid: dict[str, list[str]] = {}
        self.outcomes: dict[str, TestOutcome] = {}

    def pytest_collection_modifyitems(self, items: list) -> None:
        for item in items:
            self.markers_by_nodeid[item.nodeid] = [
                marker.name for marker in item.iter_markers() if marker.name in _CATEGORY_MARKERS
            ]

    def pytest_runtest_logreport(self, report) -> None:
        # Only "call" reflects the test itself; "setup" is recorded too,
        # but only when it didn't pass (a fixture error means the test
        # body never ran, so "call" never fires for it) -- this way every
        # collected test gets exactly one recorded outcome.
        if report.when != "call" and not (report.when == "setup" and report.outcome != "passed"):
            return

        if report.outcome == "passed":
            outcome: Status = "PASS"
        elif report.outcome == "skipped":
            outcome = "SKIP"
        else:
            outcome = "FAIL"

        detail = None
        if outcome == "FAIL" and report.longrepr is not None:
            detail = str(report.longrepr).splitlines()[-1][:200]

        self.outcomes[report.nodeid] = TestOutcome(
            nodeid=report.nodeid,
            outcome=outcome,
            markers=self.markers_by_nodeid.get(report.nodeid, []),
            detail=detail,
        )


def _combine(section: str, subchecks: list[tuple[str, Status]]) -> CheckResult:
    overall: Status = "PASS"
    lines = []
    for message, status in subchecks:
        lines.append(f"[{status}] {message}")
        if _SEVERITY[status] > _SEVERITY[overall]:
            overall = status
    return CheckResult(section, overall, lines)


def _category_result(label: str, marker: str, outcomes: list[TestOutcome]) -> CheckResult:
    matching = [o for o in outcomes if marker in o.markers]
    if not matching:
        return CheckResult(label, "FAIL", ["No tests were found for this category."])

    subchecks: list[tuple[str, Status]] = []
    for o in sorted(matching, key=lambda x: x.nodeid):
        short_name = o.nodeid.split("::", 1)[-1]
        message = short_name if o.detail is None else f"{short_name}: {o.detail}"
        subchecks.append((message, o.outcome))
    return _combine(label, subchecks)


def run_tests() -> tuple[list[CheckResult], list[TestOutcome], int]:
    collector = _UploadTestCollector()
    pytest_exit_code = int(
        pytest.main(
            [
                str(REPO_ROOT / "tests" / "backend"),
                "-q",
                "-c",
                str(REPO_ROOT / "pytest.ini"),
                "-p",
                "no:cacheprovider",
            ],
            plugins=[collector],
        )
    )

    outcomes = list(collector.outcomes.values())
    results = [_category_result(label, marker, outcomes) for marker, label in _CATEGORIES]

    uncategorized = [o for o in outcomes if not o.markers]
    if uncategorized:
        lines = [
            f"{o.nodeid.split('::', 1)[-1]}: {o.outcome}"
            for o in sorted(uncategorized, key=lambda x: x.nodeid)
        ]
        results.append(CheckResult("Uncategorized tests (informational)", "PASS", lines))

    # pytest_exit_code 0 = all passed, 1 = some failed (already reflected in
    # the categories above); 2+ means collection/usage/internal problems
    # the category breakdown above wouldn't otherwise surface.
    if pytest_exit_code >= 2:
        results.append(
            CheckResult(
                "Test run",
                "FAIL",
                [f"pytest exited with code {pytest_exit_code} (collection or internal error)"],
            )
        )

    return results, outcomes, pytest_exit_code


def _overall_status(results: list[CheckResult]) -> Status:
    overall: Status = "PASS"
    for result in results:
        if _SEVERITY[result.status] > _SEVERITY[overall]:
            overall = result.status
    return overall


def render_report(results: list[CheckResult], total_tests: int) -> str:
    lines = [
        "PolicySentinel — Policy Upload Module Verification Report",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Total tests executed: {total_tests}",
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
    results, outcomes, _pytest_exit_code = run_tests()
    report = render_report(results, total_tests=len(outcomes))
    print("\n" + report)

    log_dir = BACKEND_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    report_path = log_dir / "policy_upload_verification_report.txt"
    report_path.write_text(report + "\n", encoding="utf-8")
    print(f"\nReport written to {report_path}")

    return 0 if _overall_status(results) != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
