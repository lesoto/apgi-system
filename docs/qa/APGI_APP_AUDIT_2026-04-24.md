# APGI System Application Quality Audit (macOS-focused)

**Audit date:** 2026-04-24  
**Auditor role:** Senior macOS developer + QA engineer  
**Scope:** Python APGI desktop GUI (`apgi_gui`), API integration surface (`api`), configuration, and user-facing docs.

## Executive Summary

The application is **partially functional but significantly incomplete**. Core simulation start/pause/stop flows exist, but many advertised GUI capabilities are wired to no-op stubs, and at least one callback contract bug can suppress meaningful error handling in runtime failure scenarios. Documentation materially overstates delivered functionality versus the current implementation.

**Overall health/completeness score: 58/100.**

- This score reflects a working baseline architecture with broad module coverage and successful bytecode compilation, but substantial feature gaps and security/configuration hygiene risks.

## Evidence-driven findings across six dimensions

## 1) Functional Bugs

### Critical

1. **Error callback type mismatch can break GUI error handling path**  
   - GUI error handler expects a dict and calls `data.get(...)`.  
   - Simulation controller passes `str(e)` to `on_error`.  
   - In an exception path, this can trigger another exception in UI callback processing instead of showing a reliable actionable error to the user.

### High

2. **Most menu actions are unimplemented (silent no-op behavior)**  
   - Numerous menu callbacks are `pass`, including settings, analysis, tooling, help, and view toggles. Users can click controls that do nothing.

3. **`--config` CLI argument accepted but not implemented**  
   - The CLI parser accepts `--config` and then intentionally performs no load operation.

4. **Simulation stop/reset lifecycle lacks thread join/synchronization**  
   - `stop()` only flips booleans and does not join the simulation thread. This can cause race conditions during rapid start/stop/reset cycles.

### Medium

5. **Displayed runtime metrics include placeholders instead of real values**  
   - Ignition events are hard-coded as `"0"` in the status update path.

6. **Documentation/feature contract mismatch can be interpreted as functional defects**  
   - User docs describe many implemented behaviors not present in running UI.

## 2) UI/UX Issues (including macOS HIG fit)

### High

1. **Keyboard shortcut accelerators are displayed but not actually bound**  
   - Menu entries show accelerators, but no key bindings are wired in GUI code.

2. **Main user flows expose dead controls**  
   - Tools, Analysis, Help, and several View/Edit actions appear active while invoking unimplemented handlers.

### Medium

3. **Feature parity mismatch with docs creates UX trust failures**  
   - Docs promise six visualization tabs and rich interactions; implementation provides only three tabs.

4. **Accessibility gaps**  
   - No visible implementation of tooltips, keyboard focus guidance, or accessibility-specific affordances for key controls in `apgi_gui` modules reviewed.

## 3) Performance & Stability

### High

1. **Periodic UI loop performs repeated process inspection and imports**  
   - `psutil` import and process memory sampling happen every 100ms in the UI timer loop; avoidable overhead on lower-power laptops.

### Medium

2. **Potential instability under stress from unsynchronized thread lifecycle**  
   - No join or deterministic teardown behavior in simulation controller may cause transient state races.

3. **Environment/dependency fragility for local test execution**  
   - Project metadata requires Python >=3.11, but the current environment is 3.10; also missing runtime test deps causes immediate pytest import failure.

## 4) Missing Settings & Features

### High

1. **Settings panels and advanced configuration actions are largely non-functional**  
   - Edit menu entries and many configuration helpers are stubs.

2. **Help and documentation hooks in-app are unimplemented**  
   - Documentation/shortcuts/about actions exist in menu but handlers are `pass`.

3. **Data export/config I/O interactions are placeholders**  
   - Current callbacks only log text for load/save/export actions.

### Medium

4. **Advertised advanced visualization tabs absent**  
   - Self-model, oscillations, and 3D state-space tabs are documented but not implemented in `VisualizationPanel`.

## 5) Security & Privacy

### Critical

1. **Repository contains committed `.env` with placeholder/credential-like secrets and mixed environment declarations**  
   - Includes API, DB, JWT, and service credential variables in one tracked file. Even placeholder values normalize insecure secret-handling patterns and increase deployment misconfiguration risk.

### High

2. **Ambiguous env composition raises accidental insecure deployment risk**  
   - Mixed sections and overlapping variables can cause configuration confusion (e.g., multiple password-like values, development-centric reload settings).

