"""Shared machinery for the pytest-based verification report generators
under tests/ (see generate_upload_test_report.py and
generate_clause_pipeline_verification_report.py).

Each generator runs a scoped slice of the suite, groups outcomes by
pytest marker into the named categories it cares about, and renders a
PASS/FAIL report. This module holds the (identical) mechanics; each
generator only supplies its own paths, categories, title, and output
file. Not a test module itself (no test_ prefix) so pytest never
collects it as one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"

Status = Literal["PASS", "FAIL", "SKIP"]
_SEVERITY: dict[Status, int] = {"PASS": 0, "SKIP": 1, "FAIL": 2}


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


class _MarkerCollector:
    """pytest plugin: records each test's final outcome plus which of
    `category_markers` it carries, keyed by nodeid."""

    def __init__(self, category_markers: set[str]) -> None:
        self.category_markers = category_markers
        self.markers_by_nodeid: dict[str, list[str]] = {}
        self.outcomes: dict[str, TestOutcome] = {}

    def pytest_collection_modifyitems(self, items: list) -> None:
        for item in items:
            self.markers_by_nodeid[item.nodeid] = [
                marker.name
                for marker in item.iter_markers()
                if marker.name in self.category_markers
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


def run_tests(
    test_paths: list[Path], categories: list[tuple[str, str]]
) -> tuple[list[CheckResult], list[TestOutcome], int]:
    """Runs pytest over `test_paths`, then groups outcomes by the
    (marker, label) pairs in `categories`. A test can carry more than
    one category marker and will appear under every category it's
    tagged with."""
    category_markers = {marker for marker, _ in categories}
    collector = _MarkerCollector(category_markers)
    pytest_exit_code = int(
        pytest.main(
            [
                *(str(path) for path in test_paths),
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
    results = [_category_result(label, marker, outcomes) for marker, label in categories]

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


def overall_status(results: list[CheckResult]) -> Status:
    overall: Status = "PASS"
    for result in results:
        if _SEVERITY[result.status] > _SEVERITY[overall]:
            overall = result.status
    return overall


def render_report(title: str, results: list[CheckResult], total_tests: int) -> str:
    lines = [
        title,
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Total tests executed: {total_tests}",
        "=" * 64,
    ]
    for result in results:
        lines.append("")
        lines.append(f"[{result.status}] {result.section}")
        lines.extend(f"    {line}" for line in result.lines)

    lines.append("")
    lines.append("=" * 64)
    lines.append(f"Overall: {overall_status(results)}")
    return "\n".join(lines)


def write_report(report: str, filename: str) -> Path:
    log_dir = BACKEND_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    report_path = log_dir / filename
    report_path.write_text(report + "\n", encoding="utf-8")
    return report_path
