"""
Unit tests for data export functionality.

This module tests CSV export, JSON export, and analysis report generation
with specific data scenarios and edge cases.

**Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5**
"""

import numpy as np
import pytest
import json
import csv
import tempfile
import os
from pathlib import Path

from apgi_system.system import APGISystem


class DataExporter:
    """
    Helper class for data export functionality.
    
    This class simulates the export logic from the GUI application,
    allowing us to test export functionality in isolation.
    """
    
    def __init__(self):
        """Initialize data exporter."""
        self.log_data = []
        
    def record_state(self, state):
        """
        Record state data from simulation step.
        
        Parameters
        ----------
        state : dict
            System state dictionary from APGISystem.step()
        """
        current_time = state['time'] / 1000.0  # Convert to seconds
        
        # Extract and record metrics (matches GUI logic)
        data_entry = {
            'time': current_time,
            'ignition': 1 if state['ignition']['ignition_occurred'] else 0,
            'free_energy': state['ignition']['total_signal'],
            'extero_precision': state['precision']['exteroceptive'],
            'intero_precision': state['precision']['interoceptive'],
            'metabolic_reserves': state['metabolism']['reserves'],
            'allostatic_load': state['allostasis']['allostatic_load'],
            'heart_rate': state['body']['current']['heart_rate'],
            'cortisol': state['body']['current']['cortisol'],
            'workspace_active': 1 if state['workspace']['is_broadcasting'] else 0,
            'gamma_power': state['oscillations']['band_powers'].get('gamma', 0),
            'beta_power': state['oscillations']['band_powers'].get('beta', 0),
            'minimal_self_coherence': state['self_model']['minimal']['coherence']
        }
        
        self.log_data.append(data_entry)
        
    def export_to_csv(self, filename):
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
            
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.log_data[0].keys())
            writer.writeheader()
            writer.writerows(self.log_data)
        return True
        
    def export_to_json(self, filename):
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
            
        with open(filename, 'w') as f:
            json.dump(self.log_data, f, indent=2)
        return True
        
    def generate_analysis_report(self):
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
        times = [entry['time'] for entry in self.log_data]
        ignitions = [entry['ignition'] for entry in self.log_data]
        free_energies = [entry['free_energy'] for entry in self.log_data]
        metabolic_reserves = [entry['metabolic_reserves'] for entry in self.log_data]
        
        # Compute ignition statistics
        ignition_count = sum(ignitions)
        total_duration = times[-1] - times[0] if len(times) > 1 else 0
        ignition_rate = ignition_count / total_duration if total_duration > 0 else 0
        
        # Compute ignition intervals
        ignition_times = [times[i] for i in range(len(times)) if ignitions[i] == 1]
        ignition_intervals = []
        if len(ignition_times) > 1:
            ignition_intervals = [ignition_times[i+1] - ignition_times[i] 
                                 for i in range(len(ignition_times)-1)]
        
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
            'ignition_events': {
                'count': ignition_count,
                'rate_hz': ignition_rate,
                'mean_interval': np.mean(ignition_intervals) if ignition_intervals else 0,
                'std_interval': np.std(ignition_intervals) if ignition_intervals else 0
            },
            'free_energy': {
                'mean': fe_mean,
                'std': fe_std,
                'min': fe_min,
                'max': fe_max
            },
            'metabolic_costs': {
                'total_consumed': total_consumed,
                'average_per_step': avg_per_step,
                'final_reserves': final_reserves
            }
        }


