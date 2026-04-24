#!/usr/bin/env python3
"""
Example 04: Extending Falsification Criteria

Demonstrates how to define and register custom falsification criteria
beyond the built-in APGI tests.

Usage:
    python examples/04_extending_falsification_criteria.py
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ── Custom criterion interface ────────────────────────────────────────────── #


class FalsificationCriterion:
    """Base class for all falsification criteria."""

    name: str = "unnamed"
    description: str = ""

    def evaluate(self, signal: list, params: dict) -> dict:
        """
        Evaluate the criterion against a signal.

        Returns:
            dict with keys: passed (bool), score (float 0-1), detail (str)
        """
        raise NotImplementedError


class VarianceRatioCriterion(FalsificationCriterion):
    """Built-in: checks that signal variance is stable across halves."""

    name = "variance_ratio"
    description = "Signal variance must be stable across temporal halves."

    def evaluate(self, signal, params):
        half = len(signal) // 2

        def var(s):
            m = sum(s) / len(s)
            return sum((x - m) ** 2 for x in s) / len(s)

        r = var(signal[:half]) / (var(signal[half:]) + 1e-12)
        passed = 0.5 <= r <= 2.0
        return {
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "detail": f"ratio={r:.4f}",
        }


class FrequencyConsistencyCriterion(FalsificationCriterion):
    """Custom: checks zero-crossing rate matches expected frequency."""

    name = "frequency_consistency"
    description = "Zero-crossing rate must match expected signal frequency."

    def evaluate(self, signal, params):
        n = len(signal)
        # Smooth with a moving average (window ~2% of length) to suppress
        # noise-induced false zero crossings before counting.
        win = max(3, n // 50)
        smoothed = [
            sum(signal[max(0, i - win // 2) : min(n, i + win // 2 + 1)])
            / len(signal[max(0, i - win // 2) : min(n, i + win // 2 + 1)])
            for i in range(n)
        ]
        crossings = sum(1 for i in range(1, n) if smoothed[i - 1] * smoothed[i] < 0)
        observed_hz = crossings / (2 * n)
        expected_hz = params.get("frequency", 1.0) / n
        # Allow ratio in [0.25, 4.0] with a log-space score.
        import math

        ratio = observed_hz / (expected_hz + 1e-12)
        log_ratio = abs(math.log(max(ratio, 1e-9)))
        score = max(0.0, 1.0 - log_ratio / math.log(4))
        passed = score >= 0.25
        return {
            "passed": passed,
            "score": round(score, 4),
            "detail": f"observed={observed_hz:.6f} expected={expected_hz:.6f} ratio={ratio:.2f}",
        }


class AmplitudeThresholdCriterion(FalsificationCriterion):
    """Custom: checks that signal amplitude exceeds a minimum threshold."""

    name = "amplitude_threshold"
    description = "Peak-to-peak amplitude must exceed minimum threshold."

    def __init__(self, min_amplitude=0.5):
        self.min_amplitude = min_amplitude

    def evaluate(self, signal, params):
        amp = max(signal) - min(signal)
        passed = amp >= self.min_amplitude
        score = min(1.0, amp / self.min_amplitude)
        return {
            "passed": passed,
            "score": round(score, 4),
            "detail": f"amplitude={amp:.4f} threshold={self.min_amplitude}",
        }


class SNRCriterion(FalsificationCriterion):
    """Custom: SNR estimate using first-difference noise floor."""

    name = "snr_check"
    description = "Estimated SNR must exceed 10 dB."

    def evaluate(self, signal, params):
        import math

        n = len(signal)
        mean = sum(signal) / n
        # Signal power = variance of the full waveform (correct for zero-mean sinusoids).
        signal_power = sum((x - mean) ** 2 for x in signal) / n
        # Noise power via first differences: E[(x_i - x_{i-1})^2] = 2*sigma_noise^2
        # Subtract the sinusoidal slope contribution: (2*pi*freq/n)^2 / 2.
        freq = params.get("frequency", 1.0)
        diff_power = sum((signal[i] - signal[i - 1]) ** 2 for i in range(1, n)) / (n - 1)
        sin_slope_power = (2 * math.pi * freq / n) ** 2 / 2
        noise_power = max((diff_power - sin_slope_power) / 2, 1e-12)
        snr_db = 10 * math.log10(signal_power / noise_power)
        passed = snr_db >= 10.0
        return {
            "passed": passed,
            "score": min(1.0, max(0.0, snr_db / 30.0)),
            "detail": f"SNR={snr_db:.2f} dB",
        }


# ── Registry ──────────────────────────────────────────────────────────────── #


class CriteriaRegistry:
    def __init__(self) -> None:
        self._criteria: list[FalsificationCriterion] = []

    def register(self, criterion: FalsificationCriterion) -> None:
        self._criteria.append(criterion)
        print(f"  Registered: '{criterion.name}' — {criterion.description}")

    def run_all(self, signal: list, params: dict) -> list[dict]:
        return [{"criterion": c.name, **c.evaluate(signal, params)} for c in self._criteria]


# ── Demo ──────────────────────────────────────────────────────────────────── #


def generate_signal(n=400, freq=1.0, noise=0.1):
    import math

    return [
        math.sin(2 * math.pi * freq * i / n) + noise * ((i * 17 % 11) / 11.0 - 0.5)
        for i in range(n)
    ]


def main():
    print("=" * 60)
    print("APGI — Extending Falsification Criteria (Example 04)")
    print("=" * 60)

    # Build registry with built-in + custom criteria
    print("\nRegistering criteria:")
    registry = CriteriaRegistry()
    registry.register(VarianceRatioCriterion())
    registry.register(FrequencyConsistencyCriterion())
    registry.register(AmplitudeThresholdCriterion(min_amplitude=0.8))
    registry.register(SNRCriterion())

    params = {"frequency": 1.0, "noise": 0.1}
    signal = generate_signal(freq=params["frequency"], noise=params["noise"])
    print(
        f"\nGenerated signal: {len(signal)} samples  freq={params['frequency']}Hz  noise={params['noise']}"
    )

    print("\nRunning criteria battery:")
    t0 = time.time()
    results = registry.run_all(signal, params)
    elapsed = time.time() - t0

    print(f"\n  {'Criterion':<28} {'Status':<8} {'Score':>6}  {'Detail'}")
    print("  " + "-" * 70)
    for r in results:
        status = "PASS ✓" if r["passed"] else "FAIL ✗"
        print(f"  {r['criterion']:<28} {status:<8} {r['score']:>6.3f}  {r['detail']}")

    passed = sum(1 for r in results if r["passed"])
    print(f"\n  {passed}/{len(results)} criteria passed in {elapsed:.4f}s")
    print("\nFalsification extension example complete.")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
