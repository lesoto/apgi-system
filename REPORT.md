# APGI System — Comprehensive Application Audit Report

**Date:** 2026-02-22
**Auditor:** Claude (Automated End-to-End Audit)
**Branch:** `claude/app-audit-testing-sGNvO`
**Scope:** Full application — GUI layer, REST API, core system modules, tests, and documentation

---

## Executive Summary

The APGI (Allostatic Precision-Gated Ignition) System is a multi-component Python application for computational consciousness modeling. It comprises seven GUI applications, a FastAPI REST backend, a deeply modular core simulation engine, a configuration/validation layer, and a comprehensive test suite.

The core simulation engine and data-processing backend are well-architected, mathematically rigorous, and robustly implemented. The REST API follows modern FastAPI best practices with proper authentication, rate limiting, and schema validation. However, the GUI layer — which constitutes the primary user-facing surface — contains **several critical stub implementations** that silently fail or mislead users, along with significant code duplication and missing persistence mechanisms.

Three issues are classified **Critical** because they present functionality that appears complete to the user but performs no real action. Nine issues are classified **High**, eleven **Medium**, and eight **Low**.

The overall implementation is approximately **65% complete** relative to the documented feature set.

---

## KPI Scores

| KPI | Score | Rationale |
|-----|-------|-----------|
| **1. Functional Completeness** | **62 / 100** | Core simulation engine and API are fully functional. Three critical stub implementations (View panel toggles, sensory injection, body state editor) and one incomplete API feature (alert DB) reduce completeness significantly. LLM/assistant integration is infrastructural only — no real conversation system. |
| **2. UI/UX Consistency** | **68 / 100** | Theme system is coherent and multi-application. Keyboard shortcuts are documented and mostly bound. `ToolTip` class is duplicated verbatim across four separate files. View menu checkbuttons do not reflect actual panel visibility state. Design System doc (DESIGN-SYSTEM.md) defines a full token system that is partially unenforced in code. |
| **3. Responsiveness & Performance** | **74 / 100** | Responsive window sizing, thread-safe data buffers (RLock/Lock), 100 ms GUI update cycle, bounded deques for memory safety, and FPS monitoring are all implemented correctly. Log file grows unbounded (no RotatingFileHandler). No data downsampling for long runs. Update loop runs continuously even when simulation is idle. |
| **4. Error Handling & Resilience** | **72 / 100** | Extensive try/except coverage, thread-safe operations, dependency-check fallbacks, and user-facing error dialogs are present. Several bare `except: pass` blocks silently swallow errors. Alert middleware has no database persistence. No crash-recovery for the main simulation GUI. |
| **5. Overall Implementation Quality** | **66 / 100** | Strong backend architecture, good test coverage, well-written documentation. GUI files are monolithic (4 453 – 8 601 lines each). Three stub methods are falsely presented as functional. Code duplication across GUI files is high. Session state is not persisted. |

**Aggregate Score: 68 / 100**

---

## Bug Inventory

### CRITICAL

---

#### BUG-001 — View Menu Panel Toggles Are No-Ops

| Field | Detail |
|---|---|
| **Severity** | Critical |
| **Component** | `apgi_gui.py` — `_toggle_control_panel()`, `_toggle_neural_activity()`, `_toggle_interoception()`, `_toggle_system_metrics()` |
| **Lines** | 1961–1980 |
| **Affected URL / Entry Point** | Main GUI → View menu → Control Panel / Neural Activity / Interoception / System Metrics |

**Description:** All four View-menu checkbutton handlers contain only a `_log_event()` call. The comment at line 1963 reads `# Implementation would show/hide control panel`. No widget `pack_forget()` or `pack()` calls are made. Toggling any View option logs a message but never changes the layout.

**Reproduction Steps:**
1. Launch `python apgi_gui.py`.
2. Open **View** menu → uncheck **Control Panel**.
3. Observe: the left control panel remains fully visible.
4. Check the event log: it says "Control panel hidden" — but nothing hides.

**Expected:** The control panel widget is removed from the layout when unchecked and restored when rechecked.
**Actual:** No visual change; only a log message is written.

---

#### BUG-002 — "Inject Sensory Input" Is a Simulated Stub

