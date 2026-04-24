#!/usr/bin/env python3
"""
Example: Data Loader Utility

Demonstrates how to load, inspect, and preprocess data using the
APGI Framework's data loading utilities.

Usage:
    python examples/data_loader.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def demo_load_csv():
    """Load a CSV file and print basic statistics."""
    import csv

    sample_files = list(PROJECT_ROOT.glob("*.csv"))
    if not sample_files:
        print("  No .csv files found in project root. Creating a sample...")
        sample = PROJECT_ROOT / "sample_data.csv"
        with open(sample, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "signal", "label"])
            for i in range(20):
                writer.writerow([i * 0.1, float(i) * 0.5 + (i % 3), i % 2])
        sample_files = [sample]

    csv_file = sample_files[0]
    print(f"  Loading: {csv_file.name}")
    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"  Rows loaded: {len(rows)}")
    if rows:
        print(f"  Columns: {list(rows[0].keys())}")
        print(f"  First row: {rows[0]}")
    return rows


def demo_load_numpy():
    """Load a NumPy .npy file if available."""
    try:
        import numpy as np
    except ImportError:
        print("  NumPy not installed, skipping .npy demo.")
        return

    npy_files = list(PROJECT_ROOT.glob("*.npy"))
    if not npy_files:
        print("  No .npy files found. Creating a sample array...")
        arr = np.random.randn(10, 4)
        path = PROJECT_ROOT / "sample_array.npy"
        np.save(path, arr)
        npy_files = [path]

    path = npy_files[0]
    arr = np.load(path)
    print(f"  Loaded: {path.name}  shape={arr.shape}  dtype={arr.dtype}")
    print(f"  mean={arr.mean():.4f}  std={arr.std():.4f}")


def main():
    print("=" * 60)
    print("APGI Framework — Data Loader Example")
    print("=" * 60)

    print("\n[1] CSV Loader Demo")
    demo_load_csv()

    print("\n[2] NumPy Loader Demo")
    demo_load_numpy()

    print("\nData loader example complete.")


if __name__ == "__main__":
    main()
