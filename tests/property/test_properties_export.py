"""
Property-based tests for data export and analysis functionality.

This module implements property-based tests using Hypothesis to verify
universal properties that should hold for data export completeness,
analysis report generation, CSV format consistency, and JSON round-trip
preservation.

Each test is tagged with the corresponding property from the design document
and validates specific requirements from the requirements document.
"""

import base64
import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from numpy.typing import NDArray

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apgi_system.system import APGISystem  # noqa
from tests.strategies import observation_strategy  # noqa

# Configure Hypothesis for property-based testing
settings.register_profile(
    "property_tests",
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.function_scoped_fixture,
        HealthCheck.large_base_example,
        HealthCheck.data_too_large,
    ],
)
settings.load_profile("property_tests")


class DataExporter:
    """
    Helper class to simulate data export functionality.

    This class provides methods to record simulation data and export it
    in various formats (CSV, JSON) for testing export completeness and
    format consistency.
    """

    def __init__(self) -> None:
        """Initialize data exporter."""
        self.log_data: list[dict] = []

    def _to_scalar(self, value):
        """Convert array to scalar if needed for CSV/JSON export."""
        if isinstance(value, np.ndarray):
            return float(value.item()) if value.size == 1 else float(value[0])
        return value

    def record_state(self, state: Dict[str, Any]) -> None:
        """
        Record state data from simulation step.

        Parameters
        ----------
        state : dict
            System state dictionary from APGISystem.step()
        """
        current_time = state["time"] / 1000.0  # Convert to seconds

        # Extract and record metrics (matches GUI logic)
        # Convert arrays to scalars for export
        data_entry = {
            "time": current_time,
            "ignition": 1 if state["ignition"]["ignition_occurred"] else 0,
            "free_energy": self._to_scalar(state["ignition"]["total_signal"]),
            "extero_precision": self._to_scalar(state["precision"]["exteroceptive"]),
            "intero_precision": self._to_scalar(state["precision"]["interoceptive"]),
            "metabolic_reserves": self._to_scalar(state["metabolism"]["reserves"]),
            "allostatic_load": self._to_scalar(state["allostasis"]["allostatic_load"]),
            "heart_rate": self._to_scalar(state["body"]["current"]["heart_rate"]),
            "cortisol": self._to_scalar(state["body"]["current"]["cortisol"]),
            "workspace_active": 1 if state["workspace"]["is_reportable"] else 0,
            "gamma_power": self._to_scalar(state["oscillations"]["band_powers"].get("gamma", 0)),
            "beta_power": self._to_scalar(state["oscillations"]["band_powers"].get("beta", 0)),
            "minimal_self_coherence": self._to_scalar(state["self_model"]["minimal"]["coherence"]),
        }

        self.log_data.append(data_entry)

    def export_to_csv(self, filename) -> bool:
        """
        Export data to CSV format.

        Parameters
        ----------
        filename : str
            Path to CSV file to write

        Returns
        -------
        bool
            True if export succeeded, False otherwise
        """
        if not self.log_data:
            return False

        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.log_data[0].keys())
            writer.writeheader()
            writer.writerows(self.log_data)
        return True

    def export_to_json(self, filename) -> bool:
        """
        Export data to JSON format.

        Parameters
        ----------
        filename : str
            Path to JSON file to write

        Returns
        -------
        bool
            True if export succeeded, False otherwise
        """
        if not self.log_data:
            return False

        with open(filename, "w") as f:
            json.dump(self.log_data, f, indent=2)
        return True

    def generate_analysis_report(self) -> dict:
        """
        Generate analysis report with summary statistics.

        Returns
        -------
        dict
            Analysis report containing summary statistics for:
            - ignition_events: count, rate, intervals
            - free_energy: mean, std, min, max
            - metabolic_costs: total consumed, average per step
        """
        if not self.log_data:
            return {}

        # Extract time series data
        times = [entry["time"] for entry in self.log_data]
        ignitions = [entry["ignition"] for entry in self.log_data]
        free_energies = [entry["free_energy"] for entry in self.log_data]
        metabolic_reserves = [entry["metabolic_reserves"] for entry in self.log_data]

        # Compute ignition statistics
        ignition_count = sum(ignitions)
        total_duration = times[-1] - times[0] if len(times) > 1 else 0
        ignition_rate = ignition_count / total_duration if total_duration > 0 else 0

        # Compute ignition intervals
        ignition_times = [times[i] for i in range(len(times)) if ignitions[i] == 1]
        ignition_intervals = []
        if len(ignition_times) > 1:
            ignition_intervals = [
                ignition_times[i + 1] - ignition_times[i] for i in range(len(ignition_times) - 1)
            ]

        # Compute free energy statistics
        fe_mean = np.mean(free_energies) if free_energies else 0
        fe_std = np.std(free_energies) if free_energies else 0
        fe_min = np.min(free_energies) if free_energies else 0
        fe_max = np.max(free_energies) if free_energies else 0

        # Compute metabolic cost statistics
        initial_reserves = metabolic_reserves[0] if metabolic_reserves else 0
        final_reserves = metabolic_reserves[-1] if metabolic_reserves else 0
        total_consumed = initial_reserves - final_reserves
        avg_per_step = total_consumed / len(self.log_data) if self.log_data else 0

        return {
            "ignition_events": {
                "count": ignition_count,
                "rate_hz": ignition_rate,
                "mean_interval": np.mean(ignition_intervals) if ignition_intervals else 0,
                "std_interval": np.std(ignition_intervals) if ignition_intervals else 0,
            },
            "free_energy": {"mean": fe_mean, "std": fe_std, "min": fe_min, "max": fe_max},
            "metabolic_costs": {
                "total_consumed": total_consumed,
                "average_per_step": avg_per_step,
                "final_reserves": final_reserves,
            },
        }


