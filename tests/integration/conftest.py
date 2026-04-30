"""
Pytest configuration for integration tests.

Configures hypothesis to avoid issues with changing working directories.
"""

import os
from pathlib import Path

import pytest

# Configure hypothesis to avoid CWD issues
# The hypothesis plugin fails when trying to report failures if CWD changes
os.environ.setdefault("HYPOTHESIS_NO_DIFF", "1")

# Configure matplotlib to use non-interactive backend to prevent tkinter segfaults
os.environ.setdefault("MPLBACKEND", "Agg")

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


def pytest_runtest_teardown(item):
    """Cleanup matplotlib/tkinter resources after each test to prevent segfaults."""
    try:
        import matplotlib.pyplot as plt

        # Close all matplotlib figures to prevent tkinter cleanup issues
        plt.close("all")
    except ImportError:
        pass
    except Exception:
        # Ignore any errors during cleanup
        pass


def pytest_sessionfinish(session, exitstatus):
    """Final cleanup at end of test session to prevent segfaults."""
    try:
        import matplotlib.pyplot as plt

        # Close all figures one more time
        plt.close("all")
    except ImportError:
        pass
    except Exception:
        # Ignore any errors during cleanup
        pass


def pytest_collection_modifyitems(config, items):
    """Skip GUI-related tests that cause segmentation faults in headless environment."""
    gui_related = [
        "test_launcher_importable",
        "test_system_gui_initialization",
        "test_main_app_gui_initialization",
    ]
    for item in items:
        # Skip all tests in test_launchers.py module
        if "test_launchers.py" in str(item.fspath):
            item.add_marker(
                pytest.mark.skip(
                    reason="GUI tests cause segmentation fault in headless environment"
                )
            )
        # Also skip by test name as backup
        elif any(gui_test in item.name for gui_test in gui_related):
            item.add_marker(
                pytest.mark.skip(
                    reason="GUI tests cause segmentation fault in headless environment"
                )
            )