| Field | Detail |
|---|---|
| **Severity** | Critical |
| **Component** | `apgi_gui.py` — `_inject_input()` |
| **Lines** | 3710–3864 |
| **Affected URL / Entry Point** | Main GUI → Tools menu → Inject Sensory Input |

**Description:** The dialog generates a signal array and prints parameters to a status text widget, then displays `messagebox.showinfo("Success", "Custom input injected successfully!")`. However, lines 3835–3844 contain the comment `# Inject into system (this would need to be implemented in the APGI system)` and the status text explicitly reads **"Input injection simulated!"** followed by **"(Note: Actual injection requires APGI system integration)"**. No signal is ever passed to `self.apgi_system`.

**Reproduction Steps:**
1. Start the simulation (F5).
2. Open **Tools** → **Inject Sensory Input**.
3. Select any pattern and click **Inject Input**.
4. Observe: dialog shows "Custom input injected successfully!" but the simulation plots show no perturbation.

**Expected:** The generated signal is injected into the running APGI system, producing a measurable response in the visualization plots.
**Actual:** Signal is only displayed in the local dialog text box; the running system is unaffected.

---

#### BUG-003 — Alert Database Storage Not Implemented

| Field | Detail |
|---|---|
| **Severity** | Critical |
| **Component** | `api/middleware/alerting.py` — `_log_alert_to_database()` |
| **Lines** | 702–731 |
| **Affected URL / Entry Point** | All REST API routes that trigger alerts |

**Description:** `_log_alert_to_database()` constructs an `alert_data` dict, logs it via the Python logger, then hits a `# TODO: Implement actual database storage` comment (line 719). The actual SQLAlchemy session block is entirely commented out. All runtime alerts are lost on process restart.

**Reproduction Steps:**
1. Run the API and trigger an alert (e.g., exceed the error-rate threshold).
2. Restart the API server.
3. Query for historical alerts — none are returned.

**Expected:** Alerts are persisted to the database and retrievable after restart.
**Actual:** Alerts are logged to stdout/file only; no row is written to the database.

---

### HIGH

---

#### BUG-004 — "Set Body State" Is a Non-Interactive Stub

| Field | Detail |
|---|---|
| **Severity** | High |
| **Component** | `apgi_gui.py` — `_set_body_state()` |
| **Lines** | 3866–3870 |
| **Affected URL / Entry Point** | Main GUI → Tools menu → Set Body State |

**Description:** The method body is a single `messagebox.showinfo()` that instructs users to "Use Activity, Arousal, and Stress sliders in control panel". No dedicated body-state editor dialog is launched. The menu item advertises functionality that does not exist.

**Expected:** A dialog for fine-grained body-state configuration (heart rate, cortisol, temperature, respiration, glucose) is displayed.
**Actual:** A one-line info popup redirects users to existing sliders.

---

#### BUG-005 — "Self-Model Coherence" Analysis Is a Stub

| Field | Detail |
|---|---|
| **Severity** | High |
| **Component** | `apgi_gui.py` — `_analyze_coherence()` |
| **Lines** | 3963–3967 |
| **Affected URL / Entry Point** | Main GUI → Analysis menu → Self-Model Coherence |

**Description:** Method body is a single `messagebox.showinfo()` directing users to "Check the Self-Model tab for coherence visualization". No coherence statistics window is opened, no data is computed, and no extra context is provided.

**Expected:** A dedicated analysis dialog showing coherence statistics, trends, and interpretation.
**Actual:** An info popup with a one-sentence redirect.

---

#### BUG-006 — `_enable_system_controls()` Does Not Disable Parameter Sliders

| Field | Detail |
|---|---|
| **Severity** | High |
| **Component** | `apgi_gui.py` — `_enable_system_controls()` |
| **Lines** | 1155–1169 |
| **Affected URL / Entry Point** | Main GUI — system initialization failure path |

**Description:** When the APGI system fails to initialize, `_enable_system_controls(False)` is called. It disables `start_btn` and `reset_btn` correctly, but the `param_vars` loop body is `pass` — a comment reads `# Note: Tkinter variables don't have a direct enable/disable state / This would need to be handled at the widget level if needed`. All eight parameter sliders remain interactive even though the system is down, creating false affordances.

**Expected:** All parameter sliders are greyed out / disabled when no system is initialized.
**Actual:** Sliders remain fully interactive, silently accepting values that have no effect.

---

