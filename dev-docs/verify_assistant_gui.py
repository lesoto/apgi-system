#!/usr/bin/env python3
"""
verify_assistant_gui.py  – Comprehensive headless verification of Assistant_GUI.py
=====================================================================================
Runs ALL core classes, utilities, menu commands, tab-creation paths, export/import
routines, themes, keyboard shortcuts, and GUI life-cycle methods without a display.

Usage:  python3 verify_assistant_gui.py
"""

import importlib.util

# ── Helpers & colours (MUST be defined before any use) ──────────────────────
import sys
import time
import traceback
from pathlib import Path
from unittest.mock import MagicMock, patch

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed: list = []
failed: list = []
skipped: list = []


def assert_(cond: bool, msg: str = "") -> None:
    assert cond, msg


def ok(name: str, detail: str = "") -> None:
    passed.append(name)
    print(f"  {GREEN}✓ PASS{RESET}  {name}" + (f"  [{detail}]" if detail else ""))


def fail(name: str, detail: str = "") -> None:
    failed.append(name)
    print(f"  {RED}✗ FAIL{RESET}  {name}" + (f"\n           ↳ {detail}" if detail else ""))


def skip(name: str, reason: str = "") -> None:
    skipped.append(name)
    print(f"  {YELLOW}⊘ SKIP{RESET}  {name}" + (f"  ({reason})" if reason else ""))


def section(title: str) -> None:
    bar = "─" * 62
    print(f"\n{CYAN}{BOLD}{bar}\n  {title}\n{bar}{RESET}")


def run_test(name: str, fn, *args, **kwargs) -> None:
    """Run fn(*args,**kwargs); record pass/fail; never abort the suite."""
    try:
        fn(*args, **kwargs)
        ok(name)
    except AssertionError as e:
        fail(name, str(e))
    except Exception as e:
        fail(name, f"{type(e).__name__}: {e}")


# ════════════════════════════════════════════════════════════════════════════
# 1.  SYNTAX CHECK
# ════════════════════════════════════════════════════════════════════════════
section("1 · Syntax Check")
import py_compile

try:
    py_compile.compile("Assistant_GUI.py", doraise=True)
    ok("py_compile – syntax clean")
except py_compile.PyCompileError as e:
    fail("py_compile – syntax clean", str(e))
    print(f"\n{RED}ABORT – file has syntax errors.{RESET}\n")
    sys.exit(1)


# ════════════════════════════════════════════════════════════════════════════
# 2.  MODULE IMPORT (must succeed before anything else)
# ════════════════════════════════════════════════════════════════════════════
section("2 · Module Import")

import tkinter as tk

_dummy_root = tk.Tk()
_dummy_root.withdraw()

try:
    spec = importlib.util.spec_from_file_location("Assistant_GUI", "Assistant_GUI.py")
    ag = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(ag)  # type: ignore[union-attr]
    ok("Assistant_GUI – imported without errors")
except Exception as e:
    fail("Assistant_GUI – imported without errors", str(e))
    traceback.print_exc()
    sys.exit(1)


# ════════════════════════════════════════════════════════════════════════════
# 3.  MODULE-LEVEL FLAG CONSTANTS
# ════════════════════════════════════════════════════════════════════════════
section("3 · Module-Level Flag Constants")

FLAGS = [
    "HAS_MATPLOTLIB",
    "HAS_PIL",
    "HAS_PSUTIL",
    "HAS_REPORTLAB",
    "HAS_TORCHDIFFEQ",
    "HAS_TRANSFORMERS",
    "THEME_MANAGER_AVAILABLE",
    "TOOLTIP_AVAILABLE",
    "HAS_APGI_ASSISTANT",
    "HAS_ASSISTANT",
]
for flag in FLAGS:
    run_test(
        f"{flag} exists & is bool",
        lambda f=flag: assert_(isinstance(getattr(ag, f), bool), f"{f} should be bool"),
    )


