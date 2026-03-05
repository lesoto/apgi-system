"""
Circuit Breaker Pattern Implementation

This module provides comprehensive circuit breaker functionality for the APGI system,
implementing fault tolerance and resilience patterns across all services and components.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, overload, ParamSpec, TypeVar
import logging
import functools
import threading

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: float = 60.0  # Seconds before attempting recovery
    success_threshold: int = 3  # Successes needed in half-open state
    timeout: float = 10.0  # Request timeout in seconds
    name: str = "default"  # Circuit breaker name
    monitor_failures: bool = True  # Whether to monitor failures
    exponential_backoff: bool = True  # Use exponential backoff
    max_backoff_time: float = 300.0  # Maximum backoff time
    failure_window: float = 60.0  # Time window for failure counting


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker performance."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    state_changes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    created_at: float = field(default_factory=time.time)


class CircuitBreakerException(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class CircuitBreakerOpenException(CircuitBreakerException):
    """Exception raised when circuit breaker is open and rejecting requests."""

    pass


class CircuitBreakerTimeoutException(CircuitBreakerException):
    """Exception raised when request times out."""

    pass


class CircuitBreaker:
    """
    Circuit Breaker implementation with comprehensive monitoring and recovery.

    The circuit breaker prevents cascading failures by temporarily stopping
    requests to failing services, allowing them time to recover.
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._lock = threading.RLock()
        self._failure_times: List[float] = []
        self._last_attempt_time: Optional[float] = None

        logger.info(
            "Circuit breaker initialized",
            extra={
                "circuit_name": config.name,
                "failure_threshold": config.failure_threshold,
                "recovery_timeout": config.recovery_timeout,
            },
        )

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenException: If circuit breaker is open
            CircuitBreakerTimeoutException: If request times out
            Exception: Original function exception
        """
        with self._lock:
            if not self._can_attempt_request():
                self.metrics.rejected_requests += 1
                logger.warning(
                    "Request rejected by circuit breaker",
                    extra={
                        "circuit_name": self.config.name,
                        "state": self.state.value,
                    },
                )
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.config.name}' is {self.state.value}"
                )

            self.metrics.total_requests += 1

            try:
                # Execute with timeout
                result = self._execute_with_timeout(func, *args, **kwargs)
                self._on_success()
                return result

            except Exception as e:
                self._on_failure(e)
                raise

    async def call_async(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute async function through circuit breaker.

        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenException: If circuit breaker is open
            CircuitBreakerTimeoutException: If request times out
            Exception: Original function exception
        """
        with self._lock:
            if not self._can_attempt_request():
                self.metrics.rejected_requests += 1
                logger.warning(
                    "Async request rejected by circuit breaker",
                    extra={
                        "circuit_name": self.config.name,
                        "state": self.state.value,
                    },
                )
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.config.name}' is {self.state.value}"
                )

            self.metrics.total_requests += 1

            try:
                # Execute with timeout
                result = await self._execute_async_with_timeout(func, *args, **kwargs)
                self._on_success()
                return result

            except Exception as e:
                self._on_failure(e)
                raise

    def _can_attempt_request(self) -> bool:
        """Check if request can be attempted."""
        now = time.time()

        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if self._last_attempt_time is None:
                return True

            time_since_last_attempt = now - self._last_attempt_time
            if time_since_last_attempt >= self.config.recovery_timeout:
                self._transition_to_half_open()
                return True

            return False

        if self.state == CircuitBreakerState.HALF_OPEN:
            return True

        return False  # type: ignore[unreachable]

    def _execute_with_timeout(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute function with timeout."""
        import signal

        def timeout_handler(signum: int, frame: Any) -> None:
            raise CircuitBreakerTimeoutException(
                f"Request timed out after {self.config.timeout} seconds"
            )

        # Set up timeout handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(self.config.timeout))

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Restore original handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    async def _execute_async_with_timeout(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute async function with timeout."""
        try:
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
            return result
        except asyncio.TimeoutError:
            raise CircuitBreakerTimeoutException(
                f"Async request timed out after {self.config.timeout} seconds"
            )

    def _on_success(self) -> None:
        """Handle successful request."""
        self.metrics.successful_requests += 1
        self.metrics.consecutive_successes += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.metrics.consecutive_successes >= self.config.success_threshold:
                self._transition_to_closed()

    def _on_failure(self, exception: Exception) -> None:
        """Handle failed request."""
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        self.metrics.last_failure_time = time.time()
        self._last_attempt_time = time.time()

        # Record failure time for window-based counting
        self._failure_times.append(time.time())

        # Clean old failure times outside the window
        cutoff_time = time.time() - self.config.failure_window
        self._failure_times = [t for t in self._failure_times if t > cutoff_time]

        # Check if we should open the circuit
        if self.state == CircuitBreakerState.CLOSED:
            if len(self._failure_times) >= self.config.failure_threshold:
                self._transition_to_open()

        elif self.state == CircuitBreakerState.HALF_OPEN:
            self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition to open state."""
        old_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.metrics.state_changes += 1
        self._last_attempt_time = time.time()

        logger.warning(
            "Circuit breaker opened",
            extra={
                "circuit_name": self.config.name,
                "old_state": old_state.value,
                "new_state": self.state.value,
                "failure_count": len(self._failure_times),
            },
        )

    def _transition_to_half_open(self) -> None:
        """Transition to half-open state."""
        old_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.metrics.state_changes += 1

        logger.info(
            "Circuit breaker attempting recovery",
            extra={
                "circuit_name": self.config.name,
                "old_state": old_state.value,
                "new_state": self.state.value,
            },
        )

    def _transition_to_closed(self) -> None:
        """Transition to closed state."""
        old_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.metrics.state_changes += 1
        self.metrics.consecutive_successes = 0
        self.metrics.consecutive_failures = 0
        self._failure_times.clear()

        logger.info(
            "Circuit breaker closed - service recovered",
            extra={
                "circuit_name": self.config.name,
                "old_state": old_state.value,
                "new_state": self.state.value,
            },
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        return {
            "name": self.config.name,
            "state": self.state.value,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "rejected_requests": self.metrics.rejected_requests,
            "state_changes": self.metrics.state_changes,
            "last_failure_time": self.metrics.last_failure_time,
            "last_success_time": self.metrics.last_success_time,
            "consecutive_successes": self.metrics.consecutive_successes,
            "consecutive_failures": self.metrics.consecutive_failures,
            "failure_rate": (
                self.metrics.failed_requests / self.metrics.total_requests
                if self.metrics.total_requests > 0
                else 0
            ),
            "uptime_percentage": self._calculate_uptime_percentage(),
            "created_at": self.metrics.created_at,
        }

    def _calculate_uptime_percentage(self) -> float:
        """Calculate uptime percentage."""
        total_time = time.time() - self.metrics.created_at
        if total_time == 0:
            return 100.0

        # Assume downtime only when circuit breaker is open
        downtime = 0.0
        if self.state == CircuitBreakerState.OPEN and self._last_attempt_time:
            downtime = time.time() - self._last_attempt_time

        uptime = total_time - downtime
        return (uptime / total_time) * 100.0

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.metrics = CircuitBreakerMetrics()
            self._failure_times.clear()
            self._last_attempt_time = None

            logger.info("Circuit breaker reset", extra={"circuit_name": self.config.name})

    def force_open(self) -> None:
        """Force circuit breaker to open state."""
        with self._lock:
            old_state = self.state
            self.state = CircuitBreakerState.OPEN
            self.metrics.state_changes += 1
            self._last_attempt_time = time.time()

            logger.warning(
                "Circuit breaker force opened",
                extra={"circuit_name": self.config.name, "old_state": old_state.value},
            )

    def force_close(self) -> None:
        """Force circuit breaker to closed state."""
        with self._lock:
            old_state = self.state
            self.state = CircuitBreakerState.CLOSED
            self.metrics.state_changes += 1
            self.metrics.consecutive_successes = 0
            self.metrics.consecutive_failures = 0
            self._failure_times.clear()

            logger.warning(
                "Circuit breaker force closed",
                extra={"circuit_name": self.config.name, "old_state": old_state.value},
            )


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.

    Provides centralized management and monitoring of circuit breakers
    across the application.
    """

    def __init__(self) -> None:
        self.breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()

    def register(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """
        Register a new circuit breaker.

        Args:
            name: Unique name for the circuit breaker
            config: Circuit breaker configuration

        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if name in self.breakers:
                logger.warning(
                    "Circuit breaker already exists, replacing", extra={"circuit_name": name}
                )

            breaker = CircuitBreaker(config)
            self.breakers[name] = breaker

            logger.info(
                "Circuit breaker registered",
                extra={"circuit_name": name, "total_breakers": len(self.breakers)},
            )

            return breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """
        Get circuit breaker by name.

        Args:
            name: Circuit breaker name

        Returns:
            CircuitBreaker instance or None if not found
        """
        return self.breakers.get(name)

    def get_all(self) -> Dict[str, CircuitBreaker]:
        """Get all registered circuit breakers."""
        with self._lock:
            return self.breakers.copy()

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers."""
        with self._lock:
            return {name: breaker.get_metrics() for name, breaker in self.breakers.items()}

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for name, breaker in self.breakers.items():
                breaker.reset()

            logger.info("All circuit breakers reset", extra={"count": len(self.breakers)})

    def remove(self, name: str) -> bool:
        """
        Remove circuit breaker.

        Args:
            name: Circuit breaker name

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if name in self.breakers:
                del self.breakers[name]
                logger.info(
                    "Circuit breaker removed",
                    extra={"circuit_name": name, "remaining_breakers": len(self.breakers)},
                )
                return True

            return False


# Global registry instance
circuit_breaker_registry = CircuitBreakerRegistry()


@overload
def circuit_breaker(  # noqa: E704
    func: Callable[P, R],
    *,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 3,
    timeout: float = 10.0,
    monitor_failures: bool = True,
) -> Callable[P, R]:
    ...


@overload
def circuit_breaker(  # noqa: E704
    *,
    name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 3,
    timeout: float = 10.0,
    monitor_failures: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    ...


def circuit_breaker(
    func: Optional[Any] = None,
    *,
    name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 3,
    timeout: float = 10.0,
    monitor_failures: bool = True,
) -> Any:
    """
    Decorator to apply circuit breaker pattern to functions.

    Args:
        func: Function to decorate (if used as @circuit_breaker)
        name: Circuit breaker name (defaults to function name)
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before attempting recovery
        success_threshold: Successes needed in half-open state
        timeout: Request timeout in seconds
        monitor_failures: Whether to monitor failures

    Returns:
        Decorated function or decorator function
    """
    if func is not None:
        # Used as @circuit_breaker (without parameters)
        breaker_name = name or f"{func.__module__}.{func.__qualname__}"

        config = CircuitBreakerConfig(
            name=breaker_name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            timeout=timeout,
            monitor_failures=monitor_failures,
        )

        breaker = circuit_breaker_registry.register(breaker_name, config)

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await breaker.call_async(func, *args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return breaker.call(func, *args, **kwargs)

            return sync_wrapper

    else:
        # Used as @circuit_breaker(...) (with parameters)
        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            breaker_name = name or f"{func.__module__}.{func.__qualname__}"

            config = CircuitBreakerConfig(
                name=breaker_name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
                timeout=timeout,
                monitor_failures=monitor_failures,
            )

            breaker = circuit_breaker_registry.register(breaker_name, config)

            if asyncio.iscoroutinefunction(func):

                @functools.wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    return await breaker.call_async(func, *args, **kwargs)

                return async_wrapper  # type: ignore
            else:

                @functools.wraps(func)
                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    return breaker.call(func, *args, **kwargs)

                return sync_wrapper

        return decorator


# Pre-configured circuit breakers for common services
class ServiceCircuitBreakers:
    """Pre-configured circuit breakers for common APGI services."""

    # Database circuit breaker - more tolerant of failures
    DATABASE_BREAKER = CircuitBreakerConfig(
        name="database",
        failure_threshold=3,
        recovery_timeout=30.0,
        success_threshold=2,
        timeout=5.0,
    )

    # External API circuit breaker - quick to fail, slow to recover
    EXTERNAL_API_BREAKER = CircuitBreakerConfig(
        name="external_api",
        failure_threshold=2,
        recovery_timeout=120.0,
        success_threshold=3,
        timeout=15.0,
    )

    # File system operations - fast failure detection
    FILESYSTEM_BREAKER = CircuitBreakerConfig(
        name="filesystem",
        failure_threshold=5,
        recovery_timeout=10.0,
        success_threshold=1,
        timeout=2.0,
    )

    # Network operations - moderate tolerance
    NETWORK_BREAKER = CircuitBreakerConfig(
        name="network", failure_threshold=3, recovery_timeout=60.0, success_threshold=2, timeout=8.0
    )

    # GPU/ML operations - resource intensive
    GPU_BREAKER = CircuitBreakerConfig(
        name="gpu_operations",
        failure_threshold=2,
        recovery_timeout=300.0,  # 5 minutes
        success_threshold=5,
        timeout=30.0,
    )

    # Simulation engine - critical service
    SIMULATION_BREAKER = CircuitBreakerConfig(
        name="simulation_engine",
        failure_threshold=1,
        recovery_timeout=180.0,  # 3 minutes
        success_threshold=3,
        timeout=20.0,
    )


# Initialize default circuit breakers
def initialize_default_circuit_breakers() -> None:
    """Initialize default circuit breakers for common services."""
    defaults = [
        ServiceCircuitBreakers.DATABASE_BREAKER,
        ServiceCircuitBreakers.EXTERNAL_API_BREAKER,
        ServiceCircuitBreakers.FILESYSTEM_BREAKER,
        ServiceCircuitBreakers.NETWORK_BREAKER,
        ServiceCircuitBreakers.GPU_BREAKER,
        ServiceCircuitBreakers.SIMULATION_BREAKER,
    ]

    for config in defaults:
        circuit_breaker_registry.register(config.name, config)

    logger.info("Default circuit breakers initialized", extra={"count": len(defaults)})


# Initialize on module import
initialize_default_circuit_breakers()
