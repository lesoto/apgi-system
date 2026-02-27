# APGI System — Comprehensive Audit Report

**Date:** 2026-02-27
**Auditor:** Claude Code (claude-sonnet-4-6)
**Repository:** `/home/user/apgi-system`
**Branch:** `claude/app-audit-security-7WlvD`
**Audit Scope:** End-to-end code audit — functionality, security, UI/UX, performance, resilience

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [KPI Scores Table](#2-kpi-scores-table)
3. [Application Overview](#3-application-overview)
4. [Bug Inventory](#4-bug-inventory)
5. [Security Vulnerability Register](#5-security-vulnerability-register)
6. [Missing Features Log](#6-missing-features-log)
7. [Dimension Analysis](#7-dimension-analysis)
8. [Actionable Recommendations](#8-actionable-recommendations)
9. [Appendix — File & Route Map](#9-appendix--file--route-map)

---

## 1. Executive Summary

The **APGI (Allostatic Precision-Gated Ignition) System** is a sophisticated consciousness-modeling simulation platform. It exposes a FastAPI REST API backed by PostgreSQL, Redis, and Celery, with a suite of Tkinter GUI applications. The system implements cutting-edge computational neuroscience (Friston's free energy principle, predictive coding, allostatic regulation) wrapped in professional DevOps infrastructure.

### Overall Health

The codebase demonstrates **excellent architectural intent** — layered middleware, RBAC, structured logging, Prometheus metrics, circuit breakers, property-based tests — but is undermined by a cluster of **logic-level bugs** that break core behaviors at runtime, and a set of **high-impact security gaps** that would be exploitable in production.

| Health Indicator | Assessment |
|---|---|
| Architecture quality | ✅ Strong — clean separation of concerns, modern async patterns |
| Functional correctness | ❌ Critical bugs break session ownership, auth, and import |
| Security posture | ⚠️ Several exploitable vulnerabilities despite robust middleware |
| Test coverage | ⚠️ Framework is excellent but runtime bugs show gaps in e2e tests |
| Documentation | ✅ Comprehensive — 15+ docs, OpenAPI, structured logging |

### Key Findings Summary

- **2 critical bugs** that crash or completely break core features at runtime
- **4 high-severity bugs** that allow privilege escalation or data corruption
- **6 medium-severity bugs** causing incorrect behavior or degraded UX
- **4 critical/high security vulnerabilities** including SSRF, rate-limit bypass, credential exposure
- **5 medium security vulnerabilities**
- **4 missing task type implementations** (present in core but not exposed via API)
- **3 missing API feature areas** (webhook management, admin endpoints, metrics auth)

---

## 2. KPI Scores Table

> **Scoring legend:** 🔴 Critical (&lt;50) · 🟠 Poor (50–64) · 🟡 Acceptable (65–79) · 🟢 Good (80–100)

| Dimension | Score | Status | Primary Driver |
|---|---|---|---|
| **Functional Completeness** | 61 / 100 | 🟠 Poor | Critical import error + session-user ownership bug break two major flows |
| **UI/UX Consistency** | 78 / 100 | 🟡 Acceptable | Error messages, Swagger docs, and response schemas are consistent; pagination cursor design is opaque |
| **Responsiveness & Performance** | 81 / 100 | 🟢 Good | Async I/O, Redis caching, circuit breakers, GZip; query-per-request DB pattern is a concern at scale |
| **Error Handling & Resilience** | 74 / 100 | 🟡 Acceptable | Global exception handlers are solid; several endpoint `except Exception` blocks leak internals |
| **Implementation Quality** | 72 / 100 | 🟡 Acceptable | Excellent patterns (RBAC, circuit breakers, structured logging) negated by several missing edge-case guards |
| **Security** | 57 / 100 | 🟠 Poor | SSRF risk, X-Forwarded-For spoofing, JWT misuse as cursor, unauthenticated metrics, plain-text password responses |
| **Overall** | **70 / 100** | 🟡 Acceptable | Promising architecture. Critical and high issues must be resolved before production use. |

---

## 3. Application Overview

### Technology Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.110+ with Uvicorn |
| Database | PostgreSQL 14 via SQLAlchemy 2.0 + Alembic migrations |
| Cache / Broker | Redis 7 (sessions, rate limiting, Celery broker) |
| Task Queue | Celery 5.3 |
| Authentication | JWT (HS256 via PyJWT) + bcrypt passwords |
| Authorization | Custom RBAC (admin / researcher / viewer) |
| Monitoring | Prometheus + structured JSON logging |
| GUI | Tkinter desktop applications |
| Testing | pytest + Hypothesis (property-based) + pytest-asyncio |
| Deployment | Docker Compose (PostgreSQL + Redis + API + Celery worker) |

### Route Inventory (48 endpoints across 9 routers)

| Router | Prefix | Endpoint Count | Auth Required |
|---|---|---|---|
| Auth | `/v1/auth` | 3 | Partial (login/refresh are public) |
| Sessions | `/v1/sessions` | 11 | Yes |
| State | `/v1/sessions/{id}/` | 7 | Yes |
| Tasks | `/v1/tasks` | 5 | Yes |
| Export | `/v1/sessions/{id}/export` | 3 | Yes |
| Users | `/v1/users` | 7 | Yes (admin for most) |
| Health | `/v1/health` | 2 | No |
| **Metrics** | `/v1/metrics` | 1 | **No (bug)** |
| Version | `/v1/version` | 2 | No |

---

## 4. Bug Inventory

Bugs are listed in priority order (critical → low). Each entry includes reproduction steps, affected location, expected vs. actual behavior, and recommended fix.

---

### BUG-001 — Critical: `get_session_manager` ImportError Crashes State Routes Module

**Severity:** 🔴 Critical
**Component:** `api/routes/state.py` → `api/services/session_manager.py`
**Type:** Import Error / Runtime Crash

**Description:**
`api/routes/state.py` line 38 imports `get_session_manager` from `api.services.session_manager`:

```python
from api.services.session_manager import SessionManager, get_session_manager
```

The function `get_session_manager` **does not exist** in `api/services/session_manager.py`. It is defined only in `api/routes/sessions.py`. This causes an `ImportError` the moment Python loads the state routes module, making **all 7 state endpoints** (`/state`, `/ignition-history`, `/prediction-errors`, `/somatic-markers`, `/interoception`, etc.) completely unreachable.

**Verification:**
```
$ python -c "from api.services.session_manager import get_session_manager"
ImportError: cannot import name 'get_session_manager' from 'api.services.session_manager'
```

**Affected URLs:**
- `GET /v1/sessions/{session_id}/state`
- `GET /v1/sessions/{session_id}/ignition-history`
- `GET /v1/sessions/{session_id}/prediction-errors`
- `GET /v1/sessions/{session_id}/somatic-markers`
- `GET /v1/sessions/{session_id}/interoception`

**Expected:** State endpoints load and return simulation state data.
**Actual:** `ImportError` at module load time; all state routes return 500 or fail to register.

**Fix:** Move `get_session_manager` from `api/routes/sessions.py` to `api/services/session_manager.py` (or to a shared dependency module), and update all imports accordingly.

**Effort:** Low (30 minutes)
**Team:** Backend

---

### BUG-002 — Critical: Session Creation Never Stores Authenticated User's ID

**Severity:** 🔴 Critical
**Component:** `api/routes/sessions.py:169`
**Type:** Authorization / Data Integrity

**Description:**
The `create_session` route handler calls the session manager **without passing the current user's ID**:

```python
# api/routes/sessions.py line 169
session_id = await manager.create_session(request)  # current_user.user_id NOT passed
```

The `create_session` method signature in `api/services/session_manager.py` (line 346) is:

```python
async def create_session(self, request: SessionCreateRequest, user_id: str = "default_user") -> str:
```

Because `user_id` defaults to `"default_user"`, **every session created by every user is stored with `user_id = "default_user"` in the database**. This has two consequences:

1. Ownership checks (`sim_session.user_id != current_user.user_id`) will always pass for admin-created default users, so **non-admin users can access each other's sessions**.
2. The `list_sessions` filter by user (`stmt.where(SessionModel.user_id == user_id)`) is permanently broken — all sessions appear to belong to the same dummy user.

**Affected URLs:**
- `POST /v1/sessions` (creates session with wrong owner)
- `GET /v1/sessions` (lists sessions of wrong user)
- All session-scoped endpoints that rely on ownership

**Expected:** Sessions are created and associated with the authenticated user's ID.
**Actual:** All sessions associated with `"default_user"`.

**Fix:**
```python
# api/routes/sessions.py
session_id = await manager.create_session(request, user_id=current_user.user_id)
```

**Effort:** Low (15 minutes)
**Team:** Backend

---

### BUG-003 — High: Logout / Token Blacklisting is Broken

**Severity:** 🟠 High
**Component:** `api/routes/auth.py` (logout endpoint)
**Type:** Logic Error / Security

**Description:**
The logout endpoint extracts the token from `request.headers`, but `request` in this context is the **Pydantic request body model** (`TokenRefreshRequest`), not the HTTP `Request` object. Pydantic models have no `.headers` attribute. The Authorization header is never read, so the access token is never blacklisted.

**Affected URLs:** `POST /v1/auth/logout`

**Expected:** Logout invalidates the user's current access token.
**Actual:** Logout returns success but does NOT invalidate the token; tokens remain valid until expiry.

**Fix:** Inject `Request` as a separate FastAPI dependency:
```python
@router.post("/logout")
async def logout(
    http_request: Request,          # ← actual HTTP request
    request: TokenRefreshRequest,   # ← body
    ...
):
    auth_header = http_request.headers.get("Authorization")
    ...
```

**Effort:** Low (30 minutes)
**Team:** Backend

---

### BUG-004 — High: Session Delete Fails for Cache-Evicted Sessions

**Severity:** 🟠 High
**Component:** `api/services/session_manager.py:507-527`
**Type:** Logic Error / Data Availability

**Description:**
The `delete_session` method checks if the session exists **in the in-memory cache** before even acquiring the lock:

```python
async def delete_session(self, session_id: str) -> None:
    # ...
    async with self.cache_lock:
        if session_id not in self.sessions:   # <-- checks MEMORY cache only
            raise ValueError(f"Session {session_id} not found")
```

Sessions are evicted from memory after 1 hour TTL or when the 1000-session LRU limit is reached. After eviction, `delete_session` raises `ValueError` even though the session may exist in the database — making it **impossible to delete old or evicted sessions**.

Additionally, there is a double-lock acquisition pattern that creates a TOCTOU race condition.

**Affected URLs:** `DELETE /v1/sessions/{session_id}`

**Expected:** Sessions can be deleted from the database regardless of their in-memory cache status.
**Actual:** Delete fails with 404/500 for sessions not currently in the in-memory cache.

**Fix:** Fall through to database lookup if the session is not in the cache, rather than immediately raising an error.

**Effort:** Medium (2 hours)
**Team:** Backend

---

### BUG-005 — High: Unauthenticated Prometheus Metrics Endpoint

**Severity:** 🟠 High
**Component:** `api/routes/metrics.py`
**Type:** Security — Information Disclosure

**Description:**
The `/v1/metrics` Prometheus endpoint has **no authentication requirement**:

```python
@router.get("/metrics")  # No Depends(require_permission(...))
async def metrics_endpoint():
    return get_metrics_response()
```

All other endpoints (except health/version) are protected. This endpoint exposes request counts, error rates, latencies, active sessions, and system resource data to any unauthenticated caller.

**Affected URL:** `GET /v1/metrics`

**Expected:** Metrics endpoint requires at minimum `admin` role.
**Actual:** Freely accessible without any credentials.

**Fix:**
```python
@router.get("/metrics", dependencies=[Depends(require_permission(Permission.SYSTEM_ADMIN))])
async def metrics_endpoint():
    ...
```
Or protect it at the network layer (restrict to internal network / Prometheus scrape IP only).

**Effort:** Low (1 hour)
**Team:** Backend / DevOps

---

### BUG-006 — High: `SimulationSession` Has No `user_id` Attribute

**Severity:** 🟠 High
**Component:** `api/services/session_manager.py:76-115`, `api/routes/sessions.py:215`
**Type:** AttributeError / Authorization Bypass

**Description:**
Multiple route handlers check session ownership via `sim_session.user_id`:

```python
if sim_session.user_id != current_user.user_id and not has_any_role(...):
    raise HTTPException(status_code=403, ...)
```

However, the `SimulationSession` class (defined in `api/services/session_manager.py`) **does not define a `user_id` attribute**:

```python
class SimulationSession:
    def __init__(self, session_id: str, config: Dict[str, Any]):
        self.session_id = session_id
        self.config = config
        self.state = SessionLifecycleState.CREATED
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        # NO self.user_id defined
```

Accessing `sim_session.user_id` will raise an `AttributeError`, causing a 500 error on any ownership-checked endpoint, or — if caught by the broad `except Exception` — silently bypass the ownership check.

**Affected URLs:** All session-scoped endpoints that perform ownership checks (state, sessions, tasks, export routes).

**Expected:** Ownership check correctly compares session's owner against current user.
**Actual:** `AttributeError: 'SimulationSession' object has no attribute 'user_id'` → 500 or bypass.

**Fix:** Add `self.user_id` to `SimulationSession.__init__` and populate it during creation:
```python
def __init__(self, session_id: str, config: Dict[str, Any], user_id: str = "default_user"):
    ...
    self.user_id = user_id
```
Also fix BUG-002 to correctly pass the authenticated user's ID.

**Effort:** Low (1 hour)
**Team:** Backend

---

### BUG-007 — Medium: JWT Used as Pagination Cursor for Ignition History

**Severity:** 🟡 Medium
**Component:** `api/routes/state.py:268-293`
**Type:** Design / Minor Security

**Description:**
The `/ignition-history` endpoint uses `jwt.encode` / `jwt.decode` with the **JWT authentication secret key** to create opaque pagination cursors:

```python
cursor_data = {"offset": end_idx}
next_cursor = jwt.encode(cursor_data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
```

Issues:
1. This misuses the authentication secret for a completely unrelated purpose.
2. The cursor leaks the JWT algorithm to clients in the pagination token.
3. If the JWT secret is rotated, all existing cursors become invalid.
4. An attacker who can obtain a cursor learns the algorithm and key structure.

**Fix:** Use a simple base64url-encoded JSON object or opaque timestamp cursor instead of a JWT for pagination. The `next_cursor` can simply be `base64.urlsafe_b64encode(json.dumps({"offset": end_idx}).encode()).decode()`.

**Effort:** Low (1 hour)
**Team:** Backend

---

### BUG-008 — Medium: Incomplete Pause/Resume State Restoration

**Severity:** 🟡 Medium
**Component:** `api/services/session_manager.py:285-292`
**Type:** Functional Correctness

**Description:**
The `_restore_state` method, called during session resume, only restores `time` and `history`:

```python
def _restore_state(self, state: Dict[str, Any]) -> None:
    self.apgi_system.time = state.get("time", 0.0)
    self.apgi_system.history = state.get("history", {})
    # NOTE: ignition, precision, workspace, body, allostasis, metabolism,
    # self_model subsystems NOT restored
```

When a session is paused and later resumed, the simulation will continue from the wrong internal state — only time and history are preserved, while all subsystem states (free energy, precision weights, ignition threshold, allostatic load, metabolic reserves, etc.) reset to defaults.

**Affected URL:** `POST /v1/sessions/{session_id}/resume` (after a pause)

**Expected:** Full subsystem state is preserved across pause/resume cycles.
**Actual:** Only time and history are restored; all other subsystem state is lost.

**Fix:** Implement full state serialization/deserialization for all subsystems in `_capture_state` and `_restore_state`.

**Effort:** High (1-2 days — requires deep subsystem state serialization)
**Team:** Backend / Core Science

---

### BUG-009 — Medium: Error Messages Leak Internal Details

**Severity:** 🟡 Medium
**Component:** `api/routes/state.py:159-163`, similar patterns in `sessions.py`, `tasks.py`
**Type:** Information Disclosure

**Description:**
Several `except Exception` blocks include the raw exception in the HTTP error detail:

```python
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"Failed to get system state: {str(e)}",  # <-- exposes internal error
    )
```

This can expose internal class names, file paths, database errors, and stack information to API clients.

**Affected URLs:** Multiple state, session, and task endpoints.

**Expected:** Generic, safe error message returned to clients; full details logged server-side.
**Actual:** Raw exception message included in API response body.

**Fix:** Replace `detail=f"...{str(e)}"` with a safe static message. Ensure full error is captured only in server logs via `logger.error(..., exc_info=True)`.

**Effort:** Low (2 hours)
**Team:** Backend

---

### BUG-010 — Medium: Rate Limiter Fallback Called Without `await`

**Severity:** 🟡 Medium
**Component:** `api/middleware/rate_limiting.py`
**Type:** Async/Sync Mismatch

**Description:**
The rate limiting middleware has a Redis-backed primary limiter and an in-memory fallback. The fallback `check_rate_limit` is called synchronously (without `await`) in what appears to be an async context, likely causing a coroutine to be returned instead of a boolean result — meaning the rate limit is **never actually enforced** when Redis is unavailable.

**Expected:** In-memory fallback correctly enforces rate limits when Redis is down.
**Actual:** Fallback returns an awaitable coroutine object (truthy), bypassing rate limiting.

**Fix:** Ensure the fallback rate limiter either uses synchronous code or is properly awaited.

**Effort:** Low (1 hour)
**Team:** Backend

---

### BUG-011 — Medium: No Email Format Validation on User Update

**Severity:** 🟡 Medium
**Component:** `api/models/schemas.py:591-606`
**Type:** Input Validation

**Description:**
`UserCreateRequest` has no email format validator and `UserUpdateRequest` also has no email validation:

```python
class UserUpdateRequest(BaseModel):
    email: Optional[str] = Field(None, description="New email address")
    # No validator, no EmailStr
```

Invalid email strings (e.g., `"not-an-email"`, `"<script>alert(1)</script>"`) can be stored in the database.

**Fix:** Use Pydantic's `EmailStr` type or add a `@field_validator` for email format validation on both request models.

**Effort:** Low (30 minutes)
**Team:** Backend

---

### BUG-012 — Low: `create_default_user` Writes Credentials File to Docker-Incompatible Path

**Severity:** 🔵 Low
**Component:** `api/database/connection.py:119-123`
**Type:** Deployment / Configuration

**Description:**
On first startup, the system writes admin credentials to `/run/secrets/apgi_admin_credentials`. In Docker environments that do not mount `/run/secrets`, the `Path.parent.mkdir(parents=True, exist_ok=True)` call may fail silently or the file may be inaccessible.

**Fix:** Make the credentials file path configurable via an environment variable, or log credentials to the application log (with a warning to rotate immediately) as a safer fallback.

**Effort:** Low (1 hour)
**Team:** Backend / DevOps

---

## 5. Security Vulnerability Register

---

### SEC-001 — Critical: SSRF via DNS Rebinding in Webhook URL Validation

**Severity:** 🔴 Critical
**OWASP Category:** A10:2021 — Server-Side Request Forgery (SSRF)
**Component:** `api/services/webhook_manager.py`

**Description:**
Webhook URL validation resolves the DNS hostname at validation time to check against a blocklist of private IP ranges. However, the actual HTTP request is sent later (time-of-check to time-of-use gap). An attacker can:

1. Register a webhook pointing to an attacker-controlled domain that initially resolves to a public IP (passes validation).
2. After validation, change the DNS record to point to an internal IP (e.g., `169.254.169.254`, `10.0.0.1`, etc.).
3. When the task completes and the webhook fires, the server makes an HTTP request to the internal address.

This allows SSRF to internal services, cloud metadata endpoints, and internal APIs.

**Reproduction Steps:**
1. Set up an attacker domain that resolves to `1.2.3.4` (external, passes blocklist).
2. Submit a task with `webhook_url = "http://attacker.example.com/callback"`.
3. Change DNS TTL/record to point to `169.254.169.254` (AWS metadata).
4. Allow the task to complete — server fetches the metadata endpoint.

**Fix:**
- Re-resolve the DNS immediately before making the HTTP request and re-validate the IP.
- Pin the resolved IP at validation time and use the IP directly (not the hostname) for the request.
- Alternatively, use a separate outbound proxy service for webhooks that enforces egress controls.

**Effort:** Medium (1 day)
**Team:** Backend / Security

---

### SEC-002 — High: Rate Limit Bypass via X-Forwarded-For Spoofing

**Severity:** 🟠 High
**OWASP Category:** A05:2021 — Security Misconfiguration
**Component:** `api/middleware/rate_limiting.py`

**Description:**
The rate limiting middleware determines the client IP by checking the `X-Forwarded-For` header:

```python
client_ip = request.headers.get("X-Forwarded-For", request.client.host)
```

An attacker can completely bypass IP-based rate limiting by injecting a fake `X-Forwarded-For: 1.2.3.4` header, making the server believe all requests come from arbitrary different IPs.

**Fix:**
- Only trust `X-Forwarded-For` when the request arrives from a known proxy IP (configure a `TRUSTED_PROXIES` list).
- Use `request.client.host` directly in environments without a reverse proxy.
- For deployments behind a load balancer, use a library like `starlette-client-ip` that handles proxy trust correctly.

**Effort:** Medium (half day)
**Team:** Backend / DevOps

---

### SEC-003 — High: Plain-Text Password Returned in API Responses

**Severity:** 🟠 High
**OWASP Category:** A02:2021 — Cryptographic Failures
**Component:** `api/models/schemas.py:555-558`, `api/models/schemas.py:621-626`

**Description:**
Two response schemas return plain-text passwords to API clients:

```python
class UserCreateResponse(BaseModel):
    ...
    password: str = Field(..., description="Plain text password (only returned once)")

class PasswordResetResponse(BaseModel):
    ...
    new_password: str = Field(..., description="New plain text password")
```

While the intent is a one-time credential handoff, returning passwords in HTTP responses risks:
- Password exposure in server logs, reverse proxies, and SIEM systems that log response bodies.
- Accidental exposure if HTTPS is not enforced.
- Violation of security policies that prohibit plain-text password transmission.

**Fix:**
- Return an initial authentication link/token instead of the plain-text password.
- If the plain-text password must be returned, add an explicit deprecation warning in the response and ensure TLS is mandatory.
- Ensure response logging middleware explicitly strips the `password` and `new_password` fields.

**Effort:** Medium (1 day — may require UX decisions)
**Team:** Backend / Security

---

### SEC-004 — High: Hardcoded Database Credentials in Docker Compose

**Severity:** 🟠 High
**OWASP Category:** A07:2021 — Identification and Authentication Failures
**Component:** `docker-compose.yml`

**Description:**
The Docker Compose file hardcodes database credentials and does not set `JWT_SECRET_KEY`:

```yaml
environment:
  POSTGRES_PASSWORD: apgi_password   # hardcoded weak credential
  DATABASE_URL: postgresql://apgi:apgi_password@postgres:5432/apgi_api
  # JWT_SECRET_KEY: NOT SET → uses development default
```

Without `JWT_SECRET_KEY`, the application falls back to its development default (`your-secret-key-change-in-production-min-32-chars`), which is publicly documented in `.env.example`. Any JWT token signed with this key is verifiable by anyone who reads the repository.

**Fix:**
- Remove hardcoded passwords from `docker-compose.yml`.
- Use Docker Secrets (`secrets:` block) or environment files (`.env` excluded from git).
- Explicitly set `JWT_SECRET_KEY` to a cryptographically random value (≥32 bytes) in all deployment environments.

**Effort:** Low (2 hours)
**Team:** DevOps / Security

---

### SEC-005 — Medium: Username Enumeration via Timing Attack

**Severity:** 🟡 Medium
**OWASP Category:** A07:2021 — Identification and Authentication Failures
**Component:** `api/services/auth_manager.py`

**Description:**
The login flow handles non-existent users and wrong-password differently in terms of code execution time:
- Non-existent user: immediately returns `None` after a single database query.
- Existing user with wrong password: executes `bcrypt.checkpw(...)` which deliberately takes ~100ms.

This timing difference allows an attacker to enumerate valid usernames by measuring response times.

**Fix:**
Always run `bcrypt.checkpw` against a dummy hash when the user is not found, to equalize response time regardless of username validity:
```python
if not user:
    bcrypt.checkpw(password.encode(), b"$2b$04$fakehash")  # constant-time dummy
    return None
```

**Effort:** Low (30 minutes)
**Team:** Backend

---

### SEC-006 — Medium: Account Lockout Silently Disabled When Redis is Unavailable

**Severity:** 🟡 Medium
**Component:** `api/services/auth_manager.py` (lockout tracking)
**OWASP Category:** A07:2021 — Identification and Authentication Failures

**Description:**
Failed login attempt tracking is stored in Redis. If Redis is unavailable, the lockout mechanism silently fails and brute-force protection is lost. There is no in-memory fallback for failed attempt counting.

**Fix:**
- Add an in-memory fallback counter (thread-safe `defaultdict`) that activates when Redis is unreachable.
- Alert operators when the Redis-backed lockout is unavailable.

**Effort:** Medium (half day)
**Team:** Backend

---

### SEC-007 — Medium: CORS Not Configured in Docker Compose

**Severity:** 🟡 Medium
**Component:** `docker-compose.yml`, `api/config.py`
**OWASP Category:** A05:2021 — Security Misconfiguration

**Description:**
The Docker Compose file sets no `CORS_ORIGINS` environment variable. The default in `.env.example` is `http://localhost:3000,http://localhost:8080` — localhost-only. In production deployments where the API is accessed from a different origin, CORS will reject all browser-based requests unless the variable is set.

**Fix:** Document required production CORS values in the deployment guide. Add a startup warning if `CORS_ORIGINS` contains `localhost` and `ENVIRONMENT=production`.

**Effort:** Low (1 hour)
**Team:** DevOps / Backend

---

### SEC-008 — Medium: Health Endpoint Exposes Infrastructure Information Without Auth

**Severity:** 🟡 Medium
**Component:** `api/routes/health.py`
**OWASP Category:** A05:2021 — Security Misconfiguration

**Description:**
The `/v1/health` endpoint returns detailed component status (database, Redis, Celery version/connectivity) without authentication. While health endpoints are commonly public, returning internal component names and versions increases the attack surface for targeted exploits.

**Fix:**
- Return a minimal `{"status": "healthy"}` for unauthenticated requests.
- Return detailed component checks only for authenticated admin users.
- Alternatively, restrict the endpoint to internal network access at the load balancer level.

**Effort:** Low (1 hour)
**Team:** Backend / DevOps

---

## 6. Missing Features Log

### FEAT-001 — Four Experimental Tasks Not Exposed via API

**Priority:** High
**Component:** `api/services/task_executor.py`, `apgi_system/experiments/tasks/`

**Description:**
The core simulation has 7 experimental task implementations, but only 3 are listed in `task_executor.list_available_tasks()` and registered in `TaskType` enum:

| Task | Core Implementation | API Exposed |
|---|---|---|
| Iowa Gambling Task | ✅ `iowa_gambling.py` | ✅ |
| Visual Masking Paradigm | ✅ `masking_paradigm.py` | ✅ |
| Attentional Blink | ✅ `attentional_blink.py` | ✅ |
| **Binocular Rivalry** | ✅ `binocular_rivalry.py` | ❌ |
| **Change Blindness** | ✅ `change_blindness.py` | ❌ |
| **N-Back Task** | ✅ `nback_task.py` | ❌ |
| **Stroop Task** | ✅ `stroop_task.py` | ❌ |

**Impact:** 4 of 7 task types are invisible to API consumers. Approximately 57% of the experimental paradigm suite is inaccessible via the API.

**Fix:** Register the four missing tasks in `api/tasks/task_registry.py` and add them to `list_available_tasks()`.

**Effort:** Medium (1–2 days per task, including Celery task wrappers and parameter documentation)
**Team:** Backend / Core Science

---

### FEAT-002 — No Webhook Management API

**Priority:** Medium
**Component:** `api/services/webhook_manager.py` (service exists but no routes)

**Description:**
The `WebhookManager` service provides webhook delivery tracking and retry logic, but there are **no REST API endpoints** for:
- Listing webhooks registered for a session or task.
- Viewing webhook delivery history and retry status.
- Manually retrying a failed webhook.
- Deleting/disabling a webhook.

Users can only set a `webhook_url` at task submission time with no subsequent visibility or control.

**Fix:** Add a `/v1/webhooks` or `/v1/sessions/{id}/webhooks` router with CRUD endpoints backed by `WebhookDeliveries` table.

**Effort:** Medium (2–3 days)
**Team:** Backend

---

### FEAT-003 — No System Administration Endpoints

**Priority:** Medium
**Component:** API layer

**Description:**
There are no endpoints for system-level administration beyond user management:
- No endpoint to list/view active Celery workers.
- No endpoint to view or clear the Redis cache.
- No endpoint to view circuit breaker states.
- No endpoint to trigger database maintenance (vacuum, analyze).
- No endpoint to view current rate limiting state per user.

**Fix:** Add an `/v1/admin/` router (admin-only) with system inspection capabilities.

**Effort:** High (3–5 days)
**Team:** Backend / DevOps

---

### FEAT-004 — No Summary Statistics Endpoint Implementation

**Priority:** Low
**Component:** `api/routes/state.py` (or export routes)

**Description:**
The `SummaryStatistics` schema is defined in `api/models/schemas.py` (lines 465-474) and referenced in documentation, but there is no corresponding endpoint that returns summary statistics for a session. The field includes `duration_ms`, `num_steps`, `ignition_stats`, `energy_stats`, and `allostasis_stats`.

**Fix:** Implement `GET /v1/sessions/{session_id}/summary-statistics` endpoint that aggregates session history data into the `SummaryStatistics` response.

**Effort:** Medium (1 day)
**Team:** Backend / Core Science

---

### FEAT-005 — Missing Refresh Token Revocation on Logout

**Priority:** Medium
**Component:** `api/routes/auth.py` (logout)

**Description:**
Due to BUG-003 (logout doesn't correctly read the Authorization header), access token blacklisting is broken. Additionally, the logout endpoint may not revoke the associated refresh token either. A user who logs out still has a valid refresh token that can generate new access tokens for up to 7 days.

**Fix:** After fixing BUG-003, also ensure the refresh token for the current session is invalidated in the `RefreshTokens` table (`revoked = True`).

**Effort:** Low (1 hour, after BUG-003 fix)
**Team:** Backend

---

## 7. Dimension Analysis

### 7.1 Functional Completeness — 61/100

**Evaluation Criteria:** All advertised features work correctly, all happy paths and edge cases produce expected results, no broken imports or crash paths.

**Findings:**
- 2 critical bugs (BUG-001, BUG-002) completely break state endpoints and session ownership — together these affect 12+ of 48 endpoints.
- BUG-003 breaks logout token invalidation.
- BUG-006 makes ownership checks raise `AttributeError` at runtime.
- 4 task types documented in the core system are not reachable via the API (FEAT-001).
- Pause/resume state restoration is functionally incomplete (BUG-008).
- `SummaryStatistics` schema defined but no matching endpoint (FEAT-004).

**What works well:** Session creation/listing (minus ownership), task submission for 3 task types, authentication/authorization middleware, health checks, data export, user management.

---

### 7.2 UI/UX Consistency — 78/100

**Evaluation Criteria:** Consistent error response format, predictable HTTP status codes, clear field naming, documentation aligned with implementation, pagination usable.

**Findings:**
- ✅ Consistent error format `{"error": {"code": ..., "message": ..., "request_id": ..., "timestamp": ..., "details": ...}}` across all handlers.
- ✅ OpenAPI docs available at `/docs` and `/redoc`.
- ✅ Pagination implemented on session list.
- ✅ Clear HTTP status code usage (422 for validation, 404 for not-found, 403 for auth failures).
- ⚠️ Pagination cursor for ignition history is a JWT token — opaque and confusing for API consumers (BUG-007).
- ⚠️ `UserCreateResponse.password` field is surprising to clients and violates REST convention (SEC-003).
- ⚠️ Some 500 errors expose raw exception strings instead of safe messages (BUG-009).
- ⚠️ `list_sessions` always returns sessions for "default_user" regardless of authenticated user (BUG-002).

---

### 7.3 Responsiveness & Performance — 81/100

**Evaluation Criteria:** Non-blocking I/O, connection pooling, caching, efficient queries, appropriate timeouts.

**Findings:**
- ✅ Async I/O throughout (FastAPI + asyncio + `asyncio.to_thread` for sync Celery calls).
- ✅ Redis caching for session metadata with 1-hour TTL.
- ✅ Connection pooling: `pool_size=10, max_overflow=20`.
- ✅ Circuit breakers on database and Redis operations prevent cascade failures.
- ✅ GZip compression on responses ≥ 1000 bytes.
- ✅ In-memory session cache (LRU, max 1000 entries) for hot sessions.
- ⚠️ `get_user_stats` in `user_management.py:332-348` performs two full table scans (list all users twice). Should use COUNT queries.
- ⚠️ `get_session` falls back to full database load + re-creates the `SimulationSession` object (heavyweight APGI system init) on cache miss — no lazy loading.
- ⚠️ `_cleanup_expired_sessions` is called on every `get_session` and `create_session` — O(n) scan of in-memory cache with lock held.

---

### 7.4 Error Handling & Resilience — 74/100

**Evaluation Criteria:** All exceptions handled gracefully, no unhandled promise rejections, meaningful error codes, circuit breakers, fallback behavior.

**Findings:**
- ✅ Global exception handlers registered for `APIError`, `RequestValidationError`, `HTTPException`, and catch-all `Exception`.
- ✅ Circuit breakers on database persistence and Redis cache operations.
- ✅ Request body safely captured (with sensitive field redaction) in unhandled exception handler.
- ✅ Error alerting middleware with configurable thresholds and cooldown.
- ⚠️ BUG-001 (`ImportError` in state routes) is a hard crash that bypasses all exception handlers.
- ⚠️ BUG-009: Several `except Exception as e` blocks expose internal error details.
- ⚠️ Redis unavailability silently disables account lockout (SEC-006) with no operator alert.
- ⚠️ Rate limit fallback async mismatch (BUG-010) silently disables rate limiting under Redis failure.

---

### 7.5 Implementation Quality — 72/100

**Evaluation Criteria:** Code correctness, adherence to patterns, type safety, test coverage for critical paths, no anti-patterns.

**Findings:**
- ✅ Consistent use of Pydantic v2 models with `ConfigDict` and `field_validator`.
- ✅ RBAC implementation is well-structured and permission-granular.
- ✅ Database models use proper SQLAlchemy 2.0 ORM patterns with `select()`.
- ✅ Structured JSON logging with request IDs for distributed tracing.
- ✅ Extensive property-based tests (Hypothesis) and integration tests.
- ❌ BUG-006: `SimulationSession` missing `user_id` attribute — indicates missing type coverage.
- ❌ BUG-001: Import error in production code — indicates absence of import/startup tests.
- ⚠️ Double-lock pattern in `delete_session` (acquire lock twice) is a code smell.
- ⚠️ `create_default_user` in `connection.py` duplicates logic already in `user_management.py` and `auth.py`.
- ⚠️ `_restore_state` has a `# This is a simplified restoration - in production...` comment in production code.

---

## 8. Actionable Recommendations

### Priority P0 — Fix Before Any Production Deployment

| ID | Issue | Action | Effort | Team |
|---|---|---|---|---|
| BUG-001 | ImportError crashes state routes | Move `get_session_manager` to `session_manager.py` | 30 min | Backend |
| BUG-002 | Sessions always owned by "default_user" | Pass `current_user.user_id` to `create_session` | 15 min | Backend |
| BUG-006 | `SimulationSession` missing `user_id` | Add `user_id` param to `__init__` | 1 hour | Backend |
| SEC-004 | Default JWT secret in Docker Compose | Add `JWT_SECRET_KEY` env var to all deployments | 2 hours | DevOps |

### Priority P1 — Fix Within First Sprint

| ID | Issue | Action | Effort | Team |
|---|---|---|---|---|
| BUG-003 | Logout broken (wrong request object) | Inject `Request` as separate dependency | 30 min | Backend |
| BUG-004 | Delete fails for evicted sessions | Fall through to DB lookup if not in cache | 2 hours | Backend |
| BUG-005 | Metrics endpoint unauthenticated | Add `require_permission(SYSTEM_ADMIN)` | 1 hour | Backend |
| SEC-001 | SSRF via DNS rebinding | Re-validate IP immediately before HTTP request | 1 day | Backend |
| SEC-002 | Rate limit bypass via header spoofing | Implement trusted proxy IP list | Half day | Backend |
| SEC-003 | Passwords returned in API responses | Remove plaintext passwords from response models | 1 day | Backend |

### Priority P2 — Fix Within Second Sprint

| ID | Issue | Action | Effort | Team |
|---|---|---|---|---|
| BUG-007 | JWT as pagination cursor | Replace with base64-encoded offset cursor | 1 hour | Backend |
| BUG-008 | Incomplete pause/resume state | Implement full subsystem serialization | 2 days | Backend/Science |
| BUG-009 | Internal errors in responses | Replace `str(e)` with generic message + server log | 2 hours | Backend |
| BUG-010 | Rate limit fallback async mismatch | Fix sync/async discrepancy | 1 hour | Backend |
| BUG-011 | No email validation | Add `EmailStr` or validator to user models | 30 min | Backend |
| SEC-005 | Username enumeration via timing | Add constant-time dummy bcrypt call | 30 min | Backend |
| SEC-006 | Lockout disabled without Redis | Add in-memory fallback counter | Half day | Backend |
| FEAT-001 | 4 tasks not exposed in API | Register and implement task routes | 2–4 days | Backend |
| FEAT-005 | Refresh token not revoked on logout | Revoke refresh token on logout | 1 hour | Backend |

### Priority P3 — Backlog

| ID | Issue | Action | Effort | Team |
|---|---|---|---|---|
| BUG-012 | Credentials file path incompatible | Make path configurable via env var | 1 hour | DevOps |
| SEC-007 | CORS not configured in Docker | Document and add prod CORS values | 1 hour | DevOps |
| SEC-008 | Health endpoint exposes details | Return minimal response for unauthenticated | 1 hour | Backend |
| FEAT-002 | No webhook management API | Add `/v1/webhooks` CRUD router | 3 days | Backend |
| FEAT-003 | No admin system endpoints | Add `/v1/admin/` router | 5 days | Backend |
| FEAT-004 | Summary statistics endpoint missing | Implement `GET /{session_id}/summary-statistics` | 1 day | Backend |

---

## 9. Appendix — File & Route Map

### Critical File Reference

| File | Purpose | Key Issues |
|---|---|---|
| `api/routes/sessions.py` | Session CRUD + lifecycle | BUG-002 (user_id not passed) |
| `api/routes/state.py` | System state endpoints | BUG-001 (bad import), BUG-009 |
| `api/routes/auth.py` | Authentication endpoints | BUG-003 (logout broken) |
| `api/routes/metrics.py` | Prometheus metrics | BUG-005 (no auth) |
| `api/services/session_manager.py` | Session lifecycle, cache | BUG-004, BUG-006, BUG-008 |
| `api/services/auth_manager.py` | JWT, bcrypt, lockout | SEC-005, SEC-006 |
| `api/services/webhook_manager.py` | Webhook delivery | SEC-001 (SSRF) |
| `api/services/task_executor.py` | Task submission | FEAT-001 (4 tasks missing) |
| `api/middleware/rate_limiting.py` | Rate limiting | SEC-002, BUG-010 |
| `api/models/schemas.py` | Request/response models | SEC-003, BUG-011 |
| `api/database/connection.py` | DB init, default user | BUG-012 |
| `docker-compose.yml` | Container orchestration | SEC-004, SEC-007 |

### Database Tables

| Table | Purpose | Notable |
|---|---|---|
| `users` | User accounts | bcrypt hashed passwords |
| `sessions` | Simulation sessions | `user_id` FK — currently always "default_user" (BUG-002) |
| `tasks` | Async task tracking | `webhook_url` stored per task |
| `session_data` | Time-series snapshots | `(session_id, time_ms)` indexed |
| `refresh_tokens` | JWT refresh tokens | bcrypt hashed, revocable |
| `webhook_deliveries` | Webhook attempt log | Retry scheduling |

### Environment Variable Checklist

| Variable | Required | Default | Risk If Unset |
|---|---|---|---|
| `DATABASE_URL` | Yes | localhost dev URL | App fails to start |
| `REDIS_URL` | Yes | localhost dev URL | Caching/rate limiting disabled |
| `JWT_SECRET_KEY` | **Yes** | Development placeholder | **All tokens forgeable** |
| `CORS_ORIGINS` | Yes | localhost only | CORS blocks all browser traffic |
| `ENVIRONMENT` | Yes | `development` | Some security checks skipped |
| `RATE_LIMIT_ENABLED` | No | `true` | Rate limiting disabled |
| `LOG_LEVEL` | No | `INFO` | Verbose or silent logging |

---

*Report generated by automated audit tooling on 2026-02-27. All line numbers referenced against the state of the codebase at the time of audit. This report should be reviewed by the engineering team and used to create tracked issues in the project backlog.*
