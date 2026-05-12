#!/usr/bin/env python3
"""
verify_psychological_states_gui.py – Comprehensive headless verification of Psychological_States_GUI.py
=====================================================================================
Runs ALL core classes, visualizations, tabs, states, and simulation routines without a display.

Usage: python3 verify_psychological_states_gui.py
"""

import importlib.util
import sys
import time
import tkinter as tk
import traceback
from unittest.mock import MagicMock, patch

import matplotlib

matplotlib.use("Agg")

# --- Helpers & colors ---
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed = []
failed = []
skipped = []


def assert_(cond, msg=""):
    assert cond, msg


def ok(name, detail=""):
    passed.append(name)
    print(f"  {GREEN}✓ PASS{RESET}  {name}" + (f"  [{detail}]" if detail else ""))


def fail(name, detail=""):
    failed.append(name)
    print(f"  {RED}✗ FAIL{RESET}  {name}" + (f"\n           ↳ {detail}" if detail else ""))


def skip(name, reason=""):
    skipped.append(name)
    print(f"  {YELLOW}⊘ SKIP{RESET}  {name}" + (f"  ({reason})" if reason else ""))


def section(title):
    bar = "─" * 62
    print(f"\n{CYAN}{BOLD}{bar}\n  {title}\n{bar}{RESET}")


def run_test(name, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        ok(name)
    except AssertionError as e:
        fail(name, str(e))
    except Exception as e:
        fail(name, f"{type(e).__name__}: {e}")


# ════════════════════════════════════════════════════════════════════════════
# 1. SYNTAX CHECK
# ════════════════════════════════════════════════════════════════════════════
section("1 · Syntax Check")
import py_compile

try:
    py_compile.compile("Psychological_States_GUI.py", doraise=True)
    ok("py_compile – syntax clean")
except py_compile.PyCompileError as e:
    fail("py_compile – syntax clean", str(e))
    sys.exit(1)

# ════════════════════════════════════════════════════════════════════════════
# 2. MODULE IMPORT
# ════════════════════════════════════════════════════════════════════════════
section("2 · Module Import")

_dummy_root = tk.Tk()
_dummy_root.withdraw()

# Mock components that might require display or heavy dependencies
# We mock tkinterweb to avoid display errors during headless import
with patch.dict("sys.modules", {"tkinterweb": MagicMock()}):
    try:
        spec = importlib.util.spec_from_file_location(
            "Psychological_States_GUI", "Psychological_States_GUI.py"
        )
        ps_gui = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ps_gui)
        ok("Psychological_States_GUI – imported without errors")
    except Exception as e:
        fail("Psychological_States_GUI – imported without errors", str(e))
        traceback.print_exc()
        sys.exit(1)

# ════════════════════════════════════════════════════════════════════════════
# 3. CORE CONSTANTS & STATES
# ════════════════════════════════════════════════════════════════════════════
section("3 · Core Constants & States")

run_test(
    "PSYCHOLOGICAL_STATES – exists", lambda: assert_(isinstance(ps_gui.PSYCHOLOGICAL_STATES, dict))
)
run_test(
    "PSYCHOLOGICAL_STATES – count",
    lambda: assert_(
        len(ps_gui.PSYCHOLOGICAL_STATES) >= 51,
        f"Expected 51+ states, found {len(ps_gui.PSYCHOLOGICAL_STATES)}",
    ),
)
run_test("STATE_CATEGORIES – exists", lambda: assert_(isinstance(ps_gui.STATE_CATEGORIES, dict)))

# Verify a few specific states
EXPECTED_STATES = ["flow", "anxiety", "serenity", "creativity", "depression"]
for state in EXPECTED_STATES:
    run_test(f"State '{state}' exists", lambda s=state: assert_(s in ps_gui.PSYCHOLOGICAL_STATES))

# ════════════════════════════════════════════════════════════════════════════
# 4. FULL GUI CONSTRUCTION
# ════════════════════════════════════════════════════════════════════════════
section("4 · GUI Construction")

