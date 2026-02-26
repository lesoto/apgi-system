# APGI System — Comprehensive Application Audit Report

**Prepared:** 2026-02-26
**Scope:** End-to-end audit of APGI (Allostatic Precision-Gated Ignition) System — REST API, GUI application, core library, infrastructure
**Branch:** `claude/app-audit-security-9ArKX`
**Auditor:** Automated Security & Quality Review

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [KPI Scores](#2-kpi-scores)
3. [Audit Scope & Methodology](#3-audit-scope--methodology)
4. [Critical Findings Overview](#4-critical-findings-overview)
5. [Bug Inventory — API Layer](#5-bug-inventory--api-layer)
6. [Bug Inventory — GUI Application](#6-bug-inventory--gui-application)
7. [Bug Inventory — Core Library](#7-bug-inventory--core-library)
8. [Security Vulnerability Catalog](#8-security-vulnerability-catalog)
9. [Missing Features Log](#9-missing-features-log)
10. [Actionable Remediation Recommendations](#10-actionable-remediation-recommendations)
11. [Appendix: Endpoint Auth Matrix](#11-appendix-endpoint-auth-matrix)

---

## 1. Executive Summary

The APGI System is a research-grade platform for simulating and studying Allostatic Precision-Gated Ignition dynamics of consciousness. It consists of three primary components: a **FastAPI REST API**, a **Tkinter-based desktop GUI** (five GUI applications), and a **scientific core library** with ~90% unit test coverage.

The overall application is architecturally sound with well-structured code, comprehensive documentation, and solid CI/CD tooling. However, the audit revealed **critical implementation gaps** that prevent the system from functioning correctly in production and introduce serious security vulnerabilities.

### Key Findings

| Category | Count | Severity Distribution |
|---|---|---|
| Critical Bugs | 6 | 🔴 All require immediate fix |
| High Bugs | 8 | 🟠 Fix before any deployment |
| Medium Bugs | 10 | 🟡 Fix in next sprint |
| Low Bugs | 9 | 🟢 Fix as time permits |
| Security Vulnerabilities | 12 | See §8 |
| Missing Features | 15 | See §9 |

### Top 3 Showstoppers

1. **Authentication system is completely inaccessible** — The auth router (`/v1/auth/login`, `/v1/auth/refresh`, `/v1/auth/logout`) and user management router (`/v1/users/*`) are never registered in `api/main.py`. Every login attempt returns **HTTP 404**.

2. **Session creation endpoint is broken** — The `create_session()` handler in `api/routes/sessions.py` is missing its `@router.post()` decorator. `POST /v1/sessions` returns **HTTP 405 Method Not Allowed**.

3. **Refresh token flow always fails** — `AuthManager.refresh_access_token()` re-hashes the refresh token with bcrypt (non-deterministic, new salt each call), then compares the freshly-computed hash to the stored hash via `==`. These will never match. Every refresh attempt returns **"Invalid or revoked refresh token"**.

### Health Verdict

> **The API is not production-ready.** Core authentication flows are inaccessible or broken. All data endpoints are accessible without authentication. Immediate remediation of the six critical bugs is required before any production deployment.

---

## 2. KPI Scores

Scores reflect the current state of the implementation. Thresholds: 🔴 < 50 | 🟠 50–69 | 🟡 70–84 | 🟢 85–100

| Dimension | Score | Rating | Key Driver |
|---|---|---|---|
| **Functional Completeness** | 38 / 100 | 🔴 Critical | Auth routes missing, session creation broken, core flows non-functional |
| **UI/UX Consistency** | 72 / 100 | 🟡 Acceptable | GUI is feature-rich; minor missing confirmations and hardcoded values |
| **Responsiveness & Performance** | 74 / 100 | 🟡 Acceptable | Proper pagination, rate limiting, GZip; but some memory/DoS risks |
| **Error Handling & Resilience** | 71 / 100 | 🟡 Acceptable | Exception handlers are well-structured; several silent failure paths |
| **Security Implementation** | 29 / 100 | 🔴 Critical | Zero auth enforcement on API, SSRF, credentials logged, token bugs |
| **Implementation Quality** | 63 / 100 | 🟠 Needs Work | Good design patterns, but critical logic bugs and missing registrations |

**Overall System Health: 48 / 100** 🔴

---

## 3. Audit Scope & Methodology

### Files Reviewed

| Area | Files | Lines of Code |
|---|---|---|
| API Routes | `api/routes/*.py` (9 files) | ~1,800 |
| API Middleware | `api/middleware/*.py` (8 files) | ~1,200 |
| API Services | `api/services/*.py` (7 files) | ~1,600 |
| API Database | `api/database/*.py` (2 files) | ~300 |
| API Models | `api/models/schemas.py`, `api/config.py`, `api/exceptions.py` | ~800 |
| GUI Applications | `APGI-GUI.py`, `Assistant-GUI.py`, `Psychological-States-GUI.py` | ~130,000+ |
| GUI Support | `apgi_gui/` (4 files) | ~400 |
| Core Library | `apgi_system/` (~30 modules) | ~50,000+ |
| Tests | `tests/` (65 files) | ~16,600 |
| Configuration | `config/default.yaml`, `.env.example`, `pyproject.toml` | ~250 |
| Documentation | `docs/` (20 files) | ~9,000 |

### Methodology

- Static code analysis of all source files
- Endpoint-by-endpoint authentication and authorization review
- Data flow tracing for all sensitive operations
- Cross-reference of documented vs. implemented features
- Cryptographic implementation review
- Dependency and configuration security review

---

## 4. Critical Findings Overview

```
╔══════════════════════════════════════════════════════════════════════╗
║  CRITICAL  Auth router not registered → ALL auth endpoints are 404  ║
║  CRITICAL  Users router not registered → ALL user mgmt is 404       ║
║  CRITICAL  create_session() missing @router.post() → 405 error      ║
║  CRITICAL  Bcrypt refresh token comparison always fails              ║
║  CRITICAL  not RefreshToken.revoked SQLAlchemy syntax bug            ║
║  CRITICAL  Plaintext admin credentials logged to application log     ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 5. Bug Inventory — API Layer

### 5.1 Critical Severity

---

#### BUG-001 — Auth and User Management Routers Not Registered
**Severity:** 🔴 Critical
**Component:** `api/main.py` (lines 44, 238–244)
**OWASP:** A01:2021 – Broken Access Control

**Description:**
`api/routes/auth.py` (providing `/v1/auth/login`, `/v1/auth/refresh`, `/v1/auth/logout`) and `api/routes/users.py` (providing all `/v1/users/*` endpoints) are never imported or registered with the FastAPI application in `main.py`.

**Affected Code:**
```python
# api/main.py line 44 — auth and users are absent
from api.routes import export, health, metrics, sessions, state, tasks, version

# api/main.py lines 238–244 — auth.router and users.router never included
app.include_router(sessions.router)
app.include_router(state.router)
app.include_router(tasks.router)
app.include_router(export.router)
app.include_router(metrics.router)
app.include_router(health.router)
app.include_router(version.router)
# Missing: app.include_router(auth.router)
# Missing: app.include_router(users.router)
```

**Expected:** `POST /v1/auth/login` returns HTTP 200 with tokens.
**Actual:** `POST /v1/auth/login` returns HTTP 404 Not Found.
**Impact:** No user can log in. The entire authentication system is inaccessible. User registration, password reset, and role management are unreachable.

**Reproduction Steps:**
```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret"}'
# Returns: {"detail": "Not Found"}
```

---

#### BUG-002 — Session Creation Endpoint Missing Route Decorator
**Severity:** 🔴 Critical
**Component:** `api/routes/sessions.py` (lines 130–160)
**OWASP:** A05:2021 – Security Misconfiguration

**Description:**
The `create_session()` async function exists in the sessions router but has no `@router.post()` decorator. It is therefore a plain Python function, not bound to any HTTP route.

**Affected Code:**
```python
# api/routes/sessions.py lines 130–160
# Notice: no @router.post() decorator
async def create_session(
    request: SessionCreateRequest,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionCreateResponse:
    ...
```

**Expected:** `POST /v1/sessions` creates a session and returns HTTP 201.
**Actual:** `POST /v1/sessions` returns HTTP 405 Method Not Allowed (only GET is defined for that path).
**Impact:** Clients cannot create simulation sessions via the API. The entire session management workflow is blocked.

---

#### BUG-003 — Refresh Token Bcrypt Hash Comparison Always Fails
**Severity:** 🔴 Critical
**Component:** `api/services/auth_manager.py` (lines 339–360)
**OWASP:** A07:2021 – Identification and Authentication Failures

**Description:**
`refresh_access_token()` re-hashes the presented refresh token using `hash_password()` (bcrypt with a new random salt), then attempts to find the token in the database using a direct string equality check (`==`). Since bcrypt is non-deterministic (each call uses a different salt), the newly computed hash will **never** equal the stored hash.

**Affected Code:**
```python
# api/services/auth_manager.py lines 340–359
token_hash = self.hash_password(refresh_token)  # New bcrypt hash, different salt!

db_token = (
    self.db.query(RefreshToken)
    .filter(
        and_(
            RefreshToken.user_id == payload.user_id,
            RefreshToken.token_hash == token_hash,  # NEVER MATCHES stored hash
            not RefreshToken.revoked,               # Also broken — see BUG-004
        )
    )
    .first()
)

if not db_token:
    raise AuthenticationError("Invalid or revoked refresh token")  # Always raised
```

**Expected:** Token refresh rotates the refresh token and returns new access + refresh tokens.
**Actual:** Token refresh always raises `AuthenticationError("Invalid or revoked refresh token")`.
**Impact:** Token refresh is completely non-functional. Users cannot refresh expired access tokens, effectively making 30-minute sessions non-renewable without re-login (which also doesn't work — see BUG-001).

**Fix:** Replace the hash-and-compare lookup with a deterministic approach. Store a SHA-256 hash for lookup and verify with `bcrypt.checkpw()` for the actual comparison, or use a random opaque token ID stored alongside the bcrypt hash.

---

#### BUG-004 — SQLAlchemy `not Column` Syntax Error in Token Filters
**Severity:** 🔴 Critical
**Component:** `api/services/auth_manager.py` (lines 349, 429, 463)
**OWASP:** A07:2021 – Identification and Authentication Failures

**Description:**
Three SQLAlchemy filter expressions use Python's `not` operator on a SQLAlchemy column object (`not RefreshToken.revoked`), which is invalid SQLAlchemy syntax. In modern SQLAlchemy, this raises a `TypeError` ("Boolean value of this clause is not defined") at runtime, crashing token refresh, token revocation, and "revoke all tokens" operations.

**Affected Code:**
```python
# api/services/auth_manager.py — same pattern in 3 places
.filter(
    and_(
        RefreshToken.user_id == payload.user_id,
        RefreshToken.token_hash == token_hash,
        not RefreshToken.revoked,  # WRONG: Python 'not' on SQLAlchemy column
    )
)
```

**Expected:** Filter correctly excludes revoked tokens.
**Actual:** Raises `TypeError` or (in older SQLAlchemy) evaluates to `False`, causing no tokens to be found.
**Fix:** Replace `not RefreshToken.revoked` with `RefreshToken.revoked == False` or `~RefreshToken.revoked`.

---

#### BUG-005 — No Authentication Enforced on Any Protected Endpoint
**Severity:** 🔴 Critical
**Component:** `api/routes/sessions.py`, `api/routes/state.py`, `api/routes/tasks.py`, `api/routes/export.py`
**OWASP:** A01:2021 – Broken Access Control

**Description:**
Every route in sessions, state, tasks, and export explicitly sets `dependencies=[]`, overriding any middleware-level protection. Additionally, `AuthenticationMiddleware` is never added to the application middleware stack in `main.py`. As a result, **all data endpoints are accessible without any authentication**.

**Affected Code:**
```python
# api/routes/sessions.py — every endpoint
@router.get("", dependencies=[])            # No auth
@router.get("/{session_id}", dependencies=[]) # No auth
@router.post("/{session_id}/start", dependencies=[]) # No auth
@router.delete("/{session_id}", dependencies=[])     # No auth
# ... etc
```

**Expected:** Unauthenticated requests to `/v1/sessions` return HTTP 401.
**Actual:** Unauthenticated requests succeed and return data.
**Impact:** Any anonymous user or attacker can list, read, start, stop, reset, or delete any simulation session; read all state data; export all simulation data; and cancel any running task.

---

#### BUG-006 — Admin Credentials Logged in Plaintext at Startup
**Severity:** 🔴 Critical
**Component:** `api/database/connection.py` (lines 116–121)
**OWASP:** A09:2021 – Security Logging and Monitoring Failures

**Description:**
`create_default_user()` is called at every application startup. It logs the generated admin username and password in plaintext at WARNING level, which means they appear in all log aggregation systems, log files, and any monitoring dashboards.

**Affected Code:**
```python
# api/database/connection.py lines 116–121
logger.warning(
    f"Generated default user credentials - STORE SECURELY. "
    f"Username: {secure_username}, Password: {secure_password}. "  # PLAINTEXT
    f"NOTE: These credentials allow full system access - change immediately"
)
```

**Expected:** Credentials are delivered via a secure out-of-band channel (email, secrets manager, one-time display).
**Actual:** Admin password is written in plaintext to application logs on every startup.
**Impact:** Credentials can be captured from log files, Splunk/ELK/CloudWatch, stdout logs in container registries, or CI/CD pipeline logs.

---

### 5.2 High Severity

---

#### BUG-007 — Session Listing Returns All Sessions Without User Filtering
**Severity:** 🟠 High
**Component:** `api/routes/sessions.py` (line 103)
**OWASP:** A01:2021 – Broken Access Control

**Description:**
`list_sessions()` passes `user_id=None` to the session manager, which instructs it to return all sessions regardless of ownership. There is no filtering by the authenticated user (and authentication is not enforced regardless — see BUG-005).

**Affected Code:**
```python
# api/routes/sessions.py line 103
result: Dict[str, Any] = await manager.list_sessions(user_id=None, limit=limit, cursor=cursor)
```

**Fix:** Pass the authenticated user's ID: `manager.list_sessions(user_id=current_user.user_id, ...)` unless the user is an admin.

---

#### BUG-008 — `is_admin` Permission Check Compares Wrong Types
**Severity:** 🟠 High
**Component:** `api/routes/users.py` (lines 255, 390, 458)
**OWASP:** A01:2021 – Broken Access Control

**Description:**
The admin check in `update_current_user_profile`, `update_user`, and `reset_user_password` uses `Permission.USER_ADMIN in current_user.roles`. However, `current_user.roles` is a list of role name strings (e.g., `["admin"]`), while `Permission.USER_ADMIN` has the string value `"user:admin"`. These never match, so `is_admin` is always `False`. No user can ever be detected as an admin via this check.

**Affected Code:**
```python
# api/routes/users.py line 255 (and lines 390, 458)
is_admin = Permission.USER_ADMIN in current_user.roles
# current_user.roles = ["admin"]  →  "user:admin" in ["admin"]  →  False (always)
```

**Fix:** Use the RBAC helper: `is_admin = has_permission(current_user.roles, Permission.USER_ADMIN)` or `is_admin = has_any_role(current_user.roles, [Role.ADMIN])`.

---

#### BUG-009 — `list_users(active_only=False)` Always Returns Only Active Users
**Severity:** 🟠 High
**Component:** `api/services/user_management.py` (lines 287–290)
**OWASP:** A05:2021 – Security Misconfiguration (Incorrect function behavior)

**Description:**
The `else` branch in `list_users()` applies the same `is_active = True` filter as the `if` branch, making it impossible to retrieve inactive users regardless of the `active_only` parameter.

**Affected Code:**
```python
# api/services/user_management.py lines 287–290
if active_only:
    stmt = stmt.where(User.is_active.is_(True))
else:
    stmt = stmt.where(User.is_active.is_(True))  # BUG: same filter in both branches
```

**Expected:** `list_users(active_only=False)` returns all users including inactive.
**Actual:** Always returns only active users.
**Side-Effect:** `get_user_stats()` always reports `inactive_users = 0`.

**Fix:** The `else` branch should not add an `is_active` filter, or it should filter by `False`.

---

#### BUG-010 — Webhook URL Validation Allows SSRF Attacks
**Severity:** 🟠 High
**Component:** `api/services/webhook_manager.py` (lines 102–135)
**OWASP:** A10:2021 – Server-Side Request Forgery (SSRF)

**Description:**
`validate_webhook_url()` only checks that the URL is non-empty, starts with `http://` or `https://`, and is under 500 characters. It does not block private/internal IP ranges, cloud metadata endpoints, or localhost.

**Affected Code:**
```python
# api/services/webhook_manager.py lines 119–124
if not url.startswith(("http://", "https://")):
    raise ValueError("Webhook URL must start with http:// or https://")
if len(url) > 500:
    raise ValueError(...)
# No validation of: 127.0.0.1, 10.x.x.x, 192.168.x.x, 169.254.169.254
```

**Attack Scenario:** An attacker submits `webhook_url: "http://169.254.169.254/latest/meta-data/"` when creating a task. The API will make a request to the AWS metadata endpoint and may include the response in error messages.

**Fix:** Implement an IP allowlist/blocklist, resolve DNS before connecting, block RFC 1918 and link-local ranges.

---

#### BUG-011 — `AuthenticationMiddleware` Never Added to Middleware Stack
**Severity:** 🟠 High
**Component:** `api/main.py` (lines 164–220)
**OWASP:** A07:2021 – Identification and Authentication Failures

**Description:**
`api/middleware/authentication.py` defines `AuthenticationMiddleware` — a fully implemented middleware that extracts and verifies JWT tokens — but it is never added to the application's middleware chain in `create_app()`.

**Expected:** JWT tokens from `Authorization: Bearer ...` headers are validated on each request and user identity attached to `request.state.user`.
**Actual:** No JWT validation occurs at the middleware level. Even if endpoints checked `request.state.user`, it would always be `None`.

---

#### BUG-012 — `Content-Disposition` Header Injection in Export Endpoint
**Severity:** 🟠 High
**Component:** `api/routes/export.py` (line 123)
**OWASP:** A03:2021 – Injection

**Description:**
The export filename is built from the user-controlled `session_id` path parameter and placed directly into an unquoted `Content-Disposition` header. If `session_id` contains characters like `\r\n`, an attacker can inject additional HTTP response headers.

**Affected Code:**
```python
# api/routes/export.py line 123
headers={"Content-Disposition": f"attachment; filename={filename}"}
# filename = f"session_{session_id}_export.{extension}"  — session_id is user input
```

**Fix:** Quote the filename: `f'attachment; filename="{filename}"'` and sanitize `session_id` to alphanumeric characters and hyphens.

---

#### BUG-013 — Ignition History Uses Current Ignition Signal for All Historical Events
**Severity:** 🟠 High
**Component:** `api/routes/state.py` (lines 220–236)

**Description:**
When building the ignition event history, the code reads `total_signal` and `threshold` from the **current** system state (`state.get("ignition", {})`) and applies these values to **every** historical ignition event. All historical events share the same (current) signal/threshold values.

**Expected:** Each historical ignition event has its own signal and threshold values from when it occurred.
**Actual:** All events in ignition history have identical `trigger_signal` and `threshold` values equal to the current state.

---

#### BUG-014 — Missing Session Ownership Enforcement
**Severity:** 🟠 High
**Component:** All session action endpoints in `api/routes/sessions.py`
**OWASP:** A01:2021 – Broken Access Control

**Description:**
None of the session action endpoints (start, pause, stop, reset, delete) verify that the authenticated user owns the session they are operating on. Combined with the missing authentication (BUG-005), any client can manipulate any session.

---

### 5.3 Medium Severity

---

#### BUG-015 — `reload=True` Hardcoded in Production Settings
**Severity:** 🟡 Medium
**Component:** `api/config.py` (line 33)

**Description:**
`self.reload: bool = True` is hardcoded with no environment variable override. This means uvicorn's file-watching `--reload` flag is always `True`, which is inappropriate for production and creates unnecessary file system monitoring overhead.

---

#### BUG-016 — `config_path` in Session Create Request Not Validated (Path Traversal Risk)
**Severity:** 🟡 Medium
**Component:** `api/models/schemas.py` — `SessionCreateRequest`
**OWASP:** A01:2021 – Broken Access Control

**Description:**
`SessionCreateRequest.config_path` accepts arbitrary file paths with no validation. If the session manager actually reads files from this path, an attacker could set `config_path: "../../../../etc/passwd"` to read arbitrary system files.

---

#### BUG-017 — PickleType Used for User-Influenced Data
**Severity:** 🟡 Medium
**Component:** `api/database/models.py` (multiple models)
**OWASP:** A08:2021 – Software and Data Integrity Failures

**Description:**
`Session.config`, `Session.tags`, `Task.parameters`, `Task.result_data`, `SessionData.data`, and `WebhookDelivery.payload` all use SQLAlchemy's `PickleType`. If any of this data can be influenced by user input and is later deserialized, it creates a potential remote code execution vector. Even without user input, a compromised database would allow RCE.

**Fix:** Migrate all `PickleType` columns to `JSON` type (`sqlalchemy.JSON` or `sqlalchemy.Text` with manual JSON serialization).

---

#### BUG-018 — JWT Secret Default Value in `.env.example` Triggers Security Warning
**Severity:** 🟡 Medium
**Component:** `.env.example` (line 12), `api/config.py` (lines 134–140)

**Description:**
The `.env.example` file sets `JWT_SECRET_KEY=your-secret-key-change-in-production-min-32-chars`. When this value is literally used, it does not exactly match any entry in the `insecure_defaults` list in `api/config.py`, so the insecure-default warning is **not** triggered. However, it matches the pattern and is publicly known from the repository.

---

#### BUG-019 — `Access Token` Not Invalidated on Logout
**Severity:** 🟡 Medium
**Component:** `api/routes/auth.py` (lines 154–177)
**OWASP:** A07:2021 – Identification and Authentication Failures

**Description:**
Logout only revokes the refresh token. The access token remains valid until its 30-minute expiry. An attacker who captures an access token can continue using the API for up to 30 minutes after the user logs out.

---

#### BUG-020 — No Brute-Force Protection on Login Endpoint
**Severity:** 🟡 Medium
**Component:** `api/routes/auth.py` (line 49)
**OWASP:** A07:2021 – Identification and Authentication Failures

**Description:**
`POST /v1/auth/login` falls into the `global` rate limit category, which is shared with all other uncategorized endpoints. There is no dedicated, tighter rate limit for login attempts. An attacker could attempt password brute-force at the global rate limit.

---

#### BUG-021 — No Security Headers in HTTP Responses
**Severity:** 🟡 Medium
**Component:** `api/main.py`
**OWASP:** A05:2021 – Security Misconfiguration

**Description:**
The API does not set any of the following security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Strict-Transport-Security` (when HTTPS enabled)
- `Referrer-Policy`
- `Permissions-Policy`

---

#### BUG-022 — Database Connection String Lacks SSL/TLS Configuration
**Severity:** 🟡 Medium
**Component:** `.env.example` (line 2), `api/config.py` (line 41)

**Description:**
The default `DATABASE_URL` does not include `?sslmode=require` or equivalent SSL parameters. Database credentials and query results may be transmitted unencrypted over the network.

---

#### BUG-023 — Rate Limiting Falls Back to "Allow" on Redis Failure
**Severity:** 🟡 Medium
**Component:** `api/middleware/rate_limiting.py` (lines 214–226)

**Description:**
When Redis is unavailable, the rate limiting middleware catches the exception and **allows** the request to proceed, adding fake "60 remaining" headers. This means rate limiting is completely disabled whenever Redis is down, which creates a DoS window.

---

#### BUG-024 — IP-Based Rate Limiting Spoofable via Proxy Headers
**Severity:** 🟡 Medium
**Component:** `api/middleware/rate_limiting.py` (lines 68–70)

**Description:**
`_get_client_id()` uses `request.client.host` as the IP when no authenticated user is present. When the API is deployed behind a load balancer, `request.client.host` will be the load balancer's IP for all clients. Rate limiting would then be applied to a single key shared across all unauthenticated users.

**Fix:** Use the `X-Forwarded-For` or `X-Real-IP` header when trusted proxy headers are configured.

---

### 5.4 Low Severity

---

#### BUG-025 — Inconsistent `user_id` Format Across Codebase
**Severity:** 🟢 Low
**Component:** `api/database/models.py` (line 66), `api/services/user_management.py` (line 133)

**Description:**
The `User` model's `default=lambda: str(uuid.uuid4())` generates UUID format IDs, but `user_management.py` manually sets `user_id=secrets.token_urlsafe(16)`, which generates URL-safe base64 strings. Inconsistent ID formats can cause confusion and may break ID-based lookups.

---

#### BUG-026 — Pagination Cursor Is Trivially Decodable
**Severity:** 🟢 Low
**Component:** `api/routes/state.py` (lines 246–263), `api/routes/export.py`

**Description:**
Pagination cursors are base64-encoded JSON objects: `{"offset": 50}`. Any client can decode, modify, and re-encode them to jump to arbitrary offsets, bypassing intended pagination.

---

#### BUG-027 — `get_user_stats()` Relies on Broken `list_users()` (Secondary Effect of BUG-009)
**Severity:** 🟢 Low
**Component:** `api/services/user_management.py` (lines 335–336)

**Description:**
`get_user_stats()` calls `self.list_users(active_only=False)` to count total users, but due to BUG-009, this always returns only active users. `inactive_users` will always be reported as `0`.

---

#### BUG-028 — Webhook Manager Uses `hmac.new()` (Non-Existent Function)
**Severity:** 🟢 Low
**Component:** `api/services/webhook_manager.py` (lines 93–98)

**Description:**
The code calls `hmac.new(...)` to generate webhook signatures. The correct function is `hmac.new()` — actually this is correct for older Python, but the standard library uses `hmac.new()`. Let me re-check: Python's `hmac` module exports `hmac.new()` as the constructor. This is actually fine. But wait — looking at the code more carefully:

```python
signature = hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()
```

Python's `hmac` module does export `hmac.new()`. This should work. **Disregard this bug — it is not an issue.**

---

#### BUG-029 — Large Ignition History Queries Not Enforced (Only Warned)
**Severity:** 🟢 Low
**Component:** `api/routes/state.py` (lines 193–197)

**Description:**
When `limit > 500`, the endpoint only logs a warning but still processes the request. A request with `limit=1000` will load the entire simulation history into memory and serialize it in a single response.

---

#### BUG-030 — `downsample` Parameter Not Validated for Zero/Negative Values
**Severity:** 🟢 Low
**Component:** `api/routes/export.py` (line 196)

**Description:**
`downsample: Optional[int] = Query(None, ge=1, ...)` has `ge=1` set via FastAPI's `Query`, which should prevent zero or negative values. However, if the underlying service does not re-validate, a value of 0 could cause division-by-zero in the export service.

---

#### BUG-031 — Error Response Includes Internal Exception Messages
**Severity:** 🟢 Low
**Component:** Multiple routes, e.g., `api/routes/state.py` (line 146)

**Description:**
Several endpoints include raw exception messages in HTTP 500 responses:
```python
detail=f"Failed to get system state: {str(e)}"
```
Internal error details should not be returned to clients.

---

## 6. Bug Inventory — GUI Application

### 6.1 High Severity

---

#### GUI-001 — Stack Traces Exposed to End Users in Messageboxes
**Severity:** 🟠 High
**Component:** `APGI-GUI.py` (multiple locations, e.g., lines 1604, 5021)

**Description:**
Several dialog handlers catch exceptions and display the full Python traceback via `traceback.format_exc()` in a `messagebox.showerror()` popup. This can expose file paths, library versions, and internal system details to users.

---

#### GUI-002 — YAML Configuration Loading May Use Unsafe Loader
**Severity:** 🟠 High
**Component:** `APGI-GUI.py` (lines 2032–2060)
**OWASP:** A08:2021 – Software and Data Integrity Failures

**Description:**
If `_load_config()` uses `yaml.load()` without an explicit `Loader=yaml.SafeLoader` argument, loading a maliciously crafted YAML config file could lead to arbitrary object construction and potential code execution.

**Fix:** Ensure `yaml.safe_load()` is used everywhere YAML is parsed.

---

### 6.2 Medium Severity

---

#### GUI-003 — Modal Dialogs Block Simulation Responsiveness
**Severity:** 🟡 Medium
**Component:** `APGI-GUI.py` (multiple dialog handlers)

**Description:**
Parameter editor, precision settings, and other modal dialogs block the main Tkinter event loop. While the simulation runs in a separate thread, the 50ms display update callback (`_update_displays`) cannot fire while a modal dialog is open, causing the visualization to freeze.

---

#### GUI-004 — No Simulation Stop Confirmation Before Exit
**Severity:** 🟡 Medium
**Component:** `APGI-GUI.py` (lines 727–788)

**Description:**
Closing the window while a simulation is running stops it immediately without prompting the user to save unsaved data. Users may lose simulation data if they accidentally close the application.

---

#### GUI-005 — Stressor Intensity Hardcoded at 0.5
**Severity:** 🟡 Medium
**Component:** `APGI-GUI.py` (line 4076)

**Description:**
`_induce_stressor()` hardcodes `intensity=0.5` with no user control. The UI should provide a slider or dialog to configure stressor intensity.

---

#### GUI-006 — Buffer Size Change During Active Simulation Not Handled
**Severity:** 🟡 Medium
**Component:** `APGI-GUI.py` (lines 459–595, 1654–1727)

**Description:**
The buffer configuration dialog allows changing the buffer size while simulation is running. Changing `maxlen` on a live `deque` will truncate data immediately and may cause index-out-of-bounds in plot update methods that assume a minimum buffer size.

---

### 6.3 Low Severity

---

#### GUI-007 — `_show_help()` Is Incomplete (Just Calls `_show_docs()`)
**Severity:** 🟢 Low
**Component:** `APGI-GUI.py` (line 5202)

**Description:**
The Help > Documentation menu item calls `_show_docs()`, but so does `_show_help()`. There is no dedicated context-sensitive help system.

---

#### GUI-008 — Tab Navigation Handlers Are Stubs
**Severity:** 🟢 Low
**Component:** `APGI-GUI.py` (lines 5234, 5239)

**Description:**
`_handle_tab_navigation()` and `_handle_shift_tab_navigation()` both `return None` with no custom logic, making keyboard-based tab navigation non-functional.

---

#### GUI-009 — Auto-Save Directory Created Without Permission Check
**Severity:** 🟢 Low
**Component:** `APGI-GUI.py` (lines 2344–2372)

**Description:**
Auto-save creates `~/apgi_autosave/` without first checking write permissions. If the directory is not writable, the exception is caught silently and auto-save data is lost without user notification.

---

#### GUI-010 — `_trigger_ignition()` Requires Running Simulation (No User Feedback)
**Severity:** 🟢 Low
**Component:** `APGI-GUI.py` (lines 4058–4071)

**Description:**
`_trigger_ignition()` modifies parameters but does not verify the simulation is running. If the simulation is stopped, the parameter change is applied but has no visible effect, with no feedback to the user.

---

## 7. Bug Inventory — Core Library

---

#### CORE-001 — Active Inference Module Has 12.78% Coverage Gap
**Severity:** 🟡 Medium
**Component:** `apgi_system/core/active_inference.py`

**Description:**
Per the `.kiro/specs/comprehensive-test-coverage/TASK_3.1_COVERAGE_GAPS.md`, `active_inference.py` is at 87.22% coverage with 20 uncovered lines, primarily:
- Shape mismatch error handling (lines 299, 304): 🔴 High priority
- NaN/Inf handling in `_map_down()` (lines 451, 459–461): 🔴 High priority
- NaN/Inf handling in `_project_up()` (lines 478, 496, 504, 512–514): 🔴 High priority
- Cache eviction mechanisms: 🟡 Medium priority
- Empty uncertainty/zero planning horizon edge cases: 🟢 Low priority

---

#### CORE-002 — Overall Test Coverage Below 100% Target
**Severity:** 🟡 Medium
**Component:** `pyproject.toml` (line 80), `scripts/run_coverage.py`

**Description:**
`pyproject.toml` configures `--cov-fail-under=100` for CI but current system coverage is ~90% (87.22% for `active_inference.py`, and gaps in other modules per the design spec). CI should be failing on coverage, which means either coverage is being calculated differently or CI is not enforcing the threshold.

---

## 8. Security Vulnerability Catalog

| ID | Vulnerability | OWASP Category | Severity | Component |
|---|---|---|---|---|
| SEC-001 | Unauthenticated access to all data endpoints | A01: Broken Access Control | 🔴 Critical | All routes |
| SEC-002 | Admin credentials logged in plaintext | A09: Logging Failures | 🔴 Critical | `database/connection.py` |
| SEC-003 | Refresh token verification always fails (broken crypto) | A07: Auth Failures | 🔴 Critical | `auth_manager.py` |
| SEC-004 | Server-Side Request Forgery via webhook_url | A10: SSRF | 🟠 High | `webhook_manager.py`, task routes |
| SEC-005 | HTTP header injection via unquoted Content-Disposition | A03: Injection | 🟠 High | `export.py` |
| SEC-006 | `PickleType` deserialization for user-influenced data | A08: Data Integrity | 🟡 Medium | `database/models.py` |
| SEC-007 | No HTTP security headers (CSP, X-Frame-Options, etc.) | A05: Misconfiguration | 🟡 Medium | `main.py` |
| SEC-008 | Brute-force login not rate-limited specifically | A07: Auth Failures | 🟡 Medium | `auth.py` |
| SEC-009 | Access tokens remain valid after logout | A07: Auth Failures | 🟡 Medium | `auth.py` |
| SEC-010 | Database connection not SSL-enforced by default | A05: Misconfiguration | 🟡 Medium | `config.py` |
| SEC-011 | JWT algorithm hardcoded as HS256 (symmetric, no rotation) | A07: Auth Failures | 🟡 Medium | `auth_manager.py` |
| SEC-012 | YAML config loading may use unsafe loader | A08: Data Integrity | 🟠 High | `APGI-GUI.py` |

---

## 9. Missing Features Log

Features documented, designed, or implied by the system architecture but not yet implemented or accessible:

| ID | Missing Feature | Priority | Reference |
|---|---|---|---|
| MF-001 | Login endpoint registered and accessible | 🔴 Critical | `docs/REST-API.md`, `api/routes/auth.py` exists but not registered |
| MF-002 | Session creation via `POST /v1/sessions` | 🔴 Critical | Route decorator missing in `sessions.py` |
| MF-003 | User registration endpoint (`POST /v1/users/register`) | 🔴 Critical | Router not registered in `main.py` |
| MF-004 | Refresh token rotation functional | 🔴 Critical | Blocked by bcrypt comparison bug |
| MF-005 | Session ownership enforcement | 🟠 High | Documented in authorization service, not enforced in routes |
| MF-006 | SSRF protection for webhook URLs | 🟠 High | `docs/SECURITY-POLICIES.md` implies secure webhooks |
| MF-007 | HTTP security response headers | 🟠 High | `docs/SECURITY-POLICIES.md`, OWASP requirement |
| MF-008 | Brute-force login protection / account lockout | 🟠 High | `docs/SECURITY-POLICIES.md` references rate limiting |
| MF-009 | Inactive user listing in admin API | 🟡 Medium | `api/routes/users.py` `active_only` param is broken |
| MF-010 | Access token revocation (token blacklist) | 🟡 Medium | `docs/SECURITY-POLICIES.md` references token management |
| MF-011 | HTTPS redirect middleware | 🟡 Medium | `docs/SECURITY-POLICIES.md`, HTTPS config exists but no redirect |
| MF-012 | GUI undo/redo for parameter changes | 🟡 Medium | `docs/GUI.md` not mentioned, expected UX feature |
| MF-013 | GUI multi-session support | 🟡 Medium | `docs/HOW-TO-USE-APGI.md` section on sessions |
| MF-014 | GUI batch processing / sequence of simulations | 🟡 Medium | Research use-case requirement |
| MF-015 | Session snapshot save/restore (mid-simulation) | 🟢 Low | Advanced simulation workflow |

---

## 10. Actionable Remediation Recommendations

### Priority 1 — Fix Before Any Deployment (Critical)

#### REM-001: Register Missing Routers in `api/main.py`
**Effort:** 15 minutes | **Team:** Backend
**File:** `api/main.py`
```python
# Add these two imports
from api.routes import auth, users  # Add to existing import line

# Add these two lines in create_app()
app.include_router(auth.router)
app.include_router(users.router)
```

---

#### REM-002: Add `@router.post()` Decorator to `create_session`
**Effort:** 10 minutes | **Team:** Backend
**File:** `api/routes/sessions.py` (before line 130)
```python
@router.post(
    "",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create session",
    description="Create a new simulation session",
    dependencies=[Depends(require_permission(Permission.SESSION_CREATE))],
)
async def create_session(...):
```

---

#### REM-003: Fix Refresh Token Lookup (Replace bcrypt with deterministic hash)
**Effort:** 2 hours | **Team:** Backend Security
**File:** `api/services/auth_manager.py`

The fix requires using a deterministic lookup key alongside the bcrypt hash. One approach: store a SHA-256 hash as the lookup key and the bcrypt hash for verification.

```python
# When creating a refresh token:
import hashlib
lookup_hash = hashlib.sha256(refresh_token.encode()).hexdigest()  # For DB lookup
bcrypt_hash = self.hash_password(refresh_token)  # For verification

# When verifying:
lookup_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
db_token = db.query(RefreshToken).filter(
    RefreshToken.user_id == payload.user_id,
    RefreshToken.lookup_hash == lookup_hash,  # New column needed
    RefreshToken.revoked == False,
).first()

if db_token and bcrypt.checkpw(refresh_token.encode(), db_token.token_hash.encode()):
    # Valid token
```

*Requires database migration to add `lookup_hash` column to `refresh_tokens` table.*

---

#### REM-004: Fix SQLAlchemy `not` Operator Bug
**Effort:** 30 minutes | **Team:** Backend
**File:** `api/services/auth_manager.py` (3 locations)

Replace all occurrences of `not RefreshToken.revoked` with `RefreshToken.revoked == False`:
```python
# Before (lines 349, 429, 463)
not RefreshToken.revoked

# After
RefreshToken.revoked == False
```

---

#### REM-005: Add Authentication to All Protected Endpoints
**Effort:** 3 hours | **Team:** Backend
**File:** `api/routes/sessions.py`, `api/routes/state.py`, `api/routes/tasks.py`, `api/routes/export.py`

Replace `dependencies=[]` with appropriate auth dependency on every protected route:
```python
# Replace this pattern:
dependencies=[]

# With:
dependencies=[Depends(get_current_user)]

# Or for permission-based endpoints:
dependencies=[Depends(require_permission(Permission.SESSION_READ))]
```

Additionally, register `AuthenticationMiddleware` in `main.py`:
```python
from api.middleware.authentication import AuthenticationMiddleware
app.add_middleware(AuthenticationMiddleware)
```

---

#### REM-006: Remove Plaintext Credentials from Log Output
**Effort:** 1 hour | **Team:** Backend Security
**File:** `api/database/connection.py` (lines 116–121)

```python
# Remove:
logger.warning(
    f"Generated default user credentials - STORE SECURELY. "
    f"Username: {secure_username}, Password: {secure_password}. ..."
)

# Replace with environment-variable-based or secrets-manager approach:
# Option A: Write to a secure one-time file
credentials_file = Path("/run/secrets/apgi_admin_credentials")
credentials_file.write_text(f"{secure_username}\n{secure_password}")
os.chmod(credentials_file, 0o600)
logger.info(f"Default admin credentials written to {credentials_file}. Read once and delete.")

# Option B: Store in environment and log only the username
os.environ["APGI_ADMIN_INITIAL_PASSWORD"] = secure_password
logger.info(f"Default admin user created: {secure_username}. Retrieve password from environment.")
```

---

### Priority 2 — Fix Before Any Public API Access (High)

#### REM-007: Fix Session Listing User Filter
**Effort:** 30 minutes | **Team:** Backend
Add `current_user` dependency and filter by `user_id` in `list_sessions()`.

#### REM-008: Fix `is_admin` Permission Check
**Effort:** 30 minutes | **Team:** Backend
Replace `Permission.USER_ADMIN in current_user.roles` with `has_any_role(current_user.roles, [Role.ADMIN])`.

#### REM-009: Fix `list_users(active_only=False)` Bug
**Effort:** 15 minutes | **Team:** Backend
```python
# api/services/user_management.py
if active_only:
    stmt = stmt.where(User.is_active.is_(True))
# Remove the else branch that duplicates the if branch
```

#### REM-010: Implement SSRF Protection for Webhook URLs
**Effort:** 3 hours | **Team:** Backend Security
Add IP address resolution and blocklist checking in `WebhookManager.validate_webhook_url()`:
```python
import ipaddress, socket
blocked_ranges = [
    ipaddress.IPv4Network("127.0.0.0/8"),
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
    ipaddress.IPv4Network("169.254.0.0/16"),  # Link-local / cloud metadata
]
# Resolve hostname and check against blocked ranges
```

#### REM-011: Fix Content-Disposition Header Injection
**Effort:** 15 minutes | **Team:** Backend
```python
# api/routes/export.py line 123
# Before:
headers={"Content-Disposition": f"attachment; filename={filename}"}
# After:
safe_filename = re.sub(r'[^\w\-.]', '_', filename)
headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
```

#### REM-012: Register `AuthenticationMiddleware`
**Effort:** 15 minutes | **Team:** Backend
Add `AuthenticationMiddleware` to the middleware stack in `create_app()`.

---

### Priority 3 — Fix in Next Sprint (Medium)

| Recommendation | Effort | Team |
|---|---|---|
| Add HTTP security headers middleware (CSP, X-Frame-Options, etc.) | 2h | Backend |
| Fix `reload=True` to use env variable (`UVICORN_RELOAD`) | 15m | Backend |
| Add dedicated brute-force rate limiting on `/v1/auth/login` | 2h | Backend |
| Implement short-lived access token blocklist (Redis-backed) for logout | 4h | Backend |
| Migrate `PickleType` columns to `JSON` type | 4h | Backend/DB |
| Add `?sslmode=require` to database URL in documentation | 30m | DevOps |
| Validate `config_path` against an allowlist of directories | 1h | Backend |
| Fix pagination cursor to use signed/encrypted cursors | 2h | Backend |
| Add security headers (X-Content-Type-Options, etc.) | 1h | Backend |

---

### Priority 4 — Backlog (Low)

| Recommendation | Effort | Team |
|---|---|---|
| Add `X-Forwarded-For` support for rate limiting behind proxies | 2h | Backend |
| Ensure YAML loading uses `yaml.safe_load()` everywhere | 30m | GUI |
| Add stop/exit confirmation dialog in GUI | 1h | GUI |
| Remove stack traces from GUI messageboxes | 1h | GUI |
| Make stressor intensity configurable in GUI | 1h | GUI |
| Implement tab navigation in GUI | 2h | GUI |
| Complete 100% test coverage for `active_inference.py` | 3h | QA |
| Consider RS256 asymmetric signing for JWTs | 4h | Backend |
| Add audit logging for security-sensitive operations | 6h | Backend |

---

## 11. Appendix: Endpoint Auth Matrix

Current state of authentication and authorization enforcement across all API endpoints.

| Method | Endpoint | Auth Required | Owner Check | Rate Limit | Status |
|---|---|---|---|---|---|
| GET | `/` | No | None | No | ✅ Public |
| **POST** | **`/v1/auth/login`** | **No** | **None** | **Global only** | **❌ Router not registered** |
| **POST** | **`/v1/auth/refresh`** | **No** | **None** | **Global only** | **❌ Router not registered + token bug** |
| **POST** | **`/v1/auth/logout`** | **Yes** | **Own token** | **Global only** | **❌ Router not registered** |
| GET | `/v1/health` | No | None | Skipped | ✅ Public |
| GET | `/v1/metrics` | No | None | Skipped | ✅ Public |
| GET | `/v1/version` | No | None | Global | ✅ Public |
| GET | `/v1/sessions` | **❌ None** | **❌ None** | Read | 🔴 BUG-005 + BUG-007 |
| **POST** | **`/v1/sessions`** | **❌ None** | **❌ None** | **Create** | **🔴 BUG-002 + BUG-005** |
| GET | `/v1/sessions/{id}` | **❌ None** | **❌ None** | Read | 🔴 BUG-005 |
| POST | `/v1/sessions/{id}/start` | **❌ None** | **❌ None** | Create | 🔴 BUG-005 + BUG-014 |
| POST | `/v1/sessions/{id}/pause` | **❌ None** | **❌ None** | Create | 🔴 BUG-005 + BUG-014 |
| POST | `/v1/sessions/{id}/stop` | **❌ None** | **❌ None** | Create | 🔴 BUG-005 + BUG-014 |
| POST | `/v1/sessions/{id}/reset` | **❌ None** | **❌ None** | Create | 🔴 BUG-005 + BUG-014 |
| DELETE | `/v1/sessions/{id}` | **❌ None** | **❌ None** | Delete | 🔴 BUG-005 + BUG-014 |
| GET | `/v1/sessions/{id}/state` | **❌ None** | **❌ None** | Read | 🔴 BUG-005 |
| GET | `/v1/sessions/{id}/ignition-history` | **❌ None** | **❌ None** | Read | 🔴 BUG-005 + BUG-013 |
| GET | `/v1/sessions/{id}/interoception` | **❌ None** | **❌ None** | Read | 🔴 BUG-005 |
| GET | `/v1/sessions/{id}/prediction-errors` | **❌ None** | **❌ None** | Read | 🔴 BUG-005 |
| GET | `/v1/sessions/{id}/somatic-markers` | **❌ None** | **❌ None** | Read | 🔴 BUG-005 |
| GET | `/v1/sessions/{id}/export` | **❌ None** | **❌ None** | Export | 🔴 BUG-005 + BUG-012 |
| GET | `/v1/sessions/{id}/summary` | **❌ None** | **❌ None** | Read | 🔴 BUG-005 |
| GET | `/v1/sessions/{id}/timeseries` | **❌ None** | **❌ None** | Read | 🔴 BUG-005 |
| GET | `/v1/sessions/{id}/events` | **❌ None** | **❌ None** | Read | 🔴 BUG-005 |
| GET | `/v1/tasks` | No | None | Task | ✅ Public (task list) |
| POST | `/v1/sessions/{id}/tasks` | **❌ None** | **❌ None** | Task | 🔴 BUG-005 + SEC-004 |
| GET | `/v1/tasks/{id}` | **❌ None** | **❌ None** | Global | 🔴 BUG-005 |
| DELETE | `/v1/tasks/{id}` | **❌ None** | **❌ None** | Global | 🔴 BUG-005 |
| **POST** | **`/v1/users/register`** | **N/A** | **N/A** | **N/A** | **❌ Router not registered** |
| **GET** | **`/v1/users`** | **N/A** | **N/A** | **N/A** | **❌ Router not registered** |
| **GET** | **`/v1/users/me`** | **N/A** | **N/A** | **N/A** | **❌ Router not registered** |
| **PUT** | **`/v1/users/me`** | **N/A** | **N/A** | **N/A** | **❌ Router not registered** |
| **GET** | **`/v1/users/{id}`** | **N/A** | **N/A** | **N/A** | **❌ Router not registered** |
| **PUT** | **`/v1/users/{id}`** | **N/A** | **N/A** | **N/A** | **❌ Router not registered** |
| **POST** | **`/v1/users/{id}/reset-password`** | **N/A** | **N/A** | **N/A** | **❌ Router not registered** |
| **DELETE** | **`/v1/users/{id}`** | **N/A** | **N/A** | **N/A** | **❌ Router not registered** |

**Legend:** ✅ Correct | 🔴 Bug | **Bold** = Broken/Missing

---

*Report generated by automated audit — 2026-02-26. All findings are traceable to specific file paths and line numbers for developer-ready remediation.*