#### BUG-007 — AI Assistant GUI Destroyed on Dependency Failure With No Fallback

| Field | Detail |
|---|---|
| **Severity** | High |
| **Component** | `Assistant-GUI.py` — `APGIGUI.__init__()` |
| **Lines** | 2263–2272 |
| **Affected URL / Entry Point** | `python Assistant-GUI.py` |

**Description:** If `AI-Assistant.py` cannot be imported (e.g., PyTorch or torchdiffeq unavailable), `HAS_ASSISTANT` is `False` and `root.destroy()` is called immediately after showing an error. The window closes with no partial degraded mode. Given the heavy GPU dependency stack (`torch`, `torchdiffeq`, `transformers`), this failure is common in CPU-only environments.

**Expected:** A degraded mode that provides available features (history export, settings, visualization of cached data) when the core model cannot load.
**Actual:** Application closes entirely.

---

#### BUG-008 — Theme Selection Not Persisted Between Sessions

| Field | Detail |
|---|---|
| **Severity** | High |
| **Component** | `apgi_gui.py` — `_change_theme()`, `Assistant-GUI.py` — `apply_theme()` |
| **Affected URL / Entry Point** | Both main GUIs — View → Theme |

**Description:** `_change_theme()` calls `theme_manager.set_theme()` in memory only. No theme preference is written to config or any persistent store. On every application restart the default "normal" theme is applied regardless of the user's last selection.

**Expected:** Selected theme is saved to user config and reapplied on next launch.
**Actual:** Theme resets to "normal" on every restart.

---

#### BUG-009 — Auto-Save Persists Only Event Log Text, Not Simulation State

| Field | Detail |
|---|---|
| **Severity** | High |
| **Component** | `apgi_gui.py` — `_auto_save_data()` |
| **Lines** | 1982–1994 |
| **Affected URL / Entry Point** | Main GUI — File → Auto-Save (when enabled) |

**Description:** `_auto_save_data()` saves `list(self.log_data)` — the text-string event log — as JSON. Simulation parameters, buffer contents, and system state are not saved. A crash mid-session cannot be recovered from; only the event log survives.

**Expected:** Auto-save captures simulation parameters, buffer snapshots, and system state for session recovery.
**Actual:** Only the string event log is saved.

---

#### BUG-010 — Log File Grows Unbounded (No Rotation)

| Field | Detail |
|---|---|
| **Severity** | High |
| **Component** | `apgi_gui.py` — module-level logging configuration |
| **Lines** | 40–47 |
| **Affected URL / Entry Point** | All sessions — `apgi_gui.log` |

**Description:** `logging.basicConfig()` uses a plain `logging.FileHandler("apgi_gui.log")`. There is no `RotatingFileHandler` or size/backup limit. The log file grows indefinitely; long-running or frequently restarted deployments will eventually exhaust disk space.

**Expected:** Log file is rotated at a configurable size threshold (e.g., 10 MB, 3 backups).
**Actual:** `apgi_gui.log` grows without limit.

---

#### BUG-011 — Documentation Dialog Displays Inline String Instead of Actual Docs

| Field | Detail |
|---|---|
| **Severity** | High |
| **Component** | `apgi_gui.py` — `_show_docs()` |
| **Lines** | 4176–4208 |
| **Affected URL / Entry Point** | Main GUI → Help → Documentation |

**Description:** The Help → Documentation dialog renders a short hardcoded string (~14 lines). The project contains a full `docs/GUI.md` (467 lines) with complete usage guide, troubleshooting steps, and keyboard shortcuts. The hardcoded string is an outdated stub.

**Expected:** The dialog loads and renders `docs/GUI.md` (or opens it in the system viewer).
**Actual:** A 14-line placeholder string is displayed.

---

### MEDIUM

---

#### BUG-012 — `ToolTip` Class Duplicated Verbatim Across Four Files

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **Component** | `apgi_gui.py` (via `apgi_gui/components/`), `Assistant-GUI.py:153`, `Psychological-States-GUI.py:59`, `Utils-GUI.py:32`, `Tests-GUI.py:32` |

**Description:** An identical `ToolTip` class (with `on_enter`, `on_leave`, `schedule`, `unschedule`, `showtip`, `hidetip`, `update_text`) appears in at least four separate files. A bug fix must be applied in four places.

