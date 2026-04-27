"""
Pytest configuration for property-based tests.

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
    """Configure pytest and hypothesis for property tests."""
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


def pytest_runtest_teardown(item):
    """Restore original CWD after each test."""
    # Restore original CWD if it was changed
    try:
        original_cwd = os.environ.get("_PYTEST_ORIGINAL_CWD")
        if original_cwd and Path(original_cwd).exists():
            os.chdir(original_cwd)
    except Exception:
        # If restoration fails, try to change to project root
        try:
            project_root = Path(__file__).parent.parent.parent
            if project_root.exists():
                os.chdir(project_root)
        except Exception:
            pass
