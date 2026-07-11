"""Run the parsing/clause-segmentation pipeline's test suite and generate
a verification report grouped by the six categories requested for this
pipeline:

    Document parsing, Text normalization, Clause segmentation,
    Clause ordering, Database storage, API responses

These map onto the pytest markers declared in pytest.ini and applied
across the pipeline's test files (see TEST_PATHS below — scoped to just
those files, not the whole suite, so this report stays specific to
"the parsing and clause segmentation pipeline" rather than picking up
unrelated policy-upload tests that happen to share a marker name). A
test may carry more than one marker (e.g. a clause-repository ordering
test is both "metadata_storage" and "clause_ordering") and will appear
under every category it's marked with.

Prints a report to stdout and writes the same report to
backend/logs/clause_pipeline_verification_report.txt. Exits 0 if every
category is all-PASS, exits 1 otherwise — suitable as a CI gate as well
as an interactive check.

Usage (from the repo root, with backend's dependencies installed):
    python tests/generate_clause_pipeline_verification_report.py
"""

from __future__ import annotations

import sys

from report_lib import REPO_ROOT, overall_status, render_report, run_tests, write_report

REPORT_TITLE = "PolicySentinel — Parsing & Clause Segmentation Pipeline Verification Report"
REPORT_FILENAME = "clause_pipeline_verification_report.txt"

CATEGORIES: list[tuple[str, str]] = [
    ("text_extraction", "Document parsing"),
    ("text_normalization", "Text normalization"),
    ("clause_segmentation", "Clause segmentation"),
    ("clause_ordering", "Clause ordering"),
    ("metadata_storage", "Database storage"),
    ("api_response", "API responses"),
]

_BACKEND_TESTS = REPO_ROOT / "tests" / "backend"
TEST_PATHS = [
    _BACKEND_TESTS / "unit" / "test_document_parsing_service.py",
    _BACKEND_TESTS / "unit" / "test_text_normalization_service.py",
    _BACKEND_TESTS / "unit" / "test_clause_segmentation_service.py",
    _BACKEND_TESTS / "unit" / "test_store_segmented_clauses_service.py",
    _BACKEND_TESTS / "unit" / "test_clause_management_service.py",
    _BACKEND_TESTS / "integration" / "test_clause_repository.py",
    _BACKEND_TESTS / "e2e" / "test_clauses_e2e.py",
    _BACKEND_TESTS / "e2e" / "test_clause_pipeline_e2e.py",
]


def main() -> int:
    results, outcomes, _pytest_exit_code = run_tests(TEST_PATHS, CATEGORIES)
    report = render_report(REPORT_TITLE, results, total_tests=len(outcomes))
    print("\n" + report)

    report_path = write_report(report, REPORT_FILENAME)
    print(f"\nReport written to {report_path}")

    return 0 if overall_status(results) != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