## 6) Documentation & Help

### High

1. **User-facing guide materially overstates shipped capability**  
   - Claims 100% feature access, extensive tabs, and operational flows that are not currently implemented.

2. **Launch instructions reference non-existent entry scripts**  
   - Docs instruct `python run_gui.py` / `python apgi_gui.py`, but these files are absent in repository root.

### Medium

3. **In-app help actions are not wired**  
   - Even where docs exist, GUI help actions do nothing.

## Severity & priority matrix (top items)

| ID | Issue | Severity | Priority | Why |
|---|---|---|---|---|
| F-01 | Error callback payload mismatch (`str` vs `dict`) | Critical | P0 | Can fail during error handling path, masking root failures |
| S-01 | Tracked `.env` includes credential-like values/placeholders | Critical | P0 | Security hygiene and accidental prod misconfiguration risk |
| F-02 | Major menu functionality is no-op (`pass`) | High | P1 | Core user-facing controls appear functional but do nothing |
| D-01 | Docs overstate implementation | High | P1 | User trust/support burden; false expectations |
| U-01 | Accelerator labels without key bindings | High | P1 | UX inconsistency and accessibility regression |
| P-01 | No thread join during stop/reset | High | P1 | Stability risk under repeated runs |
| P-02 | UI loop imports/samples process each 100ms | Medium | P2 | Unnecessary overhead and battery impact |
| D-02 | Doc launch commands point to missing files | High | P1 | Onboarding blockers |

## Score rationale (58/100)

- **+22**: Broad architecture and modularization are present; code compiles successfully across major packages.  
- **+12**: Core simulation controls (start/pause/stop/reset) and plotting baseline exist.  
- **-20**: High volume of user-visible unimplemented handlers and missing settings workflows.  
- **-15**: Security/config hygiene concerns (`.env` handling and mixed credentials).  
- **-10**: Documentation mismatch and invalid run instructions.  
- **-9**: Stability/performance concerns in thread lifecycle and UI timer loop.

## Actionable plan to reach 90-100

1. **Fix P0 issues first (1-2 days)**
   - Standardize error callback contracts: always pass structured dicts; add typed protocol tests.
   - Remove tracked `.env` from VCS, add `.env.example`, rotate secrets, and enforce startup validation in production.

2. **Close high-impact feature gaps (3-7 days)**
   - Implement all currently exposed menu actions or disable/hide unfinished actions behind feature flags.
   - Implement actual config load/save/export flows with robust validation and error dialogs.
   - Wire keyboard shortcuts with platform-aware bindings (Command on macOS).

3. **Stability/performance hardening (2-4 days)**
   - Add thread join with timeout and deterministic stop/reset state machine.
   - Move `psutil.Process()` creation out of hot loop; sample metrics at a lower cadence (e.g., 500-1000ms).

4. **UI/UX and accessibility completion (2-5 days)**
   - Add tooltips, focus outlines, keyboard traversal, and reduced-motion options.
   - Align terminology, status states, and panel visibility toggles with actual behavior.

5. **Documentation correctness sweep (1-2 days)**
   - Rewrite GUI guide to reflect shipped features only.
   - Replace invalid launch commands with tested entry points.
   - Add in-app help links wired to existing docs.

6. **Quality gates (ongoing)**
   - Add CI checks to fail on: undocumented stubs exposed in production UI, missing key bindings for declared accelerators, and stale docs-to-feature mismatch assertions.

## Commands executed during audit

- `python -V`
- `pytest -q tests/test_cli_smoke.py tests/test_gui_components_refactored.py tests/test_input_validation.py`
- `python -m compileall apgi_gui api apgi_framework`
- `rg -n "bind\(|bind_all|event_generate|accelerator" apgi_gui/main.py apgi_gui/components/menu_bar.py`
- `rg -n "TODO|FIXME|pass\s*$|placeholder|Stub methods|return None  # Placeholder|lambda: None" apgi_gui apgi_framework api`

## Key source references used

- `apgi_gui/main.py`
- `apgi_gui/controllers/simulation_controller.py`
- `apgi_gui/components/visualization_panel.py`
- `apgi_gui/components/menu_bar.py`
- `apgi_gui/cli.py`
- `.env`
- `docs/GUI-Guide.md`
- `pyproject.toml`
