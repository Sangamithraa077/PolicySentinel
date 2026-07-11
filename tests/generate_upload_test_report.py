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

from report_lib import REPO_ROOT, overall_status, render_report, run_tests, write_report

REPORT_TITLE = "PolicySentinel — Policy Upload Module Verification Report"
REPORT_FILENAME = "policy_upload_verification_report.txt"

CATEGORIES: list[tuple[str, str]] = [
    ("file_upload", "File upload"),
    ("metadata_storage", "Metadata storage"),
    ("file_retrieval", "File retrieval"),
    ("file_deletion", "File deletion"),
    ("validation", "Validation"),
    ("error_handling", "Error handling"),
]

TEST_PATHS = [REPO_ROOT / "tests" / "backend"]


def main() -> int:
    results, outcomes, _pytest_exit_code = run_tests(TEST_PATHS, CATEGORIES)
    report = render_report(REPORT_TITLE, results, total_tests=len(outcomes))
    print("\n" + report)

    report_path = write_report(report, REPORT_FILENAME)
    print(f"\nReport written to {report_path}")

    return 0 if overall_status(results) != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