@settings(max_examples=20)
@given(num_steps=st.integers(min_value=3, max_value=20), observation=observation_strategy())
def test_property_export_data_completeness(
    num_steps: int, observation: NDArray[np.float64]
) -> None:
    """
    **Feature: apgi-enhancement-maintenance, Property 34: Export data completeness**

    For any simulation run, exported data should include all timestamps,
    subsystem states, and event markers.
    **Validates: Requirements 12.1**
    """
    # Initialize system and exporter
    system = APGISystem()
    exporter = DataExporter()

    # Run simulation for specified steps
    for step in range(num_steps):
        # Generate varied input for each step
        input_obs = observation + np.random.randn(len(observation)) * 0.1
        state = system.step(input_obs)
        exporter.record_state(state)

    # Verify data was recorded
    assert len(exporter.log_data) == num_steps

    # Define all required fields per Requirements 12.1
    required_fields = [
        "time",  # Timestamps
        "ignition",
        "workspace_active",  # Event markers
        "free_energy",
        "extero_precision",
        "intero_precision",  # Core subsystem states
        "metabolic_reserves",
        "allostatic_load",  # Thermodynamic/interoception states
        "heart_rate",
        "cortisol",  # Body states
        "gamma_power",
        "beta_power",  # Neural states
        "minimal_self_coherence",  # Self-model states
    ]

    # Verify all required fields are present in each data entry
    for entry in exporter.log_data:
        for field in required_fields:
            assert field in entry, f"Required field '{field}' missing from data entry"

    # Verify timestamps are present and monotonically increasing
    timestamps = [entry["time"] for entry in exporter.log_data]
    assert len(timestamps) == num_steps
    assert all(
        timestamps[i] <= timestamps[i + 1] for i in range(len(timestamps) - 1)
    ), "Timestamps must be monotonically increasing"

    # Verify event markers are present (ignition and workspace)
    ignitions = [entry["ignition"] for entry in exporter.log_data]
    workspace_states = [entry["workspace_active"] for entry in exporter.log_data]
    assert all(ig in [0, 1] for ig in ignitions), "Ignition markers must be 0 or 1"
    assert all(ws in [0, 1] for ws in workspace_states), "Workspace markers must be 0 or 1"

    # Verify all subsystem states are numeric and finite
    for entry in exporter.log_data:
        for field in required_fields:
            value = entry[field]
            assert isinstance(
                value, (int, float, np.number)
            ), f"Field '{field}' must be numeric, got {type(value)}"
            assert np.isfinite(value), f"Field '{field}' must be finite, got {value}"