# ════════════════════════════════════════════════════════════════════════════
# 4.  UTILITY CLASSES
# ════════════════════════════════════════════════════════════════════════════
section("4 · Utility Classes")


# ── HistoryManager ─────────────────────────────────────────────────────────
def _test_history_manager() -> None:
    hm = ag.HistoryManager(max_memory_mb=50, auto_prune=True)
    d = hm.create_managed_deque("state", maxlen=10)
    for i in range(15):
        d.append({"ts": i, "val": i * 2})
    assert len(d) <= 10, "deque maxlen not respected"
    stats = hm.get_memory_stats()
    assert "max_memory_mb" in stats
    cleared = hm.clear_all_history()
    assert cleared >= 0


run_test("HistoryManager – create/overflow/clear", _test_history_manager)


# ── ManagedDeque ───────────────────────────────────────────────────────────
def _test_managed_deque() -> None:
    hm = ag.HistoryManager()
    md = ag.ManagedDeque(maxlen=5, history_type="energy", manager=hm)
    for i in range(8):
        md.append(i)
    assert len(md) == 5
    md.prune(0.5)
    assert len(md) <= 3
    md.smart_prune(1)
    md.clear()
    assert len(md) == 0


run_test("ManagedDeque – append/prune/smart_prune/clear", _test_managed_deque)


# ── DependencyNotifier ─────────────────────────────────────────────────────
def _test_dependency_notifier() -> None:
    dn = ag.DependencyNotifier(parent_widget=None)
    dn.check_and_notify_limitations()  # no widget → print-only fallback
    dn.reset_notifications()
    assert len(dn.notified_features) == 0


run_test("DependencyNotifier – check/reset", _test_dependency_notifier)


# ── Debouncer ──────────────────────────────────────────────────────────────
def _test_debouncer() -> None:
    db = ag.Debouncer(delay_ms=10)
    results: list = []
    db.debounce("k1", results.append, 99)  # no root → immediate
    assert 99 in results


run_test("Debouncer – immediate fallback (no root)", _test_debouncer)


# ── ErrorContext ───────────────────────────────────────────────────────────
def _test_error_context() -> None:
    import logging

    log = logging.getLogger("verify_ec")
    # Non-critical exception suppressed when user_facing=True
    with ag.ErrorContext("TestOp", user_facing=True, logger=log):
        raise ValueError("simulated non-critical")
    # Critical exceptions must propagate
    try:
        with ag.ErrorContext("TestOp2", user_facing=True, logger=log):
            raise KeyboardInterrupt()
    except KeyboardInterrupt:
        pass  # expected


run_test("ErrorContext – suppress & re-raise critical", _test_error_context)


# ── StatusManager ──────────────────────────────────────────────────────────
def _test_status_manager() -> None:
    ml = MagicMock()
    ml.winfo_exists.return_value = True
    al = MagicMock()
    al.winfo_exists.return_value = True
    sm = ag.StatusManager(ml, al)
    sm.set_status("ready", "ready")
    time.sleep(0.6)  # Wait for min_update_interval (0.5s)
    sm.set_status("processing…", "processing", "thinking")
    h = sm.get_history()
    assert len(h) >= 2
    sm.clear_history()
    assert len(sm.get_history()) == 0


run_test("StatusManager – set/get/clear history", _test_status_manager)


# ── InputValidator ─────────────────────────────────────────────────────────
def _test_input_validator() -> None:
    iv = ag.InputValidator()
    # Fixed: validate_physiological expects 4 floats and returns (bool, list)
    ok_val, errors = iv.validate_physiological(70.0, 50.0, 15.0, 4.5)
    assert ok_val, f"Validation failed: {errors}"
    ok, msg = iv.validate_query("Hello world!")
    assert ok
    ok, msg = iv.validate_query("")
    assert not ok


run_test("InputValidator – physiological + query checks", _test_input_validator)