class TestCSVExport:
    """Test CSV export functionality with specific data scenarios."""
    
    def test_csv_export_with_specific_data(self):
        """
        Test CSV export with specific known data values.
        
        **Validates: Requirements 12.1, 12.3**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation for 5 steps with specific observations
        for i in range(5):
            obs = np.ones(256) * (i + 1) * 0.1  # Specific pattern
            state = system.step(obs)
            exporter.record_state(state)
        
        # Export to CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_filename = f.name
        
        try:
            success = exporter.export_to_csv(csv_filename)
            assert success, "CSV export should succeed"
            
            # Read back and verify
            with open(csv_filename, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Verify row count
            assert len(rows) == 5, "Should have 5 rows of data"
            
            # Verify headers are present
            expected_headers = [
                'time', 'ignition', 'free_energy', 'extero_precision', 'intero_precision',
                'metabolic_reserves', 'allostatic_load', 'heart_rate', 'cortisol',
                'workspace_active', 'gamma_power', 'beta_power', 'minimal_self_coherence'
            ]
            
            for header in expected_headers:
                assert header in rows[0].keys(), f"Header '{header}' should be present"
            
            # Verify data types can be parsed
            for row in rows:
                assert float(row['time']) >= 0, "Time should be non-negative"
                assert int(row['ignition']) in [0, 1], "Ignition should be 0 or 1"
                assert float(row['free_energy']) >= 0, "Free energy should be non-negative"
                assert float(row['metabolic_reserves']) >= 0, "Metabolic reserves should be non-negative"
        
        finally:
            os.unlink(csv_filename)
    
    def test_csv_export_empty_data(self):
        """
        Test CSV export with no data returns False.
        
        **Validates: Requirements 12.1**
        """
        exporter = DataExporter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_filename = f.name
        
        try:
            success = exporter.export_to_csv(csv_filename)
            assert not success, "CSV export should fail with no data"
        finally:
            if os.path.exists(csv_filename):
                os.unlink(csv_filename)
    
    def test_csv_column_ordering_consistency(self):
        """
        Test that CSV columns maintain consistent ordering across exports.
        
        **Validates: Requirements 12.3**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation
        for i in range(3):
            obs = np.random.randn(256) * 0.5
            state = system.step(obs)
            exporter.record_state(state)
        
        # Export to CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_filename = f.name
        
        try:
            exporter.export_to_csv(csv_filename)
            
            # Read headers
            with open(csv_filename, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
            
            # Verify consistent ordering (should match log_data keys order)
            expected_order = list(exporter.log_data[0].keys())
            assert headers == expected_order, "CSV headers should match data key order"
        
        finally:
            os.unlink(csv_filename)
    
    def test_csv_export_with_edge_case_values(self):
        """
        Test CSV export handles edge case values correctly.
        
        **Validates: Requirements 12.1, 12.3**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation with extreme observations
        extreme_obs = [
            np.zeros(256),  # All zeros
            np.ones(256) * 10,  # Large values
            np.random.randn(256) * 0.01  # Very small values
        ]
        
        for obs in extreme_obs:
            state = system.step(obs)
            exporter.record_state(state)
        
        # Export to CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_filename = f.name
        
        try:
            success = exporter.export_to_csv(csv_filename)
            assert success, "CSV export should handle edge case values"
            
            # Verify file is readable
            with open(csv_filename, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 3, "Should have 3 rows"
            
            # Verify all values are valid numbers
            for row in rows:
                for key, value in row.items():
                    try:
                        float(value)
                    except ValueError:
                        pytest.fail(f"Value '{value}' for key '{key}' is not a valid number")
        
        finally:
            os.unlink(csv_filename)


class TestJSONExport:
    """Test JSON export functionality with nested structures."""
    
    def test_json_export_with_specific_data(self):
        """
        Test JSON export with specific known data values.
        
        **Validates: Requirements 12.1, 12.4**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation for 5 steps
        for i in range(5):
            obs = np.ones(256) * (i + 1) * 0.1
            state = system.step(obs)
            exporter.record_state(state)
        
        # Export to JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_filename = f.name
        
        try:
            success = exporter.export_to_json(json_filename)
            assert success, "JSON export should succeed"
            
            # Read back and verify
            with open(json_filename, 'r') as f:
                data = json.load(f)
            
            # Verify structure
            assert isinstance(data, list), "JSON data should be a list"
            assert len(data) == 5, "Should have 5 entries"
            
            # Verify each entry is a dictionary
            for entry in data:
                assert isinstance(entry, dict), "Each entry should be a dictionary"
                assert 'time' in entry, "Each entry should have 'time'"
                assert 'ignition' in entry, "Each entry should have 'ignition'"
                assert 'free_energy' in entry, "Each entry should have 'free_energy'"
        
        finally:
            os.unlink(json_filename)
    
    def test_json_export_preserves_data_types(self):
        """
        Test that JSON export preserves data types correctly.
        
        **Validates: Requirements 12.4**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation
        obs = np.random.randn(256) * 0.5
        state = system.step(obs)
        exporter.record_state(state)
        
        # Export to JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_filename = f.name
        
        try:
            exporter.export_to_json(json_filename)
            
            # Read back
            with open(json_filename, 'r') as f:
                data = json.load(f)
            
            entry = data[0]
            
            # Verify data types
            assert isinstance(entry['time'], (int, float)), "Time should be numeric"
            assert isinstance(entry['ignition'], int), "Ignition should be integer"
            assert isinstance(entry['free_energy'], (int, float)), "Free energy should be numeric"
            assert isinstance(entry['extero_precision'], (int, float)), "Precision should be numeric"
            assert isinstance(entry['metabolic_reserves'], (int, float)), "Reserves should be numeric"
        
        finally:
            os.unlink(json_filename)
    
    def test_json_export_empty_data(self):
        """
        Test JSON export with no data returns False.
        
        **Validates: Requirements 12.1**
        """
        exporter = DataExporter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_filename = f.name
        
        try:
            success = exporter.export_to_json(json_filename)
            assert not success, "JSON export should fail with no data"
        finally:
            if os.path.exists(json_filename):
                os.unlink(json_filename)
    
    def test_json_round_trip_preservation(self):
        """
        Test that JSON export and import preserves data structure.
        
        **Validates: Requirements 12.4**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation
        for i in range(3):
            obs = np.random.randn(256) * 0.5
            state = system.step(obs)
            exporter.record_state(state)
        
        # Store original data
        original_data = exporter.log_data.copy()
        
        # Export to JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_filename = f.name
        
        try:
            exporter.export_to_json(json_filename)
            
            # Read back
            with open(json_filename, 'r') as f:
                loaded_data = json.load(f)
            
            # Verify data matches
            assert len(loaded_data) == len(original_data), "Data length should match"
            
            for orig, loaded in zip(original_data, loaded_data):
                for key in orig.keys():
                    assert key in loaded, f"Key '{key}' should be preserved"
                    # Compare values with tolerance for floating point
                    if isinstance(orig[key], float):
                        assert abs(orig[key] - loaded[key]) < 1e-6, f"Value for '{key}' should match"
                    else:
                        assert orig[key] == loaded[key], f"Value for '{key}' should match exactly"
        
        finally:
            os.unlink(json_filename)
    
    def test_json_export_with_nested_structures(self):
        """
        Test JSON export handles nested data structures correctly.
        
        **Validates: Requirements 12.4**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation
        obs = np.random.randn(256) * 0.5
        state = system.step(obs)
        exporter.record_state(state)
        
        # Export to JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_filename = f.name
        
        try:
            exporter.export_to_json(json_filename)
            
            # Read and verify structure is preserved
            with open(json_filename, 'r') as f:
                data = json.load(f)
            
            # Verify it's a list of dictionaries (nested structure)
            assert isinstance(data, list), "Top level should be list"
            assert isinstance(data[0], dict), "Each entry should be dict"
            
            # Verify all keys are strings (JSON requirement)
            for key in data[0].keys():
                assert isinstance(key, str), "All keys should be strings"
        
        finally:
            os.unlink(json_filename)


class TestAnalysisReportGeneration:
    """Test analysis report generation functionality."""
    
    def test_analysis_report_with_specific_data(self):
        """
        Test analysis report generation with specific known data.
        
        **Validates: Requirements 12.2**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation for 10 steps
        for i in range(10):
            obs = np.random.randn(256) * 0.5
            state = system.step(obs)
            exporter.record_state(state)
        
        # Generate report
        report = exporter.generate_analysis_report()
        
        # Verify report structure
        assert 'ignition_events' in report, "Report should include ignition_events"
        assert 'free_energy' in report, "Report should include free_energy"
        assert 'metabolic_costs' in report, "Report should include metabolic_costs"
        
        # Verify ignition event statistics
        ignition_stats = report['ignition_events']
        assert 'count' in ignition_stats, "Should include ignition count"
        assert 'rate_hz' in ignition_stats, "Should include ignition rate"
        assert 'mean_interval' in ignition_stats, "Should include mean interval"
        assert 'std_interval' in ignition_stats, "Should include std interval"
        
        # Verify values are valid
        assert ignition_stats['count'] >= 0, "Count should be non-negative"
        assert ignition_stats['rate_hz'] >= 0, "Rate should be non-negative"
        assert ignition_stats['mean_interval'] >= 0, "Mean interval should be non-negative"
        assert ignition_stats['std_interval'] >= 0, "Std interval should be non-negative"
    
    def test_analysis_report_free_energy_statistics(self):
        """
        Test that analysis report includes correct free energy statistics.
        
        **Validates: Requirements 12.2**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation
        for i in range(10):
            obs = np.random.randn(256) * 0.5
            state = system.step(obs)
            exporter.record_state(state)
        
        # Generate report
        report = exporter.generate_analysis_report()
        
        # Verify free energy statistics
        fe_stats = report['free_energy']
        assert 'mean' in fe_stats, "Should include mean"
        assert 'std' in fe_stats, "Should include std"
        assert 'min' in fe_stats, "Should include min"
        assert 'max' in fe_stats, "Should include max"
        
        # Verify values are valid
        assert np.isfinite(fe_stats['mean']), "Mean should be finite"
        assert np.isfinite(fe_stats['std']), "Std should be finite"
        assert fe_stats['std'] >= 0, "Std should be non-negative"
        assert fe_stats['min'] <= fe_stats['max'], "Min should be <= max"
        
        # Verify statistics match raw data
        free_energies = [entry['free_energy'] for entry in exporter.log_data]
        assert abs(fe_stats['mean'] - np.mean(free_energies)) < 1e-6, "Mean should match"
        assert abs(fe_stats['min'] - np.min(free_energies)) < 1e-6, "Min should match"
        assert abs(fe_stats['max'] - np.max(free_energies)) < 1e-6, "Max should match"
    
    def test_analysis_report_metabolic_cost_statistics(self):
        """
        Test that analysis report includes correct metabolic cost statistics.
        
        **Validates: Requirements 12.2**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation
        for i in range(10):
            obs = np.random.randn(256) * 0.5
            state = system.step(obs)
            exporter.record_state(state)
        
        # Generate report
        report = exporter.generate_analysis_report()
        
        # Verify metabolic cost statistics
        metabolic_stats = report['metabolic_costs']
        assert 'total_consumed' in metabolic_stats, "Should include total_consumed"
        assert 'average_per_step' in metabolic_stats, "Should include average_per_step"
        assert 'final_reserves' in metabolic_stats, "Should include final_reserves"
        
        # Verify values are valid
        assert metabolic_stats['total_consumed'] >= 0, "Total consumed should be non-negative"
        assert metabolic_stats['average_per_step'] >= 0, "Average should be non-negative"
        assert metabolic_stats['final_reserves'] >= 0, "Final reserves should be non-negative"
        
        # Verify calculation is correct
        initial_reserves = exporter.log_data[0]['metabolic_reserves']
        final_reserves = exporter.log_data[-1]['metabolic_reserves']
        expected_consumed = initial_reserves - final_reserves
        
        assert abs(metabolic_stats['total_consumed'] - expected_consumed) < 1e-6, \
            "Total consumed should match calculation"
        assert abs(metabolic_stats['final_reserves'] - final_reserves) < 1e-6, \
            "Final reserves should match"
    
    def test_analysis_report_empty_data(self):
        """
        Test analysis report generation with no data returns empty dict.
        
        **Validates: Requirements 12.2**
        """
        exporter = DataExporter()
        
        # Generate report with no data
        report = exporter.generate_analysis_report()
        
        assert report == {}, "Report should be empty dict with no data"
    
    def test_analysis_report_single_step(self):
        """
        Test analysis report generation with single step handles edge case.
        
        **Validates: Requirements 12.2**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run single step
        obs = np.random.randn(256) * 0.5
        state = system.step(obs)
        exporter.record_state(state)
        
        # Generate report
        report = exporter.generate_analysis_report()
        
        # Verify report is generated
        assert 'ignition_events' in report, "Report should be generated"
        assert 'free_energy' in report, "Report should include free energy"
        assert 'metabolic_costs' in report, "Report should include metabolic costs"
        
        # With single step, rate should be 0 (no duration)
        assert report['ignition_events']['rate_hz'] == 0, "Rate should be 0 with single step"
    
    def test_analysis_report_ignition_intervals(self):
        """
        Test that analysis report correctly computes ignition intervals.
        
        **Validates: Requirements 12.2**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation long enough to get multiple ignitions
        for i in range(50):
            obs = np.random.randn(256) * 2.0  # Larger values to trigger ignitions
            state = system.step(obs)
            exporter.record_state(state)
        
        # Generate report
        report = exporter.generate_analysis_report()
        
        ignition_stats = report['ignition_events']
        
        # If we have ignitions, verify interval statistics
        if ignition_stats['count'] > 1:
            assert ignition_stats['mean_interval'] > 0, "Mean interval should be positive"
            assert ignition_stats['std_interval'] >= 0, "Std interval should be non-negative"
        else:
            # With 0 or 1 ignitions, intervals should be 0
            assert ignition_stats['mean_interval'] == 0, "Mean interval should be 0"
            assert ignition_stats['std_interval'] == 0, "Std interval should be 0"
    
    def test_analysis_report_consistency_across_runs(self):
        """
        Test that analysis report is consistent for same data.
        
        **Validates: Requirements 12.2**
        """
        exporter = DataExporter()
        system = APGISystem()
        
        # Run simulation
        np.random.seed(42)  # Fixed seed for reproducibility
        for i in range(10):
            obs = np.random.randn(256) * 0.5
            state = system.step(obs)
            exporter.record_state(state)
        
        # Generate report twice
        report1 = exporter.generate_analysis_report()
        report2 = exporter.generate_analysis_report()
        
        # Verify reports are identical
        assert report1 == report2, "Reports should be identical for same data"