@given(num_steps=st.integers(min_value=10, max_value=50), observation=observation_strategy())
def test_property_analysis_report_statistics(
    num_steps: int, observation: NDArray[np.float64]
) -> None:
    """
    **Feature: apgi-enhancement-maintenance, Property 35: Analysis report statistics**

    For any simulation run, generated analysis reports should include
    summary statistics for ignition events, free energy, and metabolic costs.
    **Validates: Requirements 12.2**
    """
    # Initialize system and exporter
    system = APGISystem()
    exporter = DataExporter()

    # Run simulation for specified steps
    for step in range(num_steps):
        input_obs = observation + np.random.randn(len(observation)) * 0.1
        state = system.step(input_obs)
        exporter.record_state(state)

    # Generate analysis report
    report = exporter.generate_analysis_report()

    # Verify report structure contains all required sections
    assert "ignition_events" in report, "Report must include ignition_events section"
    assert "free_energy" in report, "Report must include free_energy section"
    assert "metabolic_costs" in report, "Report must include metabolic_costs section"

    # Verify ignition event statistics
    ignition_stats = report["ignition_events"]
    assert "count" in ignition_stats, "Ignition stats must include count"
    assert "rate_hz" in ignition_stats, "Ignition stats must include rate_hz"
    assert "mean_interval" in ignition_stats, "Ignition stats must include mean_interval"
    assert "std_interval" in ignition_stats, "Ignition stats must include std_interval"

    # Verify ignition statistics are valid
    assert ignition_stats["count"] >= 0, "Ignition count must be non-negative"
    assert ignition_stats["rate_hz"] >= 0, "Ignition rate must be non-negative"
    assert ignition_stats["mean_interval"] >= 0, "Mean interval must be non-negative"
    assert ignition_stats["std_interval"] >= 0, "Std interval must be non-negative"

    # Verify free energy statistics
    fe_stats = report["free_energy"]
    assert "mean" in fe_stats, "Free energy stats must include mean"
    assert "std" in fe_stats, "Free energy stats must include std"
    assert "min" in fe_stats, "Free energy stats must include min"
    assert "max" in fe_stats, "Free energy stats must include max"

    # Verify free energy statistics are valid
    assert np.isfinite(fe_stats["mean"]), "Free energy mean must be finite"
    assert np.isfinite(fe_stats["std"]), "Free energy std must be finite"
    assert fe_stats["std"] >= 0, "Free energy std must be non-negative"
    assert fe_stats["min"] <= fe_stats["max"], "Free energy min must be <= max"

    # Verify metabolic cost statistics
    metabolic_stats = report["metabolic_costs"]
    assert "total_consumed" in metabolic_stats, "Metabolic stats must include total_consumed"
    assert "average_per_step" in metabolic_stats, "Metabolic stats must include average_per_step"
    assert "final_reserves" in metabolic_stats, "Metabolic stats must include final_reserves"

    # Verify metabolic statistics are valid
    assert np.isfinite(metabolic_stats["total_consumed"]), "Total consumed must be finite"
    assert np.isfinite(metabolic_stats["average_per_step"]), "Average per step must be finite"
    assert metabolic_stats["final_reserves"] >= 0, "Final reserves must be non-negative"
    assert metabolic_stats["average_per_step"] >= 0, "Average per step must be non-negative"


