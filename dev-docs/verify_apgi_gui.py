#!/usr/bin/env python3
"""
verify_apgi_gui.py – Comprehensive headless verification of APGI_GUI.py
======================================================================
"""

import importlib.util
import sys
import tkinter as tk
import traceback
from unittest.mock import MagicMock, mock_open, patch

# ── Helpers & colours ───────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed: list[str] = []
failed: list[str] = []
skipped: list[str] = []
gui = None


def assert_(cond, msg=""):
    assert cond, msg


def ok(name, detail=""):
    passed.append(name)
    print(f"  {GREEN}✓ PASS{RESET}  {name}" + (f"  [{detail}]" if detail else ""))


def fail(name, detail=""):
    failed.append(name)
    print(f"  {RED}✗ FAIL{RESET}  {name}" + (f"\n           ↳ {detail}" if detail else ""))


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
    py_compile.compile("APGI_GUI.py", doraise=True)
    ok("py_compile – syntax clean")
except py_compile.PyCompileError as e:
    fail("py_compile – syntax clean", str(e))
    sys.exit(1)

# ════════════════════════════════════════════════════════════════════════════
# 2. MODULE IMPORT
# ════════════════════════════════════════════════════════════════════════════
section("2 · Module Import")

# Mocking external dependencies and potentially blocking UI calls
with (
    patch("matplotlib.use"),
    patch("matplotlib.backends.backend_tkagg.FigureCanvasTkAgg"),
    patch("matplotlib.backends.backend_tkagg.NavigationToolbar2Tk"),
    patch("matplotlib.figure.Figure.add_subplot"),
    patch("tkinter.messagebox.showinfo"),
    patch("tkinter.messagebox.showwarning"),
    patch("tkinter.messagebox.showerror"),
    patch("tkinter.messagebox.askyesno", return_value=True),
    patch("apgi_framework.system.APGISystem", MagicMock()),
):

    try:
        spec = importlib.util.spec_from_file_location("APGI_GUI", "APGI_GUI.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ok("APGI_GUI – imported without errors")
    except Exception as e:
        fail("APGI_GUI – imported without errors", str(e))
        traceback.print_exc()
        sys.exit(1)

# ════════════════════════════════════════════════════════════════════════════
# 3. GUI INITIALIZATION
# ════════════════════════════════════════════════════════════════════════════
section("3 · GUI Initialization")

_root = tk.Tk()
_root.withdraw()


def test_gui_init():
    global gui
    with (
        patch("apgi_gui.theme_manager.ThemeManager.set_theme"),
        patch("APGI_GUI.APGIGui._apply_theme_to_root"),
        patch("APGI_GUI.APGIGui._initialize_system"),
    ):
        gui = mod.APGIGui(_root)
        gui._convert_to_tkinter_variables()
        gui.apgi_simulation = MagicMock()

        # Helper for numeric stats
        def get_mock_stats(*args, **kwargs):
            return MagicMock(__getitem__=lambda s, k: 0.0, get=lambda k, d=0.0: 0.0)

        # Metabolism mocks
        gui.apgi_simulation.metabolism.current_reserves = 100.0
        gui.apgi_simulation.metabolism.total_consumed = 0.0
        gui.apgi_simulation.metabolism.baseline_rate = 1.0
        gui.apgi_simulation.metabolism.ignition_cost = 0.5
        gui.apgi_simulation.metabolism.total_budget = 1000.0

        # Body model mocks
        gui.apgi_simulation.body_model.get_current_state_dict.return_value = {
            "heart_rate": 70.0,
            "cortisol": 0.1,
        }
        gui.apgi_simulation.body_model.arousal_level = 0.5
        gui.apgi_simulation.body_model.stress_level = 0.1
        gui.apgi_simulation.body_model.activity_level = 0.2

        # Stats mocks
        gui.apgi_simulation.ignition_threshold.get_statistics.return_value = {
            "mean_signal": 0.5,
            "mean_threshold": 2.0,
            "recent_ignitions": 5,
            "ignition_rate": 0.1,
            "current_probability": 0.2,
            "std_signal": 0.1,
            "std_threshold": 0.1,
        }
        gui.apgi_simulation.somatic_markers.get_statistics.return_value = {
            "num_markers": 10,
            "capacity_used": 0.1,
            "retrieval_success_rate": 0.8,
            "avg_strength": 0.5,
            "avg_outcome": 0.5,
        }
        gui.apgi_simulation.coherence_model.get_statistics.return_value = {
            "mean_coherence": 0.7,
            "std_coherence": 0.1,
        }
        gui.apgi_simulation.get_state_summary.return_value = {
            "time_ms": 1000.0,
            "workspace_state": "Active",
            "metabolic_reserves": 100.0,
            "allostatic_load": 0.1,
            "ignition_stats": {"recent_ignitions": 5, "mean_signal": 0.5, "mean_threshold": 2.0},
            "somatic_markers": {"num_markers": 10, "retrieval_success_rate": 0.8},
        }
    assert_(hasattr(gui, "notebook"), "GUI should have a notebook")
    assert_(
        len(gui.notebook.tabs()) == 6, f"GUI should have 6 tabs, found {len(gui.notebook.tabs())}"
    )


run_test("APGIGui – constructor and layout", test_gui_init)

# ════════════════════════════════════════════════════════════════════════════
# 4. TAB & PANEL VERIFICATION
# ════════════════════════════════════════════════════════════════════════════
section("4 · Tab & Panel Verification")


def check_tabs():
    expected_tabs = [
        "Neural Activity",
        "Interoception",
        "System Metrics",
        "Self-Model",
        "Oscillations",
        "State Space",
    ]
    found_tabs = [gui.notebook.tab(i, "text") for i in range(len(gui.notebook.tabs()))]
    for tab in expected_tabs:
        assert_(tab in found_tabs, f"Tab '{tab}' missing")
        ok(f"Tab confirmed: {tab}")


run_test("Verify all 6 visualization tabs", check_tabs)

# ════════════════════════════════════════════════════════════════════════════
# 5. SIMULATION CONTROLS
# ════════════════════════════════════════════════════════════════════════════
section("5 · Simulation Controls")


def test_sim_lifecycle():
    with patch("threading.Thread.start"):
        gui._start_simulation()
    assert_(gui.is_running, "System should be running")
    gui._pause_simulation()
    assert_(gui.is_paused, "System should be paused")
    gui._pause_simulation()
    assert_(not gui.is_paused, "System should be resumed")
    gui._stop_simulation()
    assert_(not gui.is_running, "System should be stopped")
    gui._reset_simulation()


run_test("Simulation Control Logic", test_sim_lifecycle)

# ════════════════════════════════════════════════════════════════════════════
# 6. MENU & COMMANDS
# ════════════════════════════════════════════════════════════════════════════
section("6 · Menu & Commands")


def test_all_menu_commands():
    with (
        patch("tkinter.filedialog.askopenfilename", return_value="test.yaml"),
        patch("tkinter.filedialog.asksaveasfilename", return_value="test.yaml"),
        patch("builtins.open", mock_open()),
        patch.object(mod.messagebox, "showinfo"),
        patch.object(mod.tk, "Toplevel"),
    ):

        gui._load_config()
        gui._save_config()
        gui._trigger_ignition()
        gui._induce_stressor()

        # Mocking stats
        mock_stats = {
            "mean_signal": 0.5,
            "mean_threshold": 2.0,
            "recent_ignitions": 5,
            "ignition_rate": 0.1,
            "current_probability": 0.2,
            "std_signal": 0.1,
            "std_threshold": 0.1,
        }
        gui.apgi_simulation.ignition_threshold.get_statistics.return_value = mock_stats

        gui._show_ignition_stats()
        gui._show_energy_report()
        gui._analyze_markers()
        gui._analyze_coherence()

        gui._show_docs()
        gui._show_shortcuts()
        gui._show_about()


run_test("Core Menu Command Dispatch", test_all_menu_commands)

# ════════════════════════════════════════════════════════════════════════════
# 7. THEME & VIEW
# ════════════════════════════════════════════════════════════════════════════
section("7 · Theme & View")


def test_theme_and_view():
    with patch("APGI_GUI.APGIGui._apply_theme_to_root"), patch("builtins.open", mock_open()):
        gui._change_theme("dark")
        gui._change_theme("normal")
    gui._toggle_control_panel()


run_test("Theme & View Toggles", test_theme_and_view)

# ════════════════════════════════════════════════════════════════════════════
# 8. DATA EXPORT
# ════════════════════════════════════════════════════════════════════════════
section("8 · Data Export")


def test_data_export():
    with (
        patch("tkinter.filedialog.asksaveasfilename", return_value="export.csv"),
        patch("builtins.open", mock_open()),
        patch("matplotlib.figure.Figure.savefig"),
    ):
        gui._export_data()
        gui._export_plot()


run_test("Data & Plot Export", test_data_export)

# ════════════════════════════════════════════════════════════════════════════
# 9. SHUTDOWN
# ════════════════════════════════════════════════════════════════════════════
section("9 · Shutdown")


def test_shutdown():
    with patch("tkinter.messagebox.askyesno", return_value=True):
        gui._confirm_exit()
    assert_(not gui.is_running, "System should be stopped on exit")


run_test("Graceful Shutdown", test_shutdown)

print(f"\n{BOLD}Verification Summary{RESET}")
print(f"{GREEN}Passed:  {len(passed)}{RESET}")
print(f"{RED}Failed:  {len(failed)}{RESET}")
if failed:
    sys.exit(1)
else:
    print(f"\n{GREEN}{BOLD}ALL TESTS PASSED 100%{RESET}\n")
    sys.exit(0)