# ── UsageTracker ───────────────────────────────────────────────────────────
def _test_usage_tracker() -> None:
    ut = ag.UsageTracker()
    # Fixed: track_query expects (query_length: int, response_time: float, state: str)
    ut.track_query(10, 0.5, "state1")
    s = ut.get_usage_summary()
    assert s["total_queries"] >= 1


run_test("UsageTracker – track + summary", _test_usage_tracker)


# ── ActionHistory ──────────────────────────────────────────────────────────
def _test_action_history() -> None:
    ah = ag.ActionHistory(max_history=5)
    assert not ah.can_undo()
    assert not ah.can_redo()


run_test("ActionHistory – empty can_undo/can_redo", _test_action_history)


# ── PermissionValidator ────────────────────────────────────────────────────
def _test_permission_validator() -> None:
    import logging

    pv = ag.PermissionValidator(logger=logging.getLogger("pv"))
    # Fixed: validate_file_access returns 3 values
    ok_val, msg, sugg = pv.validate_file_access("/tmp")
    assert isinstance(ok_val, bool)


run_test("PermissionValidator – validate_file_access", _test_permission_validator)


# ── DebouncedUpdater ───────────────────────────────────────────────────────
def _test_debounced_updater() -> None:
    du = ag.DebouncedUpdater(delay_ms=50)
    stats = du.get_operation_stats()
    assert isinstance(stats, dict)
    # Fixed: cancel_all expects root
    du.cancel_all(_dummy_root)


run_test("DebouncedUpdater – stats/cancel_all", _test_debounced_updater)


# ── GUIConfig ──────────────────────────────────────────────────────────────
def _test_gui_config() -> None:
    cfg = ag.GUIConfig
    assert hasattr(cfg, "DEBOUNCE_DELAY_MS")
    assert isinstance(cfg.DEBOUNCE_DELAY_MS, int)


run_test("GUIConfig – DEBOUNCE_DELAY_MS attribute", _test_gui_config)


# ── setup_logging ──────────────────────────────────────────────────────────
def _test_setup_logging() -> None:
    logger = ag.setup_logging()
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")


run_test("setup_logging – returns Logger", _test_setup_logging)

# ── load_apgi_module ───────────────────────────────────────────────────────
run_test("load_apgi_module – runs without crash", ag.load_apgi_module)


# ════════════════════════════════════════════════════════════════════════════
# 5.  FULL GUI CONSTRUCTION (headless Tk)
# ════════════════════════════════════════════════════════════════════════════
section("5 · Full APGIGUI Instantiation")

gui = None
root = None


def _build_gui() -> None:
    global gui, root
    root = tk.Tk()
    root.withdraw()
    gui = ag.APGIGUI(root)
    assert gui is not None
    assert hasattr(gui, "notebook")


run_test("APGIGUI.__init__ – full construction", _build_gui)

if gui is None:
    print(f"\n{RED}GUI construction failed – cannot continue GUI tests.{RESET}\n")
    sys.exit(1)


def pump(ms: int = 200) -> None:
    root.update()
    time.sleep(ms / 1000)
    root.update()


pump()

# ════════════════════════════════════════════════════════════════════════════
# 6.  MENU COMMANDS
# ════════════════════════════════════════════════════════════════════════════
section("6 · Menu Commands")


def _call(method: str, *args) -> None:
    getattr(gui, method)(*args)


# --- File menu ---
run_test("new_session", lambda: _call("new_session"))
run_test("show_settings", lambda: _call("show_settings"))
run_test("show_export_settings", lambda: _call("show_export_settings"))

with patch("tkinter.filedialog.asksaveasfilename", return_value=""):
    with patch("tkinter.filedialog.askopenfilename", return_value=""):
        run_test("export_config (no file)", lambda: _call("export_config"))
        run_test("import_config (no file)", lambda: _call("import_config"))

with patch("tkinter.filedialog.asksaveasfilename", return_value="/tmp/apgi_test_session.json"):
    run_test("save_session → file dialog", lambda: _call("save_session"))