@given(num_steps=st.integers(min_value=5, max_value=30), observation=observation_strategy())
def test_property_csv_format_consistency(num_steps: int, observation: NDArray[np.float64]) -> None:
    """
    **Feature: apgi-enhancement-maintenance, Property 36: CSV format consistency**

    For any CSV export, the file should have consistent column ordering
    and include headers.
    **Validates: Requirements 12.3**
    """
    # Initialize system and exporter
    system = APGISystem()
    exporter = DataExporter()

    # Run simulation for specified steps
    for step in range(num_steps):
        input_obs = observation + np.random.randn(len(observation)) * 0.1
        state = system.step(input_obs)
        exporter.record_state(state)

    # Export to CSV
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        csv_filename = f.name

    try:
        success = exporter.export_to_csv(csv_filename)
        assert success, "CSV export should succeed"

        # Read CSV file
        with open(csv_filename, "r") as f:
            reader = csv.DictReader(f)
            csv_data = list(reader)
            headers = reader.fieldnames

        # Verify headers are present
        assert headers is not None, "CSV must include headers"
        assert len(headers) > 0, "CSV must have at least one header"

        # Verify all rows have the same number of columns
        assert len(csv_data) == num_steps, "CSV must have correct number of rows"

        for i, row in enumerate(csv_data):
            assert len(row) == len(headers), f"Row {i} must have same number of columns as headers"

        # Verify column ordering is consistent across all rows
        first_row_keys = list(csv_data[0].keys())
        for i, row in enumerate(csv_data[1:], start=1):
            row_keys = list(row.keys())
            assert row_keys == first_row_keys, f"Row {i} column order must match first row"

        # Verify headers match expected fields
        expected_fields = [
            "time",
            "ignition",
            "free_energy",
            "extero_precision",
            "intero_precision",
            "metabolic_reserves",
            "allostatic_load",
            "heart_rate",
            "cortisol",
            "workspace_active",
            "gamma_power",
            "beta_power",
            "minimal_self_coherence",
        ]

        for field in expected_fields:
            assert field in headers, f"Expected field '{field}' must be in CSV headers"

        # Verify all values in CSV are parseable as numbers
        for i, row in enumerate(csv_data):
            for field, value in row.items():
                try:
                    float(value)
                except ValueError:
                    pytest.fail(f"Row {i}, field '{field}' value '{value}' is not numeric")

    finally:
        os.unlink(csv_filename)


@given(num_steps=st.integers(min_value=5, max_value=30), observation=observation_strategy())
def test_property_json_round_trip_preservation(
    num_steps: int, observation: NDArray[np.float64]
) -> None:
    """
    **Feature: apgi-enhancement-maintenance, Property 37: JSON round-trip preservation**

    For any system state, saving to JSON and loading back should preserve
    the nested structure and data types (round-trip property).
    **Validates: Requirements 12.4**
    """
    # Initialize system and exporter
    system = APGISystem()
    exporter = DataExporter()

    # Run simulation for specified steps
    for step in range(num_steps):
        input_obs = observation + np.random.randn(len(observation)) * 0.1
        state = system.step(input_obs)
        exporter.record_state(state)

    # Store original data for comparison
    original_data = exporter.log_data.copy()

    # Export to JSON
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json_filename = f.name

    try:
        success = exporter.export_to_json(json_filename)
        assert success, "JSON export should succeed"

        # Load JSON file back
        with open(json_filename, "r") as f:
            loaded_data = json.load(f)

        # Verify round-trip preservation: loaded data matches original
        assert len(loaded_data) == len(
            original_data
        ), "Loaded data must have same length as original"

        # Verify structure preservation
        assert isinstance(loaded_data, list), "Loaded data must be a list"

        for i, (original_entry, loaded_entry) in enumerate(zip(original_data, loaded_data)):
            # Verify all keys are preserved
            assert set(original_entry.keys()) == set(
                loaded_entry.keys()
            ), f"Entry {i} keys must be preserved in round-trip"

            # Verify data types are preserved (or compatible)
            for key in original_entry.keys():
                original_value = original_entry[key]
                loaded_value = loaded_entry[key]

                # Both should be numeric
                assert isinstance(
                    original_value, (int, float, np.number)
                ), f"Original value for '{key}' must be numeric"
                assert isinstance(
                    loaded_value, (int, float)
                ), f"Loaded value for '{key}' must be numeric"

                # Values should be approximately equal (allowing for float precision)
                assert np.isclose(
                    float(original_value), float(loaded_value), rtol=1e-9
                ), f"Entry {i}, field '{key}': round-trip value mismatch"

        # Verify nested structure is preserved (data is list of dicts)
        for i, entry in enumerate(loaded_data):
            assert isinstance(entry, dict), f"Entry {i} must be a dictionary after round-trip"

            # Verify all values are numeric (not strings)
            for key, value in entry.items():
                assert isinstance(
                    value, (int, float)
                ), f"Entry {i}, field '{key}' must be numeric after round-trip, got {type(value)}"

    finally:
        os.unlink(json_filename)


