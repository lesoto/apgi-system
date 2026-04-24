# APGI System - Incident Runbooks

## 1. High API Error Rate

**Severity**: P1/P2
**Symptoms**: PagerDuty alerts for API error rates exceeding thresholds (e.g. >10 errors/min).
**Actions**:

1. Check structured logs in `/logs` or logging aggregator for `component="alerting"` or `severity="error"`.
2. Determine if it's a specific endpoint failing (view `apgi_api_errors_total` Prometheus metrics).
3. If database related, verify database connection and credentials.
4. Scale up the API pods if the system is overloaded.

## 2. Security Check Failures at Startup

**Severity**: P1
**Symptoms**: API container refuses to start, failing with `Critical security checks failed!`.
**Actions**:

1. Inspect the logs for `SecurityPostureChecker` report.
2. Fix missing environment variables (e.g. `JWT_SECRET_KEY`, `CORS_ORIGINS`).
3. Ensure that `ENVIRONMENT` is correctly set and not forcing `strict_mode=True` inappropriately.

## 3. Redis / Rate Limiter Backend Unreachable

**Severity**: P2
**Symptoms**: Logs showing "Failed to initialize Redis" or "Rate limiter backend unavailable".
**Actions**:

1. Check the Redis server status.
2. Verify `REDIS_URL` in the environment configuration.
3. If Redis is down, consider running the system in degraded mode (disabling rate limiting temporarily via `RATE_LIMIT_ENABLED=false`).

## 4. Degraded Mode Alerts

**Severity**: P3
**Symptoms**: Alerts sent to Slack/PagerDuty regarding non-critical subsystem failure (e.g., metric export failed).
**Actions**:

1. Look at Slack/Teams channel for automated alert payload.
2. Investigate the failing subsystem asynchronously without immediate risk to core operation.