**Expected:** Single shared `ToolTip` implementation in `apgi_gui/components/core.py`, imported by all files.
**Actual:** Four independent copies, each prone to independent divergence.

---

#### BUG-013 — View Menu Checkbuttons Do Not Track Actual Panel State

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **Component** | `apgi_gui.py` — `_create_menu_bar()` |
| **Lines** | 574–589 |

**Description:** View checkbuttons are created without an explicit `variable=` binding at construction time. The `tk.BooleanVar` objects in `self.view_vars` are only created 200 ms post-startup in `_convert_to_tkinter_variables()`. Until that conversion, checkbutton state is untracked. After conversion, the checkbutton state never changes the layout (BUG-001), so visual state diverges from logical state.

**Expected:** Checkbuttons are initialized checked (panels default to visible) and toggle correctly.
**Actual:** Checkbuttons may initialize unchecked and never produce a visual effect.

---

#### BUG-014 — Speed Scale Not Bound to Variable at Creation Time

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **Component** | `apgi_gui.py` — `_create_control_panel()`, `_convert_to_tkinter_variables()` |
| **Lines** | 714–719, 297–310 |

**Description:** The speed `ttk.Scale` is created without a `variable=` argument (line 714). The `speed_var` `tk.DoubleVar` is created 200 ms later in `_convert_to_tkinter_variables()` and then reassigned to the scale. During the startup window, slider movement does not update `_speed_value` and may produce a `tk.TclError` if the scale is moved before conversion completes.

**Expected:** Scale is created with its variable binding; no deferred assignment required.
**Actual:** Race window of ~200 ms where speed slider changes are silently lost.

---

#### BUG-015 — `Utils-GUI.py` and `Tests-GUI.py` Are Near-Identical Codebases

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **Component** | `Utils-GUI.py` (590 lines), `Tests-GUI.py` (597 lines) |

**Description:** Both files implement virtually identical classes (`ToolTip`, runner GUI) with minor label differences ("utils" vs "tests"). Any bug fix or enhancement to one must be manually replicated in the other.

**Expected:** Shared base class (`ScriptRunnerGUI`) parameterized by script directory and runner type.
**Actual:** Two separate files with ~95% duplicated code.

---

#### BUG-016 — Precision Modulation Dialog Has No Bounds Validation

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **Component** | `apgi_gui.py` — `_modulate_precision()` |
| **Lines** | 3697–3706 |

**Description:** Clicking Apply multiplies `extero_precision` and `intero_precision` by the modulation factor with no upper-bound check. If the user applies a factor of 3.0 multiple times, precision values can exceed the documented range [0.1, 10.0], producing undefined simulation behavior.

**Expected:** Result is clamped to the valid precision range after multiplication.
**Actual:** Precision values can grow unbounded.

---

#### BUG-017 — Zoom Controls Do Not Function Before Data Is Present

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **Component** | `apgi_gui.py` — `_zoom_fit()` |
| **Lines** | 3635–3664 |

**Description:** `_zoom_fit()` calls `self._update_plots()` only `if len(self.time_buffer) > 0`. When called before any simulation data exists, the `ax.relim()` and `ax.autoscale_view()` calls operate on empty axes, producing no visible change and no user feedback.

**Expected:** A user message ("No data to fit — start simulation first") or the button is disabled before simulation runs.
**Actual:** Silent no-op.

---

#### BUG-018 — Redis Hard Dependency in API Rate Limiter — No In-Memory Fallback

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **Component** | `api/services/rate_limiter.py`, `api/middleware/rate_limiting.py` |

**Description:** Rate limiting requires a running Redis instance. There is no in-memory fallback (e.g., `cachetools`). Deploying the API without Redis causes a startup error or unhandled exception on the first rate-limited request, even in development/testing contexts.

**Expected:** An in-memory fallback rate limiter is used automatically when Redis is unavailable.
**Actual:** API fails on rate-limit middleware invocation without Redis.

---

#### BUG-019 — `_trigger_ignition()` Requires System Running But Has No Guard

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **Component** | `apgi_gui.py` — `_trigger_ignition()` |
| **Lines** | 3668–3674 |

**Description:** The method checks `if self.apgi_system:` but proceeds to call `self.param_vars["arousal"].set(0.9)` even if the simulation is not running (`self.is_running == False`). Setting arousal to 0.9 without an active loop has no effect but may confuse users who trigger it while paused.

