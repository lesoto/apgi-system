#!/usr/bin/env python3
"""
Example 02: Batch Processing Configurations

Demonstrates how to configure and run multiple APGI experiments in batch mode,
testing different parameter combinations systematically.

Usage:
    python examples/02_batch_processing_configurations.py
"""

import itertools
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# Parameter grid for batch experiments
PARAM_GRID = {
    "noise_level": [0.05, 0.1, 0.2],
    "signal_frequency": [0.5, 1.0, 2.0],
    "n_samples": [200, 500],
}


def run_single_configuration(params: dict) -> dict:
    """Run one experiment configuration and return results."""
    noise = params["noise_level"]
    freq = params["signal_frequency"]
    n = params["n_samples"]

    try:
        import math

        signal = [
            math.sin(2 * math.pi * freq * i / n) + noise * ((i % 7) / 7.0 - 0.5) for i in range(n)
        ]
    except Exception:
        signal = [0.0] * n

    # Compute basic metrics
    mean_val = sum(signal) / len(signal)
    variance = sum((x - mean_val) ** 2 for x in signal) / len(signal)
    amplitude = max(signal) - min(signal)

    return {
        "params": params,
        "mean": round(mean_val, 6),
        "variance": round(variance, 6),
        "amplitude": round(amplitude, 6),
        "status": "ok",
    }


def batch_run(param_grid: dict) -> list:
    """Generate all parameter combinations and run each."""
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    combinations = list(itertools.product(*values))
    total = len(combinations)

    print(f"  Total configurations: {total}")
    print(f"  Parameters: {', '.join(keys)}")

    results = []
    for i, combo in enumerate(combinations, 1):
        params = dict(zip(keys, combo))
        result = run_single_configuration(params)
        results.append(result)
        pct = int(i / total * 40)
        bar = "█" * pct + "░" * (40 - pct)
        print(f"\r  [{bar}] {i}/{total}", end="", flush=True)

    print()  # newline after progress bar
    return results


def print_batch_report(results: list):
    print(f"\n  {'noise':>8} {'freq':>6} {'n':>6} {'amplitude':>12} {'variance':>12}")
    print("  " + "-" * 50)
    for r in results:
        p = r["params"]
        print(
            f"  {p['noise_level']:>8.2f} {p['signal_frequency']:>6.1f}"
            f" {p['n_samples']:>6} {r['amplitude']:>12.6f} {r['variance']:>12.6f}"
        )


def main():
    print("=" * 60)
    print("APGI — Batch Processing Configurations (Example 02)")
    print("=" * 60)

    print("\nRunning batch experiments...")
    start = time.time()
    results = batch_run(PARAM_GRID)
    elapsed = time.time() - start

    print("\nBatch Results Summary:")
    print_batch_report(results)

    amplitudes = [r["amplitude"] for r in results]
    best_idx = amplitudes.index(max(amplitudes))
    print("\n  Best configuration (highest amplitude):")
    print(f"    {results[best_idx]['params']}")
    print(f"    amplitude = {results[best_idx]['amplitude']:.6f}")

    print(f"\n  Completed {len(results)} configurations in {elapsed:.3f}s")
    print("\nBatch processing example complete.")


if __name__ == "__main__":
    main()