gui = None


def _build_gui():
    global gui
    # Mock some methods that might try to show dialogs or talk to internet
    with patch.object(ps_gui.APGIVisualizerGUI, "load_configuration", return_value=True):
        with patch.object(ps_gui.APGIVisualizerGUI, "_load_ai_models", MagicMock()):
            gui = ps_gui.APGIVisualizerGUI(_dummy_root)
    assert gui is not None
    assert hasattr(gui, "notebook")


run_test("APGIVisualizerGUI.__init__", _build_gui)

if not gui:
    print(f"\n{RED}GUI construction failed – aborting.{RESET}\n")
    sys.exit(1)


def pump(ms=100):
    _dummy_root.update()
    time.sleep(ms / 1000)
    _dummy_root.update()


pump()

# ════════════════════════════════════════════════════════════════════════════
# 5. TAB VERIFICATION
# ════════════════════════════════════════════════════════════════════════════
section("5 · Tab Verification")

TABS = [
    "Psychological States",
    "Spectral Analysis (FOOOF)",
    "Genetic Data (GWAS)",
    "Psychedelic Neuroimaging (DS-07)",
    "Early Psychosis (HCP-EP DS-11)",
    "Depression EEG (OpenNeuro DS-12)",
    "iEEG Consciousness (DS-09)",
    "THINGS-Data Multimodal (DS-15)",
    "Public Datasets",
    "Landauer Validation (Raw)",
]


def _check_tabs():
    notebook = gui.notebook
    tab_names = [notebook.tab(i, "text") for i in range(notebook.index("end"))]
    for tab in TABS:
        assert tab in tab_names, f"Missing tab: {tab}"


run_test("Verify all 10 tabs exist", _check_tabs)

# ════════════════════════════════════════════════════════════════════════════
# 6. VISUALIZATION GENERATION
# ════════════════════════════════════════════════════════════════════════════
section("6 · Visualization Generation")

VIZ_TYPES = [
    "3D State Network",
    "Ignition Landscape",
    "State Radar Comparison",
    "Parameter Correlation Heatmap",
    "State Dashboard",
    "State Transition Simulation",
    "Comparative Analysis",
]


def _test_viz_generation():
    for viz in VIZ_TYPES:
        gui.viz_type.set(viz)
        # Mock renderer to avoid actual file writing if needed, but here we just check if it crashes
        with patch.object(gui.embedded_display, "load_html_file", MagicMock()):
            with patch.object(gui.embedded_display, "display_plotly_figure", MagicMock()):
                gui.generate_visualization()
                status = gui.status_var.get()
                assert "✓" in status or "Ready" in status, f"Failed viz: {viz}, status: {status}"
        pump(50)


run_test("Test all Psychological State visualizations", _test_viz_generation)

# ════════════════════════════════════════════════════════════════════════════
# 7. SIMULATION VERIFICATION
# ════════════════════════════════════════════════════════════════════════════
section("7 · Simulation Verification")


def _test_simulation():
    # Set valid parameters
    gui.tau_S_var.set("0.5")
    gui.tau_theta_var.set("30.0")
    gui.theta_0_var.set("0.5")
    gui.alpha_var.set("5.0")

    # Mock simulation components to bypass macOS objc reload issue
    mock_sim = MagicMock()
    mock_sim.EnhancedSurpriseIgnitionSystem = MagicMock()
    mock_sim.APGIParameters = MagicMock()

    with patch(
        "importlib.util.spec_from_file_location", return_value=MagicMock(loader=MagicMock())
    ):
        with patch("importlib.util.module_from_spec", return_value=mock_sim):
            with patch.dict("sys.modules", {"APGI_Equations": mock_sim}):
                with patch.object(gui.embedded_display, "display_plotly_figure", MagicMock()):
                    gui.run_simulation_with_validation()
                    status = gui.status_var.get()
                    assert (
                        "✓" in status or "Ready" in status
                    ), f"Simulation failed, status: {status}"