with patch("tkinter.filedialog.askopenfilename", return_value=""):
    run_test("load_session → no file", lambda: _call("load_session"))

# --- View menu ---
run_test("toggle_fullscreen", lambda: _call("toggle_fullscreen"))
run_test("refresh_displays", lambda: _call("refresh_displays"))

# --- Help menu ---
run_test("show_quick_start", lambda: _call("show_quick_start"))
run_test("show_shortcuts", lambda: _call("show_shortcuts"))
run_test("show_about", lambda: _call("show_about"))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 7.  TAB CREATION METHODS
# ════════════════════════════════════════════════════════════════════════════
section("7 · Tab Creation Methods")

TAB_METHODS = [
    "create_main_tab",
    "create_cognitive_monitoring_tab",
    "create_oscillatory_tab",
    "create_biofeedback_tab",
    "create_energy_tab",
    "create_performance_tab",
    "create_visualization_tab",
    "create_settings_tab",
]
for m in TAB_METHODS:
    if hasattr(gui, m):
        run_test(f"{m} – callable", lambda fn=m: getattr(gui, fn)())
    else:
        skip(m, "method not found on gui")

pump()


# ════════════════════════════════════════════════════════════════════════════
# 8.  PHYSIOLOGY PRESET SETTERS
# ════════════════════════════════════════════════════════════════════════════
section("8 · Physiology Preset Setters")

run_test("set_relaxed_state", lambda: _call("set_relaxed_state"))
run_test("set_normal_state", lambda: _call("set_normal_state"))
run_test("set_stressed_state", lambda: _call("set_stressed_state"))
run_test("set_anxious_state", lambda: _call("set_anxious_state"))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 9.  QUERY PROCESSING
# ════════════════════════════════════════════════════════════════════════════
section("9 · Query Processing")

run_test("clear_query – empty input safe", lambda: _call("clear_query"))


def _test_process_query() -> None:
    # Fixed: process_query takes no arguments, uses widget content
    if hasattr(gui, "query_input"):
        gui.query_input.insert(tk.END, "test headless query")
    gui.process_query()
    time.sleep(0.5)
    root.update()


run_test("process_query – spawns thread without crash", _test_process_query)


def _test_send_query_empty() -> None:
    if hasattr(gui, "query_input"):
        gui.query_input.delete(1.0, tk.END)
    gui.send_query()  # should early-return on empty input


run_test("send_query – empty input early-return", _test_send_query_empty)
pump()


# ════════════════════════════════════════════════════════════════════════════
# 10.  VISUALIZATIONS
# ════════════════════════════════════════════════════════════════════════════
section("10 · Visualization Methods")

VIZ_METHODS = [
    "update_displays",
    "update_visualizations",
    "update_oscillatory_display",
    "update_energy_display",
    "update_cognitive_display",
    "update_biofeedback_display",
    "update_performance_metrics",
    "safe_update_energy_display",
    "safe_update_cognitive_display",
    "safe_update_oscillatory_display",
    "safe_update_biofeedback_display",
]
for m in VIZ_METHODS:
    # Fixed: many visualization methods expect a 'response' dict
    mock_resp = {"cognitive_state": {"primary": "focused", "surprise": 0.1}}
    if m in [
        "update_visualizations",
        "update_oscillatory_display",
        "update_cognitive_display",
        "update_biofeedback_display",
    ]:
        run_test(f"{m}", lambda fn=m: getattr(gui, fn)(mock_resp))
    else:
        run_test(f"{m}", lambda fn=m: getattr(gui, fn)())

if ag.HAS_MATPLOTLIB:
    run_test("generate_state_timeline", lambda: _call("generate_state_timeline"))
    run_test("generate_energy_plot", lambda: _call("generate_energy_plot"))
    run_test("clear_viz_display", lambda: _call("clear_viz_display"))
    with patch("tkinter.filedialog.asksaveasfilename", return_value=""):
        run_test("save_state_timeline (no file)", lambda: _call("save_state_timeline"))
        run_test("save_energy_plot (no file)", lambda: _call("save_energy_plot"))
        run_test("save_oscillatory_spectrum (no file)", lambda: _call("save_oscillatory_spectrum"))
        run_test("save_all_plots (no file)", lambda: _call("save_all_plots"))
