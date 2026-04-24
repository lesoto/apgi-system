#!/usr/bin/env python3
"""
Coverage analysis and reporting script for APGI system.

This script runs pytest with coverage, generates reports, and provides
detailed analysis of coverage gaps.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def run_tests_with_coverage() -> int:
    """
    Run pytest with coverage measurement.

    Returns
    -------
    int
        Exit code from pytest (0 = success, non-zero = failure).
    """
    print("=" * 80)
    print("Running tests with coverage measurement...")
    print("=" * 80)

    cmd = [
        "pytest",
        "tests/",
        "-v",
        "--timeout=30",
        "-n",
        "auto",
        "--ignore=tests/integration/test_integration_properties.py",
        "--cov=apgi_framework",
        "--cov=api",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-report=json:coverage.json",
        "--cov-report=xml:coverage.xml",
    ]

    result = subprocess.run(cmd, timeout=600)
    return result.returncode


def analyze_coverage_gaps() -> Tuple[List[Dict[str, Any]], float]:
    """
    Analyze coverage.json to identify gaps.

    Returns
    -------
    tuple
        (list of gap dictionaries, overall coverage percentage)
    """
    coverage_file = Path("coverage.json")

    if not coverage_file.exists():
        print("Warning: coverage.json not found. Run tests first.")
        return [], 0.0

    with open(coverage_file, "r") as f:
        data = json.load(f)

    gaps = []
    total_statements = 0
    covered_statements = 0

    for filename, file_data in data["files"].items():
        # Skip test files and GUI files
        if "test_" in filename or "_GUI" in filename or "apgi_gui" in filename:
            continue

        summary = file_data["summary"]
        total_statements += summary["num_statements"]
        covered_statements += summary["covered_lines"]

        if summary["percent_covered"] < 100:
            missing_lines = file_data.get("missing_lines", [])
            gaps.append(
                {
                    "file": filename,
                    "coverage": summary["percent_covered"],
                    "missing_lines": missing_lines,
                    "num_missing": len(missing_lines),
                }
            )

    overall_coverage = (covered_statements / total_statements * 100) if total_statements > 0 else 0

    return gaps, overall_coverage


def print_coverage_report(gaps: List[Dict[str, Any]], overall_coverage: float) -> None:
    """
    Print a formatted coverage gap report.

    Parameters
    ----------
    gaps : list
        List of coverage gap dictionaries.
    overall_coverage : float
        Overall coverage percentage.
    """
    print("\n" + "=" * 80)
    print("COVERAGE ANALYSIS REPORT")
    print("=" * 80)
    print(f"\nOverall Coverage: {overall_coverage:.2f}%")
    print("Target Coverage: 100.00%")
    print(f"Gap: {100 - overall_coverage:.2f}%\n")

    if not gaps:
        print("✓ Congratulations! 100% coverage achieved!")
        return

    print(f"Files with coverage gaps: {len(gaps)}\n")

    # Sort by number of missing lines (descending)
    gaps.sort(key=lambda x: x["num_missing"], reverse=True)

    for i, gap in enumerate(gaps, 1):
        print(f"{i}. {gap['file']}")
        print(f"   Coverage: {gap['coverage']:.2f}%")
        print(f"   Missing lines: {gap['num_missing']}")

        # Show first 10 missing lines
        missing = gap["missing_lines"][:10]
        if missing:
            print(f"   Lines: {', '.join(map(str, missing))}", end="")
            if len(gap["missing_lines"]) > 10:
                print(f" ... and {len(gap['missing_lines']) - 10} more")
            else:
                print()
        print()


def generate_html_report() -> None:
    """Generate and open HTML coverage report."""
    print("=" * 80)
    print("Generating HTML coverage report...")
    print("=" * 80)

    html_index = Path("htmlcov/index.html")
    if html_index.exists():
        print(f"\n✓ HTML report generated: {html_index.absolute()}")
        print("  Open this file in a browser to view detailed coverage.")
    else:
        print("\n✗ HTML report not found.")


def main() -> int:
    """Main entry point for coverage analysis."""
    print("\n" + "=" * 80)
    print("APGI SYSTEM - COMPREHENSIVE COVERAGE ANALYSIS")
    print("=" * 80 + "\n")

    # Run tests with coverage
    exit_code = run_tests_with_coverage()

    # Analyze gaps
    gaps, overall_coverage = analyze_coverage_gaps()

    # Print report
    print_coverage_report(gaps, overall_coverage)

    # Generate HTML report
    generate_html_report()

    # Summary
    print("\n" + "=" * 80)
    if exit_code == 0 and overall_coverage >= 100:
        print("✓ SUCCESS: All tests passed with 100% coverage!")
        print("=" * 80 + "\n")
        return 0
    elif exit_code == 0:
        print(f"⚠ PARTIAL SUCCESS: Tests passed but coverage is {overall_coverage:.2f}%")
        print("=" * 80 + "\n")
        return 1
    else:
        print("✗ FAILURE: Some tests failed or coverage below 100%")
        print("=" * 80 + "\n")
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
