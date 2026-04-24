"""
Configuration for pytest-benchmark
"""

import pytest


def pytest_configure(config):
    """Configure pytest-benchmark settings."""
    config.addinivalue_line("markers", "benchmark: mark test as a benchmark")


@pytest.fixture
def benchmark_data():
    """Provide benchmark test data."""
    import numpy as np
    import pandas as pd

    return {
        "small_array": np.random.rand(1000, 10),
        "medium_array": np.random.rand(10000, 10),
        "large_array": np.random.rand(100000, 10),
        "small_dataframe": pd.DataFrame(np.random.rand(1000, 10)),
        "medium_dataframe": pd.DataFrame(np.random.rand(10000, 10)),
        "large_dataframe": pd.DataFrame(np.random.rand(100000, 10)),
    }