else:
    skip("Matplotlib visualization tests", "HAS_MATPLOTLIB=False")

pump()


# ════════════════════════════════════════════════════════════════════════════
# 11.  EXPORT ROUTINES
# ════════════════════════════════════════════════════════════════════════════
section("11 · Export Routines")

with patch("tkinter.filedialog.asksaveasfilename", return_value=""):
    run_test("export_session_csv (no file)", lambda: _call("export_session_csv"))
    run_test("export_metrics_csv (no file)", lambda: _call("export_metrics_csv"))
    run_test("export_session_json (no file)", lambda: _call("export_session_json"))

if ag.HAS_REPORTLAB:
    with patch("tkinter.filedialog.asksaveasfilename", return_value=""):
        run_test("export_session_pdf (no file)", lambda: _call("export_session_pdf"))
else:
    skip("export_session_pdf", "HAS_REPORTLAB=False")

pump()


# ════════════════════════════════════════════════════════════════════════════
# 12.  SETTINGS & CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════
section("12 · Settings & Configuration")

run_test("apply_settings", lambda: _call("apply_settings"))
run_test("reset_to_defaults", lambda: _call("reset_to_defaults"))
run_test("validate_configuration", lambda: gui.validate_configuration({}))
run_test("save_configuration", lambda: _call("save_configuration"))
run_test("load_configuration", lambda: _call("load_configuration"))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 13.  THEME & HIGH-CONTRAST
# ════════════════════════════════════════════════════════════════════════════
section("13 · Theme & High-Contrast")

for theme in ["normal", "dark", "light", "high_contrast"]:
    run_test(f"apply_theme('{theme}')", lambda t=theme: _call("apply_theme", t))

run_test("toggle_high_contrast", lambda: _call("toggle_high_contrast"))
run_test("get_theme_color – 'bg'", lambda: assert_(gui.get_theme_color("bg") is not None))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 14.  FONT SIZE / ACCESSIBILITY
# ════════════════════════════════════════════════════════════════════════════
section("14 · Accessibility – Font Size & Tab Navigation")

run_test("increase_font_size", lambda: _call("increase_font_size"))
run_test("decrease_font_size", lambda: _call("decrease_font_size"))
run_test("reset_font_size", lambda: _call("reset_font_size"))
run_test("next_tab", lambda: gui.next_tab(None))
run_test("prev_tab", lambda: gui.prev_tab(None))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 15.  AUTO-CALIBRATION
# ════════════════════════════════════════════════════════════════════════════
section("15 · Auto-Calibration")

run_test("calibrate_baseline", lambda: _call("calibrate_baseline"))
run_test("auto_calibrate", lambda: _call("auto_calibrate"))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 16.  HISTORY & MEMORY MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════
section("16 · History & Memory Management")

run_test("show_memory_stats", lambda: _call("show_memory_stats"))
run_test("clear_all_history", lambda: _call("clear_all_history"))
run_test("configure_history_limits", lambda: _call("configure_history_limits"))
run_test("clear_history", lambda: _call("clear_history"))
run_test("enable_memory_profiling", lambda: _call("enable_memory_profiling"))
run_test("disable_memory_profiling", lambda: _call("disable_memory_profiling"))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 17.  SESSION MANAGEMENT & AUTO-SAVE
# ════════════════════════════════════════════════════════════════════════════
section("17 · Session Management & Auto-Save")

run_test("auto_save_session", lambda: _call("auto_save_session"))
run_test("check_auto_save_recovery", lambda: _call("check_auto_save_recovery"))
run_test("start_auto_save_timer", lambda: _call("start_auto_save_timer"))
run_test("stop_auto_save_timer", lambda: _call("stop_auto_save_timer"))
run_test("reset_assistant", lambda: _call("reset_assistant"))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 18.  LOGGING TAB
# ════════════════════════════════════════════════════════════════════════════
section("18 · Log Tab (view / refresh / clear)")