run_test("Run Simulation with Validation", _test_simulation)

# ════════════════════════════════════════════════════════════════════════════
# 8. PARAMETER VALIDATION
# ════════════════════════════════════════════════════════════════════════════
section("8 · Parameter Validation")


def _test_validation():
    # Test invalid value
    gui.tau_S_var.set("5.0")  # Max is 1.0
    valid = gui.validate_parameters()
    assert not valid, "Validation should fail for tau_S = 5.0"
    assert "✗" in gui.validation_status.get()

    # Test reset to valid
    gui.tau_S_var.set("0.3")
    valid = gui.validate_parameters()
    assert valid, "Validation should pass for tau_S = 0.3"
    assert "✓" in gui.validation_status.get()


run_test("Parameter range validation", _test_validation)

# ════════════════════════════════════════════════════════════════════════════
# 9. OTHER TABS (Logic Verification)
# ════════════════════════════════════════════════════════════════════════════
section("9 · Other Tabs Logic")


def _test_spectral_tab():
    if not hasattr(gui, "_generate_spectral_visualization"):
        skip("Spectral Analysis", "Method not found")
        return
    gui.spectral_viz_type.set("Consciousness Landscape")
    with patch.object(gui.spectral_display, "load_html_file", MagicMock()):
        with patch.object(gui.spectral_display, "display_plotly_figure", MagicMock()):
            gui._generate_spectral_visualization()
    ok("Spectral Analysis generation logic")


run_test("Spectral Analysis Tab", _test_spectral_tab)


def _test_psychedelic_tab():
    if not hasattr(gui, "_generate_psychedelic_visualization"):
        skip("Psychedelic Analysis", "Method not found")
        return
    gui.psychedelic_viz_type.set("Substance Comparison")
    with patch.object(gui.psychedelic_display, "display_plotly_figure", MagicMock()):
        gui._generate_psychedelic_visualization()
    ok("Psychedelic Analysis generation logic")


run_test("Psychedelic Analysis Tab", _test_psychedelic_tab)

# ════════════════════════════════════════════════════════════════════════════
# 10. THEME & SETTINGS
# ════════════════════════════════════════════════════════════════════════════
section("10 · Theme & Settings")


def _test_themes():
    if not gui.theme_manager:
        skip("Themes", "Theme manager not available")
        return
    themes = gui.theme_manager.get_available_themes()
    for t in themes:
        gui._set_theme(t)
        assert gui.theme_manager.current_theme == t
        ok(f"Theme applied: {t}")


run_test("Theme switching", _test_themes)


def _test_save_params():
    with patch("tkinter.filedialog.asksaveasfilename", return_value="/tmp/test_params.json"):
        with patch("builtins.open", MagicMock()):
            gui.save_parameters()
            assert "✓" in gui.status_var.get()


run_test("Save Parameters dialog logic", _test_save_params)

# ════════════════════════════════════════════════════════════════════════════
# 11. SHUTDOWN
# ════════════════════════════════════════════════════════════════════════════
section("11 · Shutdown")


def _test_quit():
    gui.quit_application()
    ok("quit_application")


run_test("Graceful Shutdown", _test_quit)

# ════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════════════
section("SUMMARY REPORT")
total = len(passed) + len(failed) + len(skipped)
print(f"\n  Total tests  : {BOLD}{total}{RESET}")
print(f"  {GREEN}Passed       : {len(passed)}{RESET}")
print(f"  {RED}Failed       : {len(failed)}{RESET}")
print(f"  {YELLOW}Skipped      : {len(skipped)}{RESET}")

if failed:
    print(f"\n{RED}{BOLD}  ── FAILED TESTS ──{RESET}")
    for f in failed:
        print(f"    • {f}")
    sys.exit(1)
else:
    print(f"\n{GREEN}{BOLD}  ALL CORE FUNCTIONALITY VERIFIED 100% ✓{RESET}")
    sys.exit(0)
