"""
Performance Test Gates

Load test baselines for CI/CD. Fails CI on p95 degradation > 10%.

Usage:
    pytest benchmarks/test_performance_gates.py -v
    pytest benchmarks/test_performance_gates.py --benchmark-only

Environment Variables:
    PERFORMANCE_BASELINE_FILE: Path to baseline file (default: benchmarks/baselines.json)
    PERFORMANCE_P95_DEGRADATION_THRESHOLD: Allowed p95 degradation % (default: 10)
    API_BASE_URL: Base URL for testing (default: http://localhost:8000)
    PERFORMANCE_TEST_DURATION: Test duration in seconds (default: 30)
    PERFORMANCE_TEST_RPS: Target requests per second (default: 50)
"""

import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import pytest
import requests

# Configuration
BASELINE_FILE = os.getenv("PERFORMANCE_BASELINE_FILE", "benchmarks/baselines.json")
P95_DEGRADATION_THRESHOLD = float(os.getenv("PERFORMANCE_P95_DEGRADATION_THRESHOLD", "10"))
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_DURATION = int(os.getenv("PERFORMANCE_TEST_DURATION", "30"))
TARGET_RPS = int(os.getenv("PERFORMANCE_TEST_RPS", "50"))


@dataclass
class PerformanceMetrics:
    """Performance metrics for an endpoint."""

    endpoint: str
    requests: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    min_ms: float
    max_ms: float
    errors: int
    error_rate: float
    requests_per_second: float
    timestamp: str


@dataclass
class PerformanceBaseline:
    """Baseline metrics for comparison."""

    version: str
    created_at: str
    metrics: Dict[str, Dict[str, float]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceBaseline":
        return cls(
            version=data["version"],
            created_at=data["created_at"],
            metrics=data["metrics"],
        )


class LoadTester:
    """Simple load tester for API endpoints."""

    def __init__(self, base_url: str, target_rps: int = 50):
        self.base_url = base_url
        self.target_rps = target_rps
        self.session = requests.Session()

    def measure_endpoint(
        self, endpoint: str, method: str = "GET", payload: Optional[Dict] = None
    ) -> PerformanceMetrics:
        """Measure performance of an endpoint."""
        url = urljoin(self.base_url, endpoint)
        latencies: List[float] = []
        errors = 0
        requests_made = 0

        # Calculate delay between requests to hit target RPS
        delay = 1.0 / self.target_rps

        start_time = time.time()
        end_time = start_time + TEST_DURATION

        while time.time() < end_time:
            req_start = time.time()
            try:
                if method == "GET":
                    response = self.session.get(url, timeout=10)
                else:
                    response = self.session.post(url, json=payload, timeout=10)

                if response.status_code >= 400:
                    errors += 1
            except Exception:
                errors += 1

            latency_ms = (time.time() - req_start) * 1000
            latencies.append(latency_ms)
            requests_made += 1

            # Rate limiting
            time.sleep(max(0, delay - (time.time() - req_start)))

        total_time = time.time() - start_time
        rps = requests_made / total_time if total_time > 0 else 0

        if latencies:
            sorted_latencies = sorted(latencies)
            p50 = sorted_latencies[int(len(sorted_latencies) * 0.50)]
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
            mean = sum(latencies) / len(latencies)
            min_lat = min(latencies)
            max_lat = max(latencies)
        else:
            p50 = p95 = p99 = mean = min_lat = max_lat = 0

        error_rate = errors / requests_made if requests_made > 0 else 0

        return PerformanceMetrics(
            endpoint=endpoint,
            requests=requests_made,
            p50_ms=p50,
            p95_ms=p95,
            p99_ms=p99,
            mean_ms=mean,
            min_ms=min_lat,
            max_ms=max_lat,
            errors=errors,
            error_rate=error_rate,
            requests_per_second=rps,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )


def load_baseline() -> Optional[PerformanceBaseline]:
    """Load baseline from file."""
    if not os.path.exists(BASELINE_FILE):
        return None

    try:
        with open(BASELINE_FILE, "r") as f:
            data = json.load(f)
        return PerformanceBaseline.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def save_baseline(baseline: PerformanceBaseline) -> None:
    """Save baseline to file."""
    os.makedirs(os.path.dirname(BASELINE_FILE), exist_ok=True)
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline.to_dict(), f, indent=2)


def calculate_degradation_percent(current: float, baseline: float) -> float:
    """Calculate degradation percentage."""
    if baseline == 0:
        return float("inf") if current > 0 else 0
    return ((current - baseline) / baseline) * 100


@pytest.fixture
def load_tester() -> LoadTester:
    """Create a load tester instance."""
    return LoadTester(API_BASE_URL, TARGET_RPS)


@pytest.fixture
def baseline() -> Optional[PerformanceBaseline]:
    """Load the current baseline."""
    return load_baseline()


