#!/usr/bin/env python3
"""
Example: Coverage Collector Demo

Demonstrates how to collect and report test coverage metrics using
the APGI Framework's coverage utilities.

Usage:
    python examples/coverage_collector_demo.py
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def collect_module_coverage(root: Path):
    """Walk project source and count .py files vs __pycache__."""
    total_py = 0
    covered = 0
    uncovered = []

    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts or ".git" in path.parts:
            continue
        if path.name.startswith("test_"):
            continue
        total_py += 1
        # Heuristic: check if a corresponding test file exists
        possible_test = root / "tests" / f"test_{path.name}"
        if possible_test.exists():
            covered += 1
        else:
            uncovered.append(path.relative_to(root))

    return total_py, covered, uncovered


def print_coverage_report(total, covered, uncovered):
    pct = (covered / total * 100) if total else 0
    bar_len = 40
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)

    print(f"\n  Coverage: [{bar}] {pct:.1f}%")
    print(f"  Modules total : {total}")
    print(f"  Covered       : {covered}")
    print(f"  Uncovered     : {total - covered}")

    if uncovered:
        print("\n  Top uncovered modules (first 10):")
        for p in uncovered[:10]:
            print(f"    • {p}")


def main():
    print("=" * 60)
    print("APGI Framework — Coverage Collector Demo")
    print("=" * 60)

    print("\nScanning project for source modules...")
    start = time.time()
    total, covered, uncovered = collect_module_coverage(PROJECT_ROOT)
    elapsed = time.time() - start

    print_coverage_report(total, covered, uncovered)
    print(f"\nScan completed in {elapsed:.3f}s")
    print("\nCoverage collector demo complete.")


if __name__ == "__main__":
    main()
