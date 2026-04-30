import importlib
import sys

import pytest

# List of all GUI entry points
# Note: APGI_Application_GUI is excluded due to segmentation fault on import
# This is a known issue with matplotlib/tkinter initialization in headless environments
GUI_LAUNCHERS = [
    "APGI_GUI",
    "APGI_Simulation_GUI",
    "Assistant_GUI",
    "Psychological_States_GUI",
]


@pytest.mark.integration
@pytest.mark.parametrize("launcher", GUI_LAUNCHERS)
def test_launcher_importable(launcher):
    """
    Test that each GUI launcher is importable without errors.
    This ensures that basic dependencies and syntax are correct.
    """
    try:
        # Clear module from sys.modules if it was previously imported
        if launcher in sys.modules:
            del sys.modules[launcher]

        # Import the launcher module
        importlib.import_module(launcher)
    except ImportError as e:
        pytest.fail(f"Launcher {launcher} failed to import: {e}")
    except Exception as e:
        # Some GUIs might try to initialize Tkinter which fails without a display
        # We catch these specifically to distinguish from code errors
        if (
            "no display name and no $DISPLAY environment variable" in str(e)
            or "main thread is not in main loop" in str(e)
            or "TclError" in str(e)
        ):
            # This is expected in headless CI environments if they try to init Tk
            pass
        else:
            pytest.fail(f"Launcher {launcher} failed during import/init: {e}")


@pytest.mark.integration
@pytest.mark.skip(
    reason="APGI_Application_GUI causes segmentation fault on import in headless environment"
)
def test_main_app_gui_initialization():
    """
    Test a more specific initialization of the main application if possible.
    Since it's a GUI, we might only be able to check if the class can be instantiated.

    Skipped due to segmentation fault on import in headless CI environment.
    """
    try:
        from APGI_Application_GUI import APGIFrameworkGUI

        # We don't call it as it would try to open a window
        assert APGIFrameworkGUI is not None
    except ImportError:
        pytest.fail("APGI_Application_GUI.APGIFrameworkGUI not found")


@pytest.mark.integration
@pytest.mark.skip(
    reason="GUI initialization causes segmentation fault during pytest cleanup in headless environment"
)
def test_system_gui_initialization():
    try:
        from APGI_GUI import APGIGui

        assert APGIGui is not None
    except ImportError:
        pytest.fail("APGI_GUI.APGIGui not found")