class TestPerformanceGates:
    """Performance test gates that fail CI on degradation."""

    @pytest.mark.performance
    def test_health_endpoint_performance(
        self, load_tester: LoadTester, baseline: Optional[PerformanceBaseline]
    ):
        """Test health endpoint meets performance requirements."""
        metrics = load_tester.measure_endpoint("/v1/health")

        # Assert basic requirements
        assert metrics.requests > 0, "No requests were made"
        assert metrics.error_rate < 0.01, f"Error rate too high: {metrics.error_rate:.2%}"

        # Check against baseline if available
        if baseline and "/v1/health" in baseline.metrics:
            baseline_p95 = baseline.metrics["/v1/health"]["p95_ms"]
            degradation = calculate_degradation_percent(metrics.p95_ms, baseline_p95)

            assert degradation <= P95_DEGRADATION_THRESHOLD, (
                f"P95 degradation exceeded threshold: {degradation:.1f}% "
                f"(current: {metrics.p95_ms:.1f}ms, baseline: {baseline_p95:.1f}ms)"
            )

    @pytest.mark.performance
    def test_version_endpoint_performance(
        self, load_tester: LoadTester, baseline: Optional[PerformanceBaseline]
    ):
        """Test version endpoint meets performance requirements."""
        metrics = load_tester.measure_endpoint("/v1/version")

        assert metrics.requests > 0, "No requests were made"
        assert metrics.error_rate < 0.01, f"Error rate too high: {metrics.error_rate:.2%}"

        if baseline and "/v1/version" in baseline.metrics:
            baseline_p95 = baseline.metrics["/v1/version"]["p95_ms"]
            degradation = calculate_degradation_percent(metrics.p95_ms, baseline_p95)

            assert degradation <= P95_DEGRADATION_THRESHOLD, (
                f"P95 degradation exceeded threshold: {degradation:.1f}% "
                f"(current: {metrics.p95_ms:.1f}ms, baseline: {baseline_p95:.1f}ms)"
            )

    @pytest.mark.performance
    def test_metrics_endpoint_performance(
        self, load_tester: LoadTester, baseline: Optional[PerformanceBaseline]
    ):
        """Test metrics endpoint meets performance requirements."""
        metrics = load_tester.measure_endpoint("/v1/metrics")

        assert metrics.requests > 0, "No requests were made"
        assert metrics.error_rate < 0.01, f"Error rate too high: {metrics.error_rate:.2%}"

        if baseline and "/v1/metrics" in baseline.metrics:
            baseline_p95 = baseline.metrics["/v1/metrics"]["p95_ms"]
            degradation = calculate_degradation_percent(metrics.p95_ms, baseline_p95)

            assert degradation <= P95_DEGRADATION_THRESHOLD, (
                f"P95 degradation exceeded threshold: {degradation:.1f}% "
                f"(current: {metrics.p95_ms:.1f}ms, baseline: {baseline_p95:.1f}ms)"
            )

    @pytest.mark.baseline
    def test_create_performance_baseline(self, load_tester: LoadTester):
        """Create a new performance baseline. Run this to establish baselines."""
        endpoints = ["/v1/health", "/v1/version", "/v1/metrics"]

        metrics_data: Dict[str, Dict[str, float]] = {}
        for endpoint in endpoints:
            metrics = load_tester.measure_endpoint(endpoint)
            metrics_data[endpoint] = {
                "p50_ms": metrics.p50_ms,
                "p95_ms": metrics.p95_ms,
                "p99_ms": metrics.p99_ms,
                "mean_ms": metrics.mean_ms,
                "requests_per_second": metrics.requests_per_second,
                "error_rate": metrics.error_rate,
            }
            print(f"\n{endpoint}:")
            print(f"  P50: {metrics.p50_ms:.1f}ms")
            print(f"  P95: {metrics.p95_ms:.1f}ms")
            print(f"  P99: {metrics.p99_ms:.1f}ms")
            print(f"  RPS: {metrics.requests_per_second:.1f}")

        baseline = PerformanceBaseline(
            version="1.0.0",
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            metrics=metrics_data,
        )

        save_baseline(baseline)
        print(f"\nBaseline saved to {BASELINE_FILE}")


if __name__ == "__main__":
    # Run baseline creation directly
    tester = LoadTester(API_BASE_URL, TARGET_RPS)

    endpoints = ["/v1/health", "/v1/version", "/v1/metrics"]

    metrics_data: Dict[str, Dict[str, float]] = {}
    for endpoint in endpoints:
        metrics = tester.measure_endpoint(endpoint)
        metrics_data[endpoint] = {
            "p50_ms": metrics.p50_ms,
            "p95_ms": metrics.p95_ms,
            "p99_ms": metrics.p99_ms,
            "mean_ms": metrics.mean_ms,
            "requests_per_second": metrics.requests_per_second,
            "error_rate": metrics.error_rate,
        }
        print(f"\n{endpoint}:")
        print(f"  Requests: {metrics.requests}")
        print(f"  P50: {metrics.p50_ms:.1f}ms")
        print(f"  P95: {metrics.p95_ms:.1f}ms")
        print(f"  P99: {metrics.p99_ms:.1f}ms")
        print(f"  Mean: {metrics.mean_ms:.1f}ms")
        print(f"  Min: {metrics.min_ms:.1f}ms")
        print(f"  Max: {metrics.max_ms:.1f}ms")
        print(f"  Errors: {metrics.errors} ({metrics.error_rate:.2%})")
        print(f"  RPS: {metrics.requests_per_second:.1f}")

    perf_baseline = PerformanceBaseline(
        version="1.0.0",
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        metrics=metrics_data,
    )

    save_baseline(perf_baseline)
    print(f"\nBaseline saved to {BASELINE_FILE}")