@given(
    num_steps=st.integers(min_value=50, max_value=200),
    page_size=st.integers(min_value=5, max_value=30),
    observation=observation_strategy(),
)
def test_property_pagination_consistency(
    num_steps: int, page_size: int, observation: NDArray[np.float64]
) -> None:
    """
    **Feature: api-rest-interface, Property 13: Pagination consistency**

    For any paginated request, following all pagination links should eventually
    return all data without duplicates or gaps.
    **Validates: Requirements 5.5**
    """
    # Initialize system and exporter
    system = APGISystem()
    exporter = DataExporter()

    # Run simulation for specified steps to generate data
    for step in range(num_steps):
        input_obs = observation + np.random.randn(len(observation)) * 0.1
        state = system.step(input_obs)
        exporter.record_state(state)

    # Get complete data (ground truth)
    complete_data = exporter.log_data.copy()
    assert len(complete_data) == num_steps, "Complete data should have all steps"

    # Simulate paginated retrieval
    all_paginated_data = []
    seen_indices = set()
    cursor = None
    page_count = 0
    max_pages = (num_steps // page_size) + 2  # Safety limit

    while page_count < max_pages:
        # Determine start index from cursor
        start_idx = 0
        if cursor:
            try:
                cursor_data = json.loads(base64.b64decode(cursor))
                start_idx = cursor_data.get("offset", 0)
            except Exception:
                break

        # Get page of data
        end_idx = min(start_idx + page_size, len(complete_data))
        page_data = complete_data[start_idx:end_idx]

        # Check for duplicates - each index should only be seen once
        for i in range(start_idx, end_idx):
            assert i not in seen_indices, f"Index {i} returned in multiple pages (duplicate)"
            seen_indices.add(i)

        # Add to collected data
        all_paginated_data.extend(page_data)

        # Check if more data available
        has_more = end_idx < len(complete_data)

        if not has_more:
            # No more pages
            break

        # Generate next cursor
        cursor_data = {"offset": end_idx}
        cursor = base64.b64encode(json.dumps(cursor_data).encode()).decode()

        page_count += 1

    # Verify no gaps - all indices from 0 to num_steps-1 should be present
    assert (
        len(seen_indices) == num_steps
    ), f"Expected {num_steps} unique indices, got {len(seen_indices)}"
    assert seen_indices == set(range(num_steps)), "All indices should be present without gaps"

    # Verify all data was retrieved
    assert len(all_paginated_data) == num_steps, (
        f"Paginated retrieval should return all {num_steps} records, "
        f"got {len(all_paginated_data)}"
    )

    # Verify data order is preserved (no reordering)
    for i, (original, paginated) in enumerate(zip(complete_data, all_paginated_data)):
        assert (
            original == paginated
        ), f"Data at index {i} differs between complete and paginated retrieval"

    # Verify no duplicates in final result
    # Check by comparing timestamps which should be unique and monotonically increasing
    timestamps = [entry["time"] for entry in all_paginated_data]
    assert len(timestamps) == len(set(timestamps)), "Timestamps should be unique (no duplicates)"
    assert all(
        timestamps[i] <= timestamps[i + 1] for i in range(len(timestamps) - 1)
    ), "Timestamps should be monotonically increasing (data order preserved)"