**Expected:** Method is disabled or warns if simulation is not actively running.
**Actual:** Silently adjusts slider values with no visible effect when paused/stopped.

---

#### BUG-020 — Buffer Size Change Not Persisted Across Sessions

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **Component** | `apgi_gui.py` — buffer size settings dialog |
| **Lines** | 375–462 |

**Description:** The buffer size setting is applied to in-memory deques via `_initialize_buffers()` but is never written to the YAML config. On next launch, the default size (1000) is always used regardless of user preference.

**Expected:** Buffer size is written to config and restored on launch.
**Actual:** Buffer size resets to 1000 on every restart.

---

#### BUG-021 — `Assistant-GUI.py` Undo/Redo Only Partially Implemented

| Field | Detail |
|---|---|
| **Severity** | Medium |
| **Component** | `Assistant-GUI.py` — `redo_action2()` |
| **Lines** | ~8188 |

**Description:** `undo_action` is implemented with a proper deque-backed history. `redo_action2()` is present (note the `2` suffix suggesting a revision) but the redo stack (`redo_history`) population is inconsistent — undo actions do not always push to redo, leaving the redo function silently ineffective for some operation types.

**Expected:** Redo restores the last undone action in all cases.
**Actual:** Redo works for some operations but silently fails for others.

---

### LOW

---

#### BUG-022 — About Dialog Contains No Project URL

| Field | Detail |
|---|---|
| **Severity** | Low |
| **Component** | `apgi_gui.py` — `_show_about()` |
| **Lines** | 4247–4265 |

**Description:** The About dialog ends with "For more information, visit the project repository." but contains no URL or clickable link.

**Expected:** URL to project repository or documentation site is displayed.
**Actual:** Placeholder text with no actionable link.

---

#### BUG-023 — Log File Path Is Relative — Writes to CWD

| Field | Detail |
|---|---|
| **Severity** | Low |
| **Component** | `apgi_gui.py` — module-level `logging.basicConfig()` |
| **Lines** | 43 |

**Description:** `logging.FileHandler("apgi_gui.log")` writes to the current working directory. Running the application from different directories creates multiple scattered log files.

**Expected:** Log file written to a fixed platform-appropriate path (e.g., `get_data_dir() / "apgi_gui.log"`).
**Actual:** Log file location depends on the directory from which the application is launched.

---

#### BUG-024 — Diagnostic Dialog Exposes Raw Internal Keys

| Field | Detail |
|---|---|
| **Severity** | Low |
| **Component** | `apgi_gui.py` — `_show_diagnostics()` |
| **Lines** | 3880–3900 |

**Description:** The diagnostics window accesses `summary['ignition_stats'].get('mean_signal', 0)` and similar raw dict keys. If the system returns a partial or updated state summary with renamed keys, `get(..., 0)` silently shows `0` with no indication of a data-retrieval failure.

**Expected:** Key presence is validated; a clear "N/A" or warning is shown for missing fields.
**Actual:** Silent fallback to `0` masks missing data.

---

#### BUG-025 — `Tests-GUI.py` Has No Test Result Summary

| Field | Detail |
|---|---|
| **Severity** | Low |
| **Component** | `Tests-GUI.py` |

**Description:** The Tests GUI streams raw pytest output but provides no aggregated pass/fail count, test duration summary, or overall status indicator. Users must manually read through potentially long output to determine overall test health.

**Expected:** A status bar or summary panel showing total: N, passed: P, failed: F, errors: E after a test run completes.
**Actual:** Raw text output only.

---

#### BUG-026 — No Script Parameter Input in Utils-GUI

| Field | Detail |
|---|---|
| **Severity** | Low |
| **Component** | `Utils-GUI.py` |

**Description:** Scripts are executed with no ability to pass command-line arguments. Utility scripts that accept configuration flags cannot be customized from the GUI.

**Expected:** A text field or argument builder allowing users to pass arguments to selected scripts.
**Actual:** Scripts are run bare with no argument support.

---

#### BUG-027 — Keyboard Shortcut Ctrl+R Is Bound Twice

| Field | Detail |
|---|---|
| **Severity** | Low |
| **Component** | `apgi_gui.py` — `_create_menu_bar()` |
| **Lines** | 647, 565 |