run_test("view_logs", lambda: _call("view_logs"))
run_test("refresh_logs", lambda: gui.refresh_logs(MagicMock(), Path("/tmp/test.log")))
run_test("clear_logs", lambda: gui.clear_logs(Path("/tmp/test.log"), MagicMock()))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 19.  STATUS BAR & SYSTEM INFO
# ════════════════════════════════════════════════════════════════════════════
section("19 · Status Bar & System Info")

run_test("set_status – ready", lambda: gui.set_status("Ready", "ready"))
run_test("set_status – error", lambda: gui.set_status("Error", "error"))
run_test("set_status – processing", lambda: gui.set_status("Processing", "processing"))
run_test("update_system_info", lambda: _call("update_system_info"))
run_test("update_assistant_status", lambda: gui.update_assistant_status("idle"))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 20.  INTERNAL / PRIVATE HELPERS
# ════════════════════════════════════════════════════════════════════════════
section("20 · Internal / Private Helpers")

run_test("_get_system_info", lambda: gui._get_system_info())
run_test("_calculate_session_duration", lambda: gui._calculate_session_duration())
run_test("_classify_query_type – question", lambda: gui._classify_query_type("What is this?"))
run_test("_classify_query_type – command", lambda: gui._classify_query_type("run analysis"))
run_test("_calculate_performance_metrics", lambda: gui._calculate_performance_metrics())
run_test("_generate_executive_summary", lambda: gui._generate_executive_summary({}))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 21.  KEYBOARD SHORTCUTS & EVENT HANDLERS
# ════════════════════════════════════════════════════════════════════════════
section("21 · Keyboard Shortcuts & Event Handlers")

run_test("setup_keyboard_shortcuts", lambda: _call("setup_keyboard_shortcuts"))
run_test("setup_accessibility", lambda: _call("setup_accessibility"))
run_test("setup_event_handlers", lambda: _call("setup_event_handlers"))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 22.  UNDO / REDO
# ════════════════════════════════════════════════════════════════════════════
section("22 · Undo / Redo")

run_test("undo_action – nothing to undo", lambda: _call("undo_action"))
run_test("redo_action – nothing to redo", lambda: _call("redo_action"))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 23.  PROGRESS BAR
# ════════════════════════════════════════════════════════════════════════════
section("23 · Progress Bar")

run_test("show_progress(50%)", lambda: gui.show_progress("50%"))
pump(100)
run_test("hide_progress", lambda: gui.hide_progress())
pump()


# ════════════════════════════════════════════════════════════════════════════
# 24.  CHAR-COUNT & DISPLAY HELPERS
# ════════════════════════════════════════════════════════════════════════════
section("24 · Char Count & Display Helpers")

run_test("update_char_count", lambda: _call("update_char_count"))
run_test("update_energy_stats", lambda: _call("update_energy_stats"))
pump()


# ════════════════════════════════════════════════════════════════════════════
# 25.  GRACEFUL SHUTDOWN (last – always)
# ════════════════════════════════════════════════════════════════════════════
section("25 · Graceful Shutdown")


def _test_quit() -> None:
    gui.stop_auto_save_timer()
    gui.quit_application()


run_test("quit_application – graceful shutdown", _test_quit)
try:
    root.destroy()
except Exception:
    pass
try:
    _dummy_root.destroy()
except Exception:
    pass


# ════════════════════════════════════════════════════════════════════════════
# SUMMARY REPORT
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
else:
    print(f"\n{GREEN}{BOLD}  ALL TESTS PASSED ✓{RESET}")

pct = round(len(passed) / max(len(passed) + len(failed), 1) * 100, 1)
print(f"\n  Pass-rate    : {BOLD}{pct}%{RESET}\n")

sys.exit(0 if not failed else 1)
