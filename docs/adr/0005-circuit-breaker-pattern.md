# ADR 0005: Circuit Breaker Pattern for External Services

## Status

Accepted

## Context

The APGI system integrates with external services (databases, APIs, message queues). Failures in these services can cascade and overwhelm the system with retry attempts.

## Decision

We will implement the Circuit Breaker pattern to provide resilience for external service calls.

## Consequences

### Positive

- Prevents cascade failures
- Fast failure for degraded services
- Automatic recovery detection
- Configurable thresholds

### Negative

- Additional complexity in service calls
- Potential for false positives during temporary issues
- Requires monitoring to tune thresholds

## Implementation

Created `apgi_framework/resilience/` module with:
- `CircuitBreaker`: Singleton pattern per service
- `CircuitState`: CLOSED, OPEN, HALF_OPEN states
- `ResilientClient`: HTTP client with built-in circuit breaker

## Configuration

```python
CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=60.0,
    half_open_max_calls=3,
    success_threshold=2
)
```