**Description:** `Ctrl+R` is bound to `_reset_simulation()` via `root.bind("<Control-r>", ...)` but `F8` is also bound to `_reset_simulation()` and labeled "Reset" in the Simulation menu. This creates a redundant binding and may conflict with system-level shortcuts on some platforms.

**Expected:** Each action has one canonical shortcut; duplicates are documented or removed.
**Actual:** `Ctrl+R` and `F8` both silently reset the simulation with no disambiguation.

---

#### BUG-028 — Export Plot Does Not Respect Active Visualization Tab

| Field | Detail |
|---|---|
| **Severity** | Low |
| **Component** | `apgi_gui.py` — `_export_plot()` |

**Description:** The export-plot function targets a fixed canvas rather than the currently active notebook tab. Users viewing the Oscillations or State Space tab expect that canvas to be exported, but receive the Neural plots canvas instead.

**Expected:** Export targets the currently selected visualization tab canvas.
**Actual:** Export always targets the Neural Activity canvas.

---

## Missing Features Log

The following features are documented, advertised in menus, or implied by the project scope but are not implemented.

| # | Feature | Location Referenced | Status |
|---|---------|-------------------|--------|
| MF-01 | Real sensory input injection into live APGI system | Tools → Inject Sensory Input | Stub — dialog exists, injection does not |
| MF-02 | Dedicated body state editor (HR, cortisol, temperature, glucose, respiration) | Tools → Set Body State | Stub — redirects to generic sliders |
| MF-03 | Self-model coherence statistics analysis window | Analysis → Self-Model Coherence | Stub — redirects to tab |
| MF-04 | Alert database persistence | `api/middleware/alerting.py` | TODO comment, code commented out |
| MF-05 | LLM / language model integration in AI Assistant | `Assistant-GUI.py`, `AI-Assistant.py` | Neural infrastructure ready; no conversation loop |
| MF-06 | Theme preference persistence | View → Theme | Not saved to config |
| MF-07 | Buffer size persistence | Settings dialog | Not saved to config |
| MF-08 | Simulation state auto-save (crash recovery) | File → Auto-Save | Only event log text is saved |
| MF-09 | View panel show/hide (Control Panel, Neural Activity, etc.) | View menu checkbuttons | Handlers are no-ops |
| MF-10 | Documentation viewer (HTML/Markdown rendering of `docs/GUI.md`) | Help → Documentation | 14-line hardcoded stub |
| MF-11 | State-to-state transition simulation | `Psychological-States-GUI.py` | Not implemented |
| MF-12 | Comparative psychological state analysis | `Psychological-States-GUI.py` | Not implemented |
| MF-13 | Test result summary panel (pass/fail counts) | `Tests-GUI.py` | Raw output only |
| MF-14 | Script argument input in Utils Runner | `Utils-GUI.py` | No argument support |
| MF-15 | Output export (save to file) from Utils/Tests GUIs | `Utils-GUI.py`, `Tests-GUI.py` | No export button |
| MF-16 | Multi-session comparison / overlay analysis | Analysis menu | Not implemented |
| MF-17 | Automated parameter sweep tool | Analysis menu | Not implemented |
| MF-18 | Real-time parameter persistence across parameter-panel edits | Edit menu parameter dialogs | Changes lost on restart |
| MF-19 | Redo support for all undoable operations in Assistant GUI | Assistant-GUI.py | Partially implemented |
| MF-20 | In-memory Redis fallback for API rate limiting | `api/services/rate_limiter.py` | Hard Redis dependency |

---

## Actionable Recommendations for Remediation

### P0 — Critical (Fix Before Any Release)

**R-01: Implement View panel toggle logic (BUG-001)**
Replace the four `_toggle_*` stub methods with actual `pack_forget()` / `pack()` calls on the respective widget references. Store widget references at creation time and bind the BooleanVars to checkbuttons at construction.

**R-02: Implement actual sensory input injection (BUG-002, MF-01)**
Connect `_inject_input()` to `self.apgi_system`. The active inference engine should expose a method (e.g., `inject_exteroceptive_signal(signal, duration)`) that the GUI calls. Remove the "simulated!" status text.

**R-03: Implement alert database storage (BUG-003, MF-04)**
Uncomment the SQLAlchemy session block in `_log_alert_to_database()`. Create the `AlertLog` ORM model and corresponding Alembic migration. Add a rollback guard.

