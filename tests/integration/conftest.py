"""
Pytest configuration for integration tests.

Configures hypothesis to avoid issues with changing working directories.
"""

import os
from pathlib import Path

# Configure hypothesis to avoid CWD issues
# The hypothesis plugin fails when trying to report failures if CWD changes
os.environ.setdefault("HYPOTHESIS_NO_DIFF", "1")

# Store original CWD at module load time for restoration
_original_cwd = Path.cwd()


def pytest_configure(config):
    """Configure pytest and hypothesis for integration tests."""
    # Disable hypothesis artifact generation that causes CWD issues
    try:
        from hypothesis import settings

        # Register a profile that disables diff generation
        settings.register_profile(
            "no_cwd_issues",
            print_blob=False,
            deadline=None,
        )
        settings.load_profile("no_cwd_issues")
    except ImportError:
        pass


def pytest_runtest_setup(item):
    """Store original CWD before each test."""
    # Store in environment for access during test
    os.environ["_PYTEST_ORIGINAL_CWD"] = str(_original_cwd)
