#!/usr/bin/env python3
"""
Clean coverage files to prevent SQLite database corruption.

Run this before pytest to ensure clean coverage state:
    python utils/clean_coverage.py
    python -m pytest

Or use the combined command:
    python utils/clean_coverage.py && python -m pytest
"""

import shutil
import sys
from pathlib import Path


def clean_coverage_files():
    """Remove all coverage-related files to prevent DB corruption."""
    project_root = Path(__file__).parent.parent
    files_to_remove = [
        ".coverage",
        ".coverage.*",  # Parallel coverage files
        "coverage.json",
        "coverage.xml",
    ]
    dirs_to_remove = [
        "htmlcov",
        ".pytest_cache",
    ]

    removed = []

    # Remove files
    for pattern in files_to_remove:
        if "*" in pattern:
            # Handle glob patterns
            for path in project_root.glob(pattern):
                try:
                    path.unlink()
                    removed.append(str(path.relative_to(project_root)))
                except OSError as e:
                    print(f"Warning: Could not remove {path}: {e}")
        else:
            path = project_root / pattern
            if path.exists():
                try:
                    path.unlink()
                    removed.append(pattern)
                except OSError as e:
                    print(f"Warning: Could not remove {path}: {e}")

    # Remove directories
    for dirname in dirs_to_remove:
        path = project_root / dirname
        if path.exists():
            try:
                shutil.rmtree(path)
                removed.append(f"{dirname}/")
            except OSError as e:
                print(f"Warning: Could not remove {path}: {e}")

    if removed:
        print(f"Cleaned coverage files: {', '.join(removed)}")
    else:
        print("No coverage files to clean")

    return len(removed)


if __name__ == "__main__":
    count = clean_coverage_files()
    sys.exit(0 if count >= 0 else 1)