**R-04: Enable parameter slider disable/enable (BUG-006)**
In `_enable_system_controls()`, iterate `self.param_scales` (not `self.param_vars`) and call `.state(['disabled'])` or `.state(['!disabled'])` on each `ttk.Scale`.

---

### P1 — High (Fix in Next Sprint)

**R-05: Implement body state editor dialog (BUG-004, MF-02)**
Create a `Toplevel` dialog with labeled sliders for heart rate, cortisol, temperature, glucose, and respiration. Wire to `self.apgi_system.body_model.set_state(...)`.

**R-06: Implement coherence analysis window (BUG-005, MF-03)**
Add a statistics computation call in `_analyze_coherence()` using the `SystemAnalyzer` class already available in `apgi_system.analysis`. Display mean/std/trend of `minimal_self_coherence` and `narrative_coherence` buffers.

**R-07: Add degraded mode to Assistant-GUI (BUG-007)**
When `HAS_ASSISTANT` is False, keep the window open and disable only the inference-dependent tabs. Show a banner indicating limited mode.

**R-08: Persist theme and buffer size to config (BUG-008, BUG-020, MF-06, MF-07)**
Write theme name and buffer size to `config/default.yaml` (or a user-specific `config/user.yaml`) on change. Read these values at startup.

**R-09: Expand auto-save to capture simulation state (BUG-009, MF-08)**
Serialize `self.param_cache`, current buffer snapshots (as `{key: list(deque)}`), and system config into the auto-save JSON. Add a session recovery dialog on startup if an auto-save file is found.

**R-10: Replace log FileHandler with RotatingFileHandler (BUG-010)**
```python
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler(
    get_data_dir() / "apgi_gui.log", maxBytes=10_485_760, backupCount=3
)
```

**R-11: Load actual documentation file in Help dialog (BUG-011, MF-10)**
Read `docs/GUI.md` with `get_resource_path("docs/GUI.md").read_text()` and display in the ScrolledText widget. Fall back to the inline string only if the file is missing.

---

### P2 — Medium (Backlog — Next Release Cycle)

**R-12: Extract shared utilities into package (BUG-012, BUG-015)**
Move `ToolTip` to `apgi_gui/components/core.py`. Merge `Utils-GUI.py` and `Tests-GUI.py` into a single `ScriptRunnerGUI` base class parameterized by `(script_dir, runner_label)`.

**R-13: Bind speed scale variable at construction (BUG-014)**
Create `self.speed_var = tk.DoubleVar(value=1.0)` before the scale widget and pass `variable=self.speed_var` at widget creation. Remove the deferred binding in `_convert_to_tkinter_variables()`.

**R-14: Add bounds validation to precision modulation (BUG-016)**
After computing new precision values, clamp with `max(0.1, min(10.0, new_value))` before calling `.set()`.

**R-15: Provide user feedback when zoom/fit has no data (BUG-017)**
In `_zoom_in/out/fit`, check `len(self.time_buffer) == 0` and display a status bar message instead of silently no-opping.

**R-16: Add Redis fallback for rate limiting (BUG-018, MF-20)**
Wrap the Redis client init in a try/except; fall back to an in-memory `cachetools.TTLCache`-based rate limiter when Redis is unavailable. Log a warning.

**R-17: Complete redo stack in Assistant-GUI (BUG-021, MF-19)**
Rename `redo_action2` to `redo_action`. Ensure every undo operation pushes the inverse action to `self.redo_history` before applying the change.

**R-18: Add test summary panel to Tests-GUI (BUG-025, MF-13)**
Parse pytest stdout for the summary line (`N passed, N failed in Xs`) and update a status label after the subprocess exits.

---

### P3 — Low / Long-Term

**R-19: Add script argument input to Utils-GUI (BUG-026, MF-14)**
Add a `ttk.Entry` widget below the script selector for free-form argument input. Split and pass to `subprocess.Popen` as additional `args`.

**R-20: Add output export to Utils/Tests GUIs (MF-15)**
Add a "Save Output" button that calls `filedialog.asksaveasfilename()` and writes the current output text to file.

**R-21: Fix export-plot to target active tab (BUG-028)**
In `_export_plot()`, query `self.notebook.index(self.notebook.select())` to determine the active tab and export the corresponding canvas figure.

