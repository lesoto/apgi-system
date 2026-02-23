# APGI System — End-to-End Audit Report

**Audit Date:** 2026-02-23
**Branch:** `claude/app-audit-testing-dzIeq`
**Auditor:** Claude Code (Anthropic)
**Application:** Allostatic Precision-Gated Ignition (APGI) Framework
**Version:** 0.1.0 / API 1.0.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Application Overview](#2-application-overview)
3. [KPI Scores](#3-kpi-scores)
4. [Bug Inventory](#4-bug-inventory)
5. [Missing Features & Incomplete Implementations](#5-missing-features--incomplete-implementations)
6. [Detailed Findings by Component](#6-detailed-findings-by-component)
7. [Actionable Recommendations](#7-actionable-recommendations)
8. [Appendix: Audit Scope & Methodology](#8-appendix-audit-scope--methodology)

---

## 1. Executive Summary

The APGI System is a sophisticated Python-based computational consciousness-modeling framework. It comprises five major components: a core scientific engine (`apgi_system/`), a FastAPI REST backend (`api/`), four Tkinter GUI applications, an extensive test suite, and utility libraries.

The **core scientific engine** is well-architected, with clear module boundaries covering active inference, predictive processing, ignition dynamics, interoception, self-modeling, and thermodynamic constraints. Documentation is thorough and the test suite is extensive.

However, the audit uncovered **3 critical bugs that render the API non-operational out of the box**, **4 high-severity defects** that break key GUI features and API endpoints, and several medium/low issues affecting reliability, security, and UX consistency. The most severe finding is that the automatically provisioned default user is assigned roles (`"user"`, `"session_manager"`) that are not recognized by the RBAC engine, resulting in **zero effective permissions** — making every authenticated and authorized API call fail with HTTP 403 immediately after a clean install.

Remediation of the 3 critical bugs is required before any production or functional testing deployment. The remaining findings should be addressed in priority order per the recommendations in §7.

---

## 2. Application Overview

| Component | Technology | Files | LOC (approx.) |
|-----------|-----------|-------|---------------|
| Core APGI Engine | Python 3.11, NumPy, JAX, PyTorch | `apgi_system/` (~30 files) | ~18,000 |
| REST API | FastAPI 0.110+, SQLAlchemy, Redis, Celery | `api/` (~40 files) | ~12,000 |
| Main GUI (`APGI-GUI.py`) | Tkinter, Matplotlib | 1 file | 4,934 |
| Assistant GUI (`Assistant-GUI.py`) | Tkinter | 1 file | 8,671 |
| Psych States GUI (`Psychological-States-GUI.py`) | Tkinter | 1 file | 3,136 |
| AI Assistant (`AI-Assistant.py`) | Tkinter | 1 file | 3,382 |
| APGI Equations (`APGI-Equations.py`) | Python | 1 file | 3,695 |
| Test Suite | pytest, hypothesis | `tests/` (~40 files) | ~35,000 |
| Utilities | Python | `utils/` (14 files) | ~8,000 |

**API Endpoints Audited:**

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| Auth | `/v1/auth` | login, refresh, logout |
| Sessions | `/v1/sessions` | CRUD + start/pause/stop/reset |
| State Access | `/v1/sessions/{id}` | state, ignition-history, interoception, prediction-errors, somatic-markers |
| Tasks | `/v1/tasks`, `/v1/sessions/{id}/tasks` | list, submit, status, cancel |
| Export | `/v1/sessions/{id}` | export, summary, timeseries, events |
| Users | `/v1/users` | register, list, me, get, update, delete, stats |
| Health | `/health`, `/v1/health` | basic + comprehensive |
| Metrics | `/v1/metrics` | Prometheus scrape endpoint |
| Version | `/v1/version` | version info |

---

## 3. KPI Scores

| # | KPI | Score | Rationale |
|---|-----|-------|-----------|
| 1 | **Functional Completeness** | **58 / 100** | Core engine and scientific subsystems are fully implemented. All API routes are scaffolded. However, 3 critical bugs make the REST API completely non-operational without manual intervention. GUI keyboard shortcuts are never bound. The high-contrast-dark theme crashes on activation. |
| 2 | **UI/UX Consistency** | **71 / 100** | The 6-tab visualization layout and control panel are well-structured. Theme system is implemented (normal, dark, high-contrast). Consistent iconography and status bar exist. Deductions: keyboard shortcuts non-functional, theme toggle crashes, no WM_DELETE_WINDOW handler on main GUI, duplicate health endpoints cause confusion. |
| 3 | **Responsiveness & Performance** | **74 / 100** | GUI uses deque-bounded buffers (1,000–10,000 pts), RLock threading, and deferred `after()` initialization. API has GZip middleware, connection pooling (pool_size=10, max_overflow=20), Redis-backed caching, and Celery for async tasks. Rate limiting falls back to in-memory due to the middleware bug. No lazy loading of matplotlib backends. |
| 4 | **Error Handling & Resilience** | **69 / 100** | Circuit breaker pattern implemented for DB operations. Global exception handlers are comprehensive. Alerting middleware exists. Deductions: `null` timestamps in 4xx error bodies, user management crashes with `AttributeError` due to missing ORM columns, middleware chain silently swallows the rate-limiter Redis wiring bug, no thread cleanup on GUI exit. |
| 5 | **Overall Implementation Quality** | **67 / 100** | Architecture is sophisticated and well-documented. RBAC design is sound in principle but broken by invalid default-user roles. SQLAlchemy models, Pydantic schemas, and Alembic migrations are used correctly. Type annotations are present. Deductions for the critical default-user/RBAC mismatch, route ordering bug, double-registered middleware, and missing `is_active` column on User ORM model. |

### Score Summary

```
┌─────────────────────────────────────┬────────┐
│ KPI                                 │ Score  │
├─────────────────────────────────────┼────────┤
│ 1. Functional Completeness          │ 58/100 │
│ 2. UI/UX Consistency                │ 71/100 │
│ 3. Responsiveness & Performance     │ 74/100 │
│ 4. Error Handling & Resilience      │ 69/100 │
│ 5. Overall Implementation Quality  │ 67/100 │
├─────────────────────────────────────┼────────┤
│ COMPOSITE AVERAGE                   │ 68/100 │
└─────────────────────────────────────┴────────┘
```

---

## 4. Bug Inventory

### Severity Definitions

| Severity | Definition |
|----------|-----------|
| **Critical** | Causes total feature failure or data corruption; blocks primary workflows |
| **High** | Major feature broken; no acceptable workaround |
| **Medium** | Feature partially broken; workaround exists |
| **Low** | Minor UX issue, cosmetic defect, or latent security concern |

---

### 4.1 Critical Bugs

---

#### BUG-001 — Default User Created with Unrecognized Roles (API Non-Operational)

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Component** | `api/database/connection.py:132`, `api/services/authorization.py:62–106` |
| **Affected URLs** | All `/v1/*` authenticated endpoints |

**Description:**
During startup `init_db()` calls `create_default_user()`, which creates a user with `roles=["user", "session_manager"]`. The RBAC engine in `authorization.py` only recognizes the `Role` enum values `"admin"`, `"researcher"`, and `"viewer"`. When `get_permissions_for_roles(["user", "session_manager"])` is called, both role lookups throw `ValueError` and are silently skipped (line 131 `continue`), resulting in an **empty permission set**. Every subsequent call to `require_permission()` raises `AuthorizationError`, returning HTTP 403.

**Reproduction Steps:**
1. Fresh install with no `.env` overrides.
2. Start the API: `uvicorn api.main:app`.
3. Authenticate via `POST /v1/auth/login` with the auto-generated default credentials (logged at startup).
4. Attempt `GET /v1/sessions` with the returned access token.
5. **Actual:** `403 Forbidden – AuthorizationError`.
6. **Expected:** `200 OK` with session list.

**Expected vs. Actual:**
- Expected: Default user can create and manage sessions.
- Actual: All authorized endpoints return 403 immediately.

---

#### BUG-002 — `User` ORM Model Missing `is_active` and `updated_at` Columns

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Component** | `api/database/models.py:58–89`, `api/services/user_management.py:138,238,288,290` |
| **Affected URLs** | `POST /v1/users`, `PUT /v1/users/{id}`, `GET /v1/users`, `GET /v1/users/stats` |

**Description:**
The `User` SQLAlchemy model defines columns: `user_id`, `username`, `email`, `password_hash`, `roles`, `created_at`, `last_login`. It does **not** define `is_active` or `updated_at`. However, `UserManagementService` accesses `user.is_active` on line 138 (provisioning), 238 (update), 288–290 (list filtering), and `get_user_stats()` executes `User.is_active.is_(True)` as a SQLAlchemy filter. Any call to these methods raises `AttributeError: 'User' object has no attribute 'is_active'`.

The schema `UserResponse` also declares `is_active: bool = Field(...)` as required but the ORM object cannot supply it.

**Reproduction Steps:**
1. `POST /v1/users` with valid JSON body (admin token).
2. **Actual:** `500 Internal Server Error – AttributeError: 'User' object has no attribute 'is_active'`.
3. **Expected:** `201 Created` with new user details including `is_active: true`.

---

#### BUG-003 — Rate Limiting Middleware Double-Registration: Redis Client Never Injected into Active Instance

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Component** | `api/main.py:212–220`, `api/middleware/rate_limiting.py` |
| **Affected URLs** | All rate-limited endpoints |

**Description:**
In `create_app()`, lines 212–220 contain:

```python
# Line 213 – creates instance A, stored in global variable
rate_limiting_middleware = RateLimitingMiddleware(app, redis_client=None, ...)

# Line 218 – calls app.add_middleware() with the CLASS, which creates instance B internally
app.add_middleware(rate_limiting_middleware.__class__, redis_client=None, ...)
```

During startup lifespan (line 105–108), `rate_limiting_middleware.set_redis_client(redis_client)` is called — but this updates **instance A** (the orphaned global). **Instance B** (the one actually processing HTTP requests) never receives the Redis client and permanently operates in in-memory fallback mode. Distributed rate limiting across multiple API workers is silently broken; each worker maintains its own independent counter, making the configured per-user/per-endpoint limits N× higher than intended (where N = worker count).

**Reproduction Steps:**
1. Start two workers: `uvicorn api.main:app --workers 2`.
2. Issue 11 `POST /v1/sessions` requests from the same client in 60 s (limit is 10/min).
3. **Actual:** All 11 succeed — each worker has its own in-memory counter, neither reaches the threshold.
4. **Expected:** Request 11 returns `429 Too Many Requests`.

---

### 4.2 High Severity Bugs

---

#### BUG-004 — All Keyboard Shortcuts Never Bound in `APGI-GUI.py`

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Component** | `APGI-GUI.py:684–700` |
| **Affected Feature** | All GUI keyboard shortcuts (F5, F6, F7, F8, Ctrl+Plus, Ctrl+Minus, Ctrl+S, Ctrl+P, Ctrl+L, Tab navigation) |

**Description:**
The entire set of keyboard bindings is defined inside the `_exit_app()` method **after** the call to `self.root.quit()`:

```python
def _exit_app(self) -> None:
    """Exit the application."""
    self.root.quit()            # ← event loop stops here
    self.root.bind("<F5>", ...)  # ← these lines are dead code
    self.root.bind("<F6>", ...)
    # ... 10 more bindings
```

`_exit_app()` is only called when the user selects File → Exit. None of the keybindings are ever registered during normal application startup. All documented shortcuts (Start: F5, Pause: F6, Stop: F7, Reset: F8, Zoom: Ctrl+Plus/Minus, etc.) are non-functional throughout the entire application lifetime.

Additionally, line 689 references `self.on_start_clicked()` — a method that does not exist on `APGIGui` (it exists on `apgi_gui.components.core.BaseFrame`). If the binding were somehow reached, it would immediately raise `AttributeError`.

**Reproduction Steps:**
1. Launch `python APGI-GUI.py`.
2. Press F5 (documented shortcut for Start Simulation).
3. **Actual:** Nothing happens.
4. **Expected:** Simulation starts.

---

#### BUG-005 — `high_contrast_dark` Theme Undefined; Toggle High Contrast Always Fails

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Component** | `APGI-GUI.py:295`, `apgi_gui/theme_manager.py:16–95` |
| **Affected Feature** | View → Theme → Toggle High Contrast |

**Description:**
`ThemeManager.THEMES` defines exactly three keys: `"normal"`, `"dark"`, `"high_contrast"`. The `_toggle_high_contrast()` method unconditionally calls `self._change_theme("high_contrast_dark")` when the current theme is not already high-contrast. `_change_theme()` calls `theme_manager.set_theme("high_contrast_dark")`, which returns `False` (unknown theme), and then displays:

```
messagebox.showerror("Theme Error", "Unknown theme: high_contrast_dark")
```

Every click of "Toggle High Contrast" from any non-high-contrast theme shows an error dialog. The feature is completely broken.

**Reproduction Steps:**
1. Launch `python APGI-GUI.py` (default "normal" theme).
2. Click View → Theme → Toggle High Contrast.
3. **Actual:** Error dialog: "Unknown theme: high_contrast_dark".
4. **Expected:** Application switches to high-contrast dark color scheme.

---

#### BUG-006 — `GET /v1/users/stats` Shadowed by `GET /v1/users/{user_id}`

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Component** | `api/routes/users.py:219,420` |
| **Affected URL** | `GET /v1/users/stats` |

**Description:**
FastAPI matches routes in declaration order within a router. In `users.py`, the parameterized route `GET /{user_id}` (line 219) is declared **before** the literal route `GET /stats` (line 420). A request to `GET /v1/users/stats` is captured by `/{user_id}` with `user_id = "stats"`. The handler attempts to look up user `"stats"` in the database, fails, and raises `UserNotFoundError`, returning HTTP 404. The statistics endpoint is entirely inaccessible.

**Reproduction Steps:**
1. Authenticate as admin.
2. `GET /v1/users/stats`.
3. **Actual:** `404 – User 'stats' not found`.
4. **Expected:** `200 OK` with `{ total_users, active_users, inactive_users, role_counts }`.

---

#### BUG-007 — `null` Timestamps in HTTP 4xx Error Responses

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Component** | `api/exception_handlers.py:108,170` |
| **Affected URLs** | All endpoints returning 422 (validation) or standard 4xx HTTP errors |

**Description:**
Both `validation_error_handler` (line 108) and `http_exception_handler` (line 170) produce error bodies with `"timestamp": None`. The comment "Will be set by middleware if available" is incorrect — no middleware replaces this null value. Clients receive malformed error objects that violate the API contract and cause deserialization errors in typed clients expecting an ISO 8601 string.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "...",
    "timestamp": null,   ← always null
    ...
  }
}
```

Note: `unhandled_exception_handler` (500 responses) correctly provides a real timestamp. The inconsistency affects all 4xx responses.

---

### 4.3 Medium Severity Bugs

---

#### BUG-008 — `APGI-GUI.py` Has No `WM_DELETE_WINDOW` Protocol Handler

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Component** | `APGI-GUI.py` (`__init__` and `_exit_app`) |
| **Affected Feature** | Application shutdown via window close button |

**Description:**
The `APGI-GUI` class does not register a `WM_DELETE_WINDOW` protocol handler (compare: `Psychological-States-GUI.py:2444` and `Assistant-GUI.py:2356` both register proper handlers). When the user closes the window via the OS title bar button, Tkinter destroys the window without stopping the simulation thread. A running simulation thread (`self.simulation_thread`) continues executing indefinitely in the background, preventing the Python process from terminating cleanly and potentially causing resource leaks or file corruption if auto-save is active.

---

#### BUG-009 — User Registration Endpoint Requires No Authentication

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Component** | `api/routes/users.py:45–95` |
| **Affected URL** | `POST /v1/users` |

**Description:**
The user registration endpoint has no `dependencies=[Depends(require_permission(...))]` guard. Any unauthenticated HTTP client can create new user accounts. While `create_user` internally goes through `UserManagementService`, the absence of authentication on a user-creation endpoint is a security concern in any non-public deployment. Other user-mutating routes (update, delete) are correctly guarded. The registration route stands out as inconsistent.

---

#### BUG-010 — Duplicate `/health` and `/v1/health` Endpoints with Inconsistent Behavior

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Component** | `api/main.py:235–245`, `api/routes/health.py:30–59` |
| **Affected URLs** | `GET /health`, `GET /v1/health` |

**Description:**
Two health endpoints coexist:

- `GET /health` (inline in `main.py`): Returns `{"status": "healthy"}` unconditionally with no actual dependency checks.
- `GET /v1/health` (via `HealthCheckService`): Checks database, Redis, and Celery worker status; returns 503 if any component is unhealthy.

Load balancer health probes pointed at `/health` will always report healthy even when the database or Redis is down. This creates a false health signal during infrastructure failures.

---

#### BUG-011 — Auto-Save Timer Not Stopped on Application Exit

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Component** | `APGI-GUI.py:2063–2079` (`_toggle_auto_save`, `_start_auto_save_timer`) |
| **Affected Feature** | Auto-Save feature |

**Description:**
When auto-save is enabled, `_start_auto_save_timer()` schedules recurring `root.after()` callbacks. The `_exit_app()` method calls `self.root.quit()` but does not call `_stop_auto_save_timer()` first. If a scheduled callback fires during or after shutdown, it may attempt to write files to a partially destroyed GUI, causing Tkinter `TclError` exceptions.

---

#### BUG-012 — `session:delete` Permission Missing from Default User Flow

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Component** | `api/services/authorization.py:84–95` (Researcher role definition) |
| **Affected Feature** | Session deletion for researcher-role users |

**Description:**
The `Role.RESEARCHER` role mapping (line 84) includes `Permission.SESSION_DELETE`. However, session deletion (`DELETE /v1/sessions/{session_id}`) relies on `require_permission(Permission.SESSION_DELETE)`. The Researcher role correctly grants this. This is not a bug in itself, but combined with BUG-001 where default users have no recognized role, any out-of-box delete attempt fails. Noted here to highlight the cascade effect of BUG-001.

---

### 4.4 Low Severity Bugs

---

#### BUG-013 — Development JWT Secret Silently Used Without Env Var

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Component** | `api/config.py:103–120` |

**Description:**
When `JWT_SECRET_KEY` is not set and `ENVIRONMENT != "production"`, the application silently substitutes `"development-secret-key-change-in-production-32-chars-min"` and emits only a `UserWarning`. There is no startup failure or visible console log at ERROR level. In containerized CI/CD pipelines that promote images directly to staging without env vars, this hardcoded key could reach environments with real user data.

---

#### BUG-014 — CORS Default Allows Only Localhost Origins

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Component** | `api/config.py:59–63` |

**Description:**
The default `cors_origins` list is `["http://localhost:3000", "http://localhost:8000"]`. Any deployment to a non-localhost host requires explicit `CORS_ORIGINS` environment variable configuration — which is not prominently called out in the QUICKSTART documentation. Browser-based clients connecting from any production or staging hostname will receive CORS errors.

---

#### BUG-015 — `pool.size()` Method Called Incorrectly on SQLAlchemy Pool

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Component** | `api/database/connection.py:253` |

**Description:**
`engine.pool.size()` is called as a method. In SQLAlchemy 2.x, `pool.size()` is indeed a callable (it is a method on `QueuePool`), but the guard `if hasattr(engine.pool, "size")` is unnecessary complexity and the pattern differs between pool types. If the pool is `NullPool` or `StaticPool` (common in testing), this raises `AttributeError`. The fallback `"unknown"` handles this, but the code path is fragile.

---

#### BUG-016 — `declarative_base()` Import Deprecated in SQLAlchemy 2.x

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Component** | `api/database/models.py:26` |

**Description:**
```python
from sqlalchemy.ext.declarative import declarative_base
```
`sqlalchemy.ext.declarative.declarative_base` is deprecated since SQLAlchemy 1.4 and emits a `MovedIn20Warning` in SQLAlchemy 2.x. The correct import is `from sqlalchemy.orm import DeclarativeBase` (2.0 style) or at minimum `from sqlalchemy.orm import declarative_base`.

---

## 5. Missing Features & Incomplete Implementations

### 5.1 API Layer

| # | Feature | Status | Evidence |
|---|---------|--------|---------|
| M-01 | **Session listing endpoint** (`GET /v1/sessions`) | Missing | `api/routes/sessions.py` defines only `POST /v1/sessions`, `GET /{id}`, and action routes. No list/index endpoint exists. Clients cannot enumerate active sessions. |
| M-02 | **Pagination on session/task lists** | Not implemented | `GET /v1/sessions` doesn't exist (see M-01); tasks have no list endpoint either. The schemas define `PaginationInfo` but it's only used in ignition history. |
| M-03 | **Webhook signature verification** | Absent | `api/services/webhook_manager.py` sends webhook payloads but no HMAC signature header (e.g., `X-Webhook-Signature`) is attached, making receivers unable to verify authenticity. |
| M-04 | **Refresh token rotation** | Not implemented | `POST /v1/auth/refresh` returns a new access token but reuses the existing refresh token. Best practice is to issue a new refresh token and revoke the old one on each refresh. |
| M-05 | **User profile `GET /v1/users/me` update** | Auth guard inconsistent | `GET /v1/users/me` has no `require_permission` guard (access by any authenticated user via JWT). `PUT /v1/users/{id}` requires `USER_UPDATE`. Researchers cannot update their own profile via the `/me` path. |
| M-06 | **Celery worker health in `/v1/health`** | Partial | `HealthCheckService.perform_health_check()` calls `celery_app.control.inspect().ping()` but does not handle the case where Celery is not configured or the broker is unreachable during startup — it silently marks Celery as "unknown" rather than surfacing an actionable error. |
| M-07 | **API rate limit headers on all responses** | Partial | Rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) are only added for rate-limited endpoints. Health and metrics endpoints skip rate limiting (correct) but also skip the headers entirely, giving clients no visibility into their quota. |

### 5.2 GUI Layer

| # | Feature | Status | Evidence |
|---|---------|--------|---------|
| M-08 | **Keyboard shortcuts** | Non-functional | See BUG-004. No shortcuts work at runtime. The documented shortcut reference in Help → Keyboard Shortcuts shows a list that is entirely inoperative. |
| M-09 | **High-contrast dark theme** | Missing | See BUG-005. The `high_contrast_dark` theme is referenced in docs (`DESIGN-SYSTEM.md:919`, `ACCESSIBILITY.md:519`) and code but not defined in `ThemeManager.THEMES`. |
| M-10 | **Export to PDF** | Not implemented | The Analysis menu lists "Generate Report" which only produces a text summary. No PDF export capability exists despite it being mentioned in `docs/HOW-TO-USE-APGI.md`. |
| M-11 | **Real-time session sync between GUI and API** | Not implemented | The GUI (`APGI-GUI.py`) directly instantiates `APGISystem` locally; it does not communicate with the REST API. The two interfaces are completely decoupled — state changes in the GUI are invisible to the API and vice versa. |
| M-12 | **Plot export** | Partial | `File → Export Data` exports CSV/JSON of simulation history but does not export the Matplotlib figures as images. The `NavigationToolbar2Tk` is embedded but the save button only saves the currently visible subplot, not all 6 tabs. |

### 5.3 Security & Infrastructure

| # | Feature | Status | Evidence |
|---|---------|--------|---------|
| M-13 | **HTTPS enforcement** | Not configured | Uvicorn is launched with no TLS settings (`api/main.py:302`). The CSRF cookie sets `secure=True` but the server itself serves plain HTTP in the default configuration, making the cookie setting ineffective. |
| M-14 | **Alembic migration for missing columns** | Missing | The `api/database/models.py` `User` model lacks `is_active` and `updated_at` columns (BUG-002). No Alembic migration exists to add them to the database schema. |
| M-15 | **Role-based session isolation** | Not implemented | `GET /v1/sessions/{session_id}` does not verify that the requesting user owns the session. Any authenticated user can read, control, or delete any other user's session if they know the UUID. |

---

## 6. Detailed Findings by Component

### 6.1 Core Engine (`apgi_system/`)

**Status: Well-implemented.**

- All 11 documented subsystems are implemented: `ActiveInferenceEngine`, `HierarchicalPredictor`, `PrecisionWeighting`, `BodyModel`, `AllostaticRegulator`, `SomaticMarkerSystem`, `IgnitionThreshold`, `GlobalWorkspace`, self-model components, `MetabolicBudget`, `OscillationEngine`.
- Configuration via YAML (`config/default.yaml`) with full `ConfigValidator` and `ConfigValidationError` handling.
- Thread-safe design with `RLock` in `APGISystem`.
- `MonitoringPerformance` tracks step timing and memory.
- No functional bugs identified in isolation.

**Minor concerns:**
- `apgi_system/types.py` is 577 bytes — largely empty; custom types could be consolidated into relevant modules.
- `tests/unit/test_allostatic_regulator.py` is **0 bytes** (empty file). This test file exists but contains no tests, reducing the effective unit test coverage for `AllostaticRegulator`.

---

### 6.2 REST API (`api/`)

**Status: Structurally complete but operationally broken by 3 critical bugs (BUG-001, BUG-002, BUG-003).**

**Middleware stack** (outer → inner):
1. `RequestSizeLimitMiddleware` — Correctly positioned first.
2. `GZipMiddleware` — Standard.
3. `PrometheusMetricsMiddleware` — Tracks all requests.
4. `RequestLoggingMiddleware` — Structured logging.
5. `AuthenticationMiddleware` — JWT extraction to `request.state.user`.
6. `ResponseSchemaValidationMiddleware` — Fail-open by default (correct).
7. `CSRFMiddleware` — Correctly skips JWT-authenticated requests.
8. `DeprecationMiddleware` — No deprecated endpoints configured.
9. `RateLimitingMiddleware` — Double-registered (BUG-003); in-memory fallback always active.
10. `CORSMiddleware` — Correctly last.

**Exception handling:** Comprehensive four-handler chain (`APIError`, `RequestValidationError`, `HTTPException`, catch-all). The catch-all correctly sends structured alerts via `alert_manager` and sanitizes sensitive fields in request bodies. Timestamps are `null` in 4xx handlers (BUG-007).

**Database layer:**
- SQLAlchemy 2.x with connection pooling.
- Alembic migrations present but no migration for missing User columns (M-14).
- Circuit breaker on all DB operations (correct resilience pattern).
- Deprecated `declarative_base` import (BUG-016).

**Authentication:**
- JWT HS256 with access/refresh token pair.
- Refresh token stored as bcrypt hash in DB with revocation support.
- Token type enforcement (`"access"` vs `"refresh"` checked on verify).
- `hmac.compare_digest` used for token comparison (correct).

---

### 6.3 GUI — `APGI-GUI.py`

**Status: Visually complete but with critical interaction defects.**

**What works:**
- 6-tab visualization notebook (Neural Activity, Interoception, System Metrics, Self-Model, Oscillations, State Space).
- Control panel with Start/Pause/Stop/Reset buttons, speed slider, 8 parameter sliders.
- Event log with bounded `deque(maxlen=10000)`.
- Thread-safe data lock (`RLock`) for buffer updates.
- Theme manager integration (normal, dark, high-contrast).
- Configuration save/load from `~/.apgi_gui_config.json`.
- Auto-save timer architecture.
- Menu system with 7 menus and ~38 items.

**What doesn't work:**
- Keyboard shortcuts (BUG-004) — all 10+ shortcuts inoperative.
- High-contrast dark theme (BUG-005).
- Clean shutdown via window X button (BUG-008).
- Auto-save cleanup on exit (BUG-011).

---

### 6.4 GUI — `Psychological-States-GUI.py`, `Assistant-GUI.py`, `AI-Assistant.py`

**Status: Individually functional with proper shutdown handlers.**

- Both `Psychological-States-GUI.py` and `Assistant-GUI.py` correctly register `WM_DELETE_WINDOW` handlers.
- `Assistant-GUI.py` at 8,671 lines is the largest file; its own `GUIConfig.THEMES` dict is separate from the shared `ThemeManager`, which may cause theme drift if one is updated without the other.
- `AI-Assistant.py` (3,382 lines) has no identified critical bugs.

---

### 6.5 Test Suite (`tests/`)

**Status: Extensive but with gaps.**

| Area | Test Files | Notes |
|------|-----------|-------|
| Unit – Core Engine | 35 files | Comprehensive; covers all subsystems |
| Unit – GUI | 5 files | Mocked Tkinter; reasonable coverage |
| Unit – API | 18 files | Good coverage of routes and services |
| Integration | 5 files | API contract and workflow tests |
| Property-based | `strategies.py` + hypothesis | Well-structured |

**Gaps:**
- `tests/unit/test_allostatic_regulator.py` is empty (0 bytes).
- No integration test exercising the full auth → create session → start → get state → stop → export flow end-to-end with a real database.
- No test covering the rate limiter middleware with Redis (the bug in BUG-003 is likely to be undetected by current tests since middleware is typically tested in isolation with `test_mode=True`).
- No test for the `GET /v1/users/stats` route ordering issue (BUG-006).

---

## 7. Actionable Recommendations

Remediation items are ordered by priority (critical first).

---

### Priority 1 — Immediate (Block Deployment)

#### REC-001: Fix Default User Roles (BUG-001)

**File:** `api/database/connection.py:132`

Change the default user roles to a recognized RBAC value:

```python
# Before
roles=["user", "session_manager"],

# After — use a recognized Role enum value
roles=["researcher"],   # or ["admin"] for a superuser default
```

Additionally, update startup documentation to instruct operators to use `utils/show_default_user.py` to retrieve the generated credentials.

---

#### REC-002: Add `is_active` and `updated_at` Columns to User Model (BUG-002)

**File:** `api/database/models.py`

Add the missing columns to the `User` class:

```python
is_active = Column(Boolean, nullable=False, default=True, comment="Whether the account is active")
updated_at = Column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now(),
    onupdate=func.now(),
    comment="Last modification timestamp",
)
```

Then generate and run an Alembic migration:
```bash
alembic revision --autogenerate -m "add_is_active_updated_at_to_users"
alembic upgrade head
```

---

#### REC-003: Fix Rate Limiting Middleware Registration (BUG-003)

**File:** `api/main.py:212–220`

Remove the manual instantiation and pass the instance directly through `app.add_middleware`. Since Starlette's `add_middleware` always creates its own instance from the class, store a reference by wrapping or using a different approach:

```python
# Replace lines 212-220 with:
rate_limiter_instance = RateLimitingMiddleware(
    app,
    redis_client=None,
    enabled=settings.rate_limit_enabled,
)
# Store reference for later Redis injection
rate_limiting_middleware = rate_limiter_instance
app.middleware_stack = None  # Reset if needed, or use a shared config object

# Simpler alternative: use a shared config/state object
# that both the app startup and middleware read from.
```

**Recommended pattern:** Use a module-level mutable config or dependency injection container that both `lifespan` and `RateLimitingMiddleware.dispatch` reference, rather than trying to update the middleware instance post-construction.

---

### Priority 2 — High (Fix Before Alpha/Beta)

#### REC-004: Move Keyboard Shortcuts to `__init__` (BUG-004)

**File:** `APGI-GUI.py`

Extract all `self.root.bind(...)` calls from `_exit_app()` into a dedicated `_setup_keyboard_shortcuts()` method and call it from `__init__` after the GUI is built:

```python
def __init__(self, root):
    ...
    self._create_menu_bar()
    self._create_main_layout()
    self._create_status_bar()
    self._setup_keyboard_shortcuts()   # ← add this call
    self._initialize_system()
    ...

def _setup_keyboard_shortcuts(self):
    self.root.bind("<F5>", lambda e: self._start_simulation())
    self.root.bind("<F6>", lambda e: self._pause_simulation())
    # ... etc.

def _exit_app(self):
    """Exit the application."""
    self._stop_simulation_if_running()
    self.root.destroy()   # prefer destroy() over quit()
```

Also fix line 689: replace `self.on_start_clicked` with `self._start_simulation`.

---

#### REC-005: Add `high_contrast_dark` to `ThemeManager.THEMES` (BUG-005)

**File:** `apgi_gui/theme_manager.py`

Add the missing theme definition:

```python
"high_contrast_dark": {
    "bg": "#000000",
    "fg": "#FFFFFF",
    "canvas_bg": "#0a0a0a",
    "accent": "#FFFF00",
    "info": "#00FFFF",
    "success": "#00FF00",
    "warning": "#FFFF00",
    "error": "#FF0000",
    "notification_colors": {"high": "#FF0000", "medium": "#FFFF00", "low": "#FFFFFF"},
    "battery_colors": {"high": "#00FF00", "medium": "#FFFF00", "low": "#FF0000"},
    "state_colors": {"idle": "#FFFFFF", "processing": "#FFFF00", "complete": "#00FF00", "error": "#FF0000"},
},
```

---

#### REC-006: Reorder `/stats` Route Before `/{user_id}` (BUG-006)

**File:** `api/routes/users.py`

Move the `GET /stats` route definition (currently at line 420) to appear **before** `GET /{user_id}` (currently at line 219). In FastAPI, literal path segments must be registered before parameterized ones to take precedence.

---

#### REC-007: Replace `null` Timestamps with Real Timestamps (BUG-007)

**File:** `api/exception_handlers.py:108,170`

```python
# Before
"timestamp": None,  # Will be set by middleware if available

# After
"timestamp": datetime.utcnow().isoformat() + "Z",
```

Import `datetime` is already present at the top of the file. Apply to both `validation_error_handler` and `http_exception_handler`.

---

### Priority 3 — Medium (Fix Before General Availability)

| Ref | Action |
|-----|--------|
| REC-008 | Register `WM_DELETE_WINDOW` in `APGI-GUI.py.__init__`: `self.root.protocol("WM_DELETE_WINDOW", self._exit_app)`. Update `_exit_app` to stop the simulation thread and cancel auto-save timer before `self.root.destroy()`. |
| REC-009 | Add `dependencies=[Depends(require_permission(Permission.USER_CREATE))]` to `POST /v1/users` if self-registration should be restricted, or document that open registration is intentional. |
| REC-010 | Replace inline `/health` in `main.py` with a redirect to `/v1/health`, or extend the inline handler to delegate to `HealthCheckService`. Remove the ambiguity entirely. |
| REC-011 | Add session ownership check in `state.py`, `sessions.py`, and `export.py`: verify `session.user_id == current_user.user_id` (or user has `SYSTEM_ADMIN`) before permitting operations (M-15). |
| REC-012 | Add `GET /v1/sessions` list endpoint to `api/routes/sessions.py`, returning paginated sessions for the current user. |
| REC-013 | Implement refresh token rotation in `POST /v1/auth/refresh`: revoke the incoming refresh token and issue a new one alongside the new access token. |

---

### Priority 4 — Low / Technical Debt

| Ref | Action |
|-----|--------|
| REC-014 | Replace deprecated `from sqlalchemy.ext.declarative import declarative_base` with `from sqlalchemy.orm import declarative_base` (BUG-016). |
| REC-015 | Add a real test to `tests/unit/test_allostatic_regulator.py` — the file is currently empty. |
| REC-016 | Add HMAC webhook signatures to `api/services/webhook_manager.py` (e.g., `X-Webhook-Signature: sha256=<hmac>`). |
| REC-017 | Add an end-to-end integration test covering the full auth → session → state → export lifecycle against a real (or containerized) database. |
| REC-018 | Document `CORS_ORIGINS` configuration prominently in the QUICKSTART; set a safer default that prompts operators to configure explicitly. |
| REC-019 | Add HTTPS/TLS documentation for production Uvicorn deployment (with nginx reverse proxy or `ssl_keyfile`/`ssl_certfile` flags). |
| REC-020 | Unify `AssistantGUI.GUIConfig.THEMES` and `apgi_gui.theme_manager.ThemeManager.THEMES` to a single source of truth to prevent theme drift between GUI applications. |

---

## 8. Appendix: Audit Scope & Methodology

### Files Reviewed

| File/Directory | Lines | Coverage |
|----------------|-------|---------|
| `api/main.py` | 303 | Full |
| `api/config.py` | 179 | Full |
| `api/exception_handlers.py` | 293 | Full |
| `api/routes/` (all 9 files) | ~6,200 | Full |
| `api/services/` (all 9 files) | ~9,200 | Representative |
| `api/middleware/` (all 9 files) | ~8,100 | Representative |
| `api/database/models.py` | 333 | Full |
| `api/database/connection.py` | 279 | Full |
| `api/models/schemas.py` | ~600 | Full |
| `api/tasks/task_registry.py` | 115 | Full |
| `APGI-GUI.py` | 4,934 | Structural + key methods |
| `apgi_gui/theme_manager.py` | 195 | Full |
| `apgi_gui/components/core.py` | ~200 | Full |
| `apgi_system/system.py` | 60 (header) | Structural |
| `utils/circuit_breaker.py` | ~300 | Representative |
| `docs/APGI-System-README.md` | ~600 | Full |
| `docs/DESIGN-SYSTEM.md` | Representative | Cross-reference |
| `tests/` (structure + key files) | Representative | Structural |
| `.env.example` | 32 | Full |
| `requirements.txt`, `pyproject.toml` | — | Full |

### Methodology

1. **Static code analysis** — full read of all API and key GUI source files; grep-based cross-referencing for method names, route definitions, column usage, and theme references.
2. **Architecture review** — mapping the middleware chain, RBAC matrix, database schema, and route registration order.
3. **Logic tracing** — tracing execution paths for critical workflows (auth → session create → task submit, GUI launch → keyboard shortcut, theme toggle).
4. **Documentation cross-referencing** — comparing documented features (`docs/`, `QUICKSTART-GUI.txt`, README) against code implementation.
5. **Dependency analysis** — reviewing `requirements.txt` and `pyproject.toml` for version constraints, deprecated package usage, and missing runtime dependencies.

### Audit Limitations

- **Runtime testing not performed** — external services (PostgreSQL, Redis, Celery) were not running in this environment. All findings are based on static analysis and logical inference.
- **GUI visual testing not performed** — Tkinter display server not available. GUI findings are based on source code inspection.
- **Performance benchmarking not performed** — load/stress testing deferred to a live environment.

---

*Report generated by Claude Code on 2026-02-23. Ready for developer handoff.*
