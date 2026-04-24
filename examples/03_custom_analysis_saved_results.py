#!/usr/bin/env python3
"""
Example 03: Custom Analysis of Saved Results

Demonstrates how to load previously saved experiment results and
run custom statistical analyses using the APGI Framework.

Usage:
    python examples/03_custom_analysis_saved_results.py
"""

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = PROJECT_ROOT / "apgi_outputs"


def load_results(results_dir: Path) -> list:
    records = []
    json_files = sorted(results_dir.glob("*.json")) if results_dir.exists() else []
    if not json_files:
        print(f"  No saved results in {results_dir}. Using synthetic demo data.")
        records = _generate_synthetic_results()
    else:
        for jf in json_files[:20]:
            try:
                with open(jf) as f:
                    records.append(json.load(f))
            except Exception as e:
                print(f"  [WARN] {jf.name}: {e}")
    print(f"  Records loaded: {len(records)}")
    return records


def _generate_synthetic_results() -> list:
    import math

    return [
        {
            "id": f"run_{i:03d}",
            "params": {
                "frequency": 0.5 + (i % 5) * 0.4,
                "noise": 0.05 + (i % 3) * 0.05,
            },
            "metrics": {
                "amplitude": 1.8 + math.sin(0.5 + (i % 5) * 0.4) * 0.3,
                "variance": 0.3 + (i % 4) * 0.05,
                "falsification_score": 0.6 + (i % 6) * 0.06,
            },
            "status": "complete",
        }
        for i in range(15)
    ]


def compute_statistics(records: list, key: str) -> dict:
    vals = [r["metrics"][key] for r in records if key in r.get("metrics", {})]
    if not vals:
        return {}
    n = len(vals)
    mean = sum(vals) / n
    std = (sum((x - mean) ** 2 for x in vals) / n) ** 0.5
    sv = sorted(vals)
    median = sv[n // 2] if n % 2 else (sv[n // 2 - 1] + sv[n // 2]) / 2
    return {
        "n": n,
        "mean": round(mean, 6),
        "std": round(std, 6),
        "median": round(median, 6),
        "min": round(min(vals), 6),
        "max": round(max(vals), 6),
    }


def main():
    print("=" * 60)
    print("APGI — Custom Analysis of Saved Results (Example 03)")
    print("=" * 60)
    print(f"\nLoading results from: {RESULTS_DIR}")
    t0 = time.time()
    records = load_results(RESULTS_DIR)

    print(f"\n  {'Metric':<28} {'N':>4} {'Mean':>10} {'Std':>10} {'Min':>10} {'Max':>10}")
    print("  " + "-" * 75)
    for metric in ["amplitude", "variance", "falsification_score"]:
        s = compute_statistics(records, metric)
        if s:
            print(
                f"  {metric:<28} {s['n']:>4} {s['mean']:>10.4f} {s['std']:>10.4f}"
                f" {s['min']:>10.4f} {s['max']:>10.4f}"
            )

    best = max(records, key=lambda r: r["metrics"].get("falsification_score", 0))
    print(f"\n  Best run: {best['id']}  score={best['metrics']['falsification_score']:.4f}")
    print(f"\n  Done in {time.time() - t0:.4f}s")


if __name__ == "__main__":
    main()