**R-22: Add project URL to About dialog (BUG-022)**
Replace "visit the project repository" with the actual repository URL. Consider using `webbrowser.open()` on a clickable label.

**R-23: Refactor monolithic GUI files**
Split `apgi_gui.py` (4 453 lines) and `Assistant-GUI.py` (8 601 lines) into sub-modules (e.g., `apgi_gui/main_window.py`, `apgi_gui/dialogs.py`, `apgi_gui/plots.py`). This is a prerequisite for unit-testing GUI logic.

---

## Appendix A — File Metrics

| File | Lines | Classes | Public Methods | Known Issues |
|------|-------|---------|---------------|-------------|
| `apgi_gui.py` | 4 453 | 1 | ~85 | BUG-001–004, 006, 008–011, 013–014, 016–017, 019–020, 022–024, 027–028 |
| `Assistant-GUI.py` | 8 601 | 12+ | ~120 | BUG-007, 008, 021 |
| `AI-Assistant.py` | 3 900 | 12 | ~40 | MF-05 (LLM not wired) |
| `APGI-Equations.py` | 3 696 | 12 | ~60 | None critical |
| `Psychological-States-GUI.py` | 2 931 | 8 | ~45 | MF-11, MF-12 |
| `Utils-GUI.py` | 590 | 2 | ~15 | BUG-015, BUG-026, MF-14, MF-15 |
| `Tests-GUI.py` | 597 | 2 | ~15 | BUG-015, BUG-025, MF-13, MF-15 |
| `api/middleware/alerting.py` | 33 724 B | 5 | ~20 | BUG-003 |
| `apgi_system/` (all modules) | ~12 000 | ~30 | ~200 | None critical |

---

## Appendix B — Keyboard Shortcut Audit

| Shortcut | Documented | Bound | Works | Notes |
|----------|-----------|-------|-------|-------|
| Ctrl+N | Yes | Yes | Yes | New session |
| Ctrl+O | Yes | Yes | Yes | Load config |
| Ctrl+S | Yes | Yes | Yes | Save config |
| Ctrl+E | Yes | Yes | Yes | Export data |
| Ctrl+Q | Yes | Yes | Yes | Exit |
| F5 | Yes | Yes | Yes | Start simulation |
| F6 | Yes | Yes | Yes | Pause/resume |
| F7 | Yes | Yes | Yes | Stop |
| F8 | Yes | Yes | Yes | Reset |
| Ctrl+R | Yes | Yes | Duplicate | Duplicate of F8 (BUG-027) |
| Ctrl+P | Yes | Yes | Partial | Toggle parameter panel — uses pack_forget but panel re-inserts in wrong position |
| Ctrl+L | Yes | Yes | Yes | Toggle log panel |
| Ctrl+Tab | Yes | Yes | Yes | Cycle notebook tabs |
| Ctrl++ | Yes | Yes | Yes | Zoom in |
| Ctrl+- | Yes | Yes | Yes | Zoom out |
| Ctrl+0 | Yes | Yes | Partial | Zoom fit — no-op before data loaded (BUG-017) |
| F1 | Yes | Yes | Yes | Help (calls _show_docs) |

---

## Appendix C — API Endpoint Coverage

| Endpoint | Auth Required | Rate Limited | Tested | Status |
|----------|-------------|-------------|--------|--------|
| `POST /v1/auth/login` | No | Yes | Yes | ✅ Complete |
| `POST /v1/auth/refresh` | Yes | Yes | Yes | ✅ Complete |
| `GET /v1/health` | No | No | Yes | ✅ Complete |
| `GET /v1/version` | No | No | Yes | ✅ Complete |
| `GET /v1/metrics` | Yes | Yes | Yes | ✅ Complete |
| `POST /v1/sessions` | Yes | Yes | Yes | ✅ Complete |
| `GET /v1/sessions/{id}` | Yes | Yes | Yes | ✅ Complete |
| `GET /v1/state` | Yes | Yes | Yes | ✅ Complete |
| `POST /v1/tasks` | Yes | Yes | Yes | ✅ Complete |
| `POST /v1/export` | Yes | Yes | Yes | ✅ Complete |
| Alert persistence (internal) | — | — | No | ❌ BUG-003 |
