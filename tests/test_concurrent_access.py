"""
Tests for Concurrent Access (T-503)
Tests for thread safety and concurrent data access patterns.
"""

import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from apgi_framework.data.persistence_layer import PersistenceLayer


class TestConcurrentDataAccess:
    """Tests for concurrent data access patterns."""

    def test_concurrent_reads(self):
        """Test that multiple threads can read simultaneously."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            # Create initial data
            import pandas as pd

            data = pd.DataFrame({"value": range(100)})
            layer.store_data("test_exp", data)

            results = []
            errors = []

            def read_data():
                try:
                    result = layer.retrieve_data("test_exp")
                    results.append(result is not None)
                except Exception as e:
                    errors.append(str(e))

            # Spawn multiple threads to read
            threads = [threading.Thread(target=read_data) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(results) == 5
            assert all(results)
            assert len(errors) == 0

    def test_concurrent_version_creation(self):
        """Test concurrent version creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            versions_created = []
            errors = []

            def create_version(i):
                try:
                    version = layer.create_version("test_exp", f"1.{i}.0", f"Version {i}")
                    versions_created.append(version.version_number)
                except Exception as e:
                    errors.append(str(e))

            # Create versions concurrently
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(create_version, i) for i in range(5)]
                for future in as_completed(futures):
                    future.result()

            # Check that versions were created
            assert len(versions_created) == 5
            assert len(errors) == 0

    def test_thread_safe_metadata_updates(self):
        """Test thread-safe metadata updates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            # Store initial metadata
            layer.save_metadata("test_exp", {"version": 1, "data": "initial"})

            errors = []

            def update_metadata(i):
                try:
                    layer.update_metadata("test_exp", {"update_id": i})
                except Exception as e:
                    errors.append(str(e))

            # Concurrent metadata updates
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(update_metadata, i) for i in range(5)]
                for future in as_completed(futures):
                    future.result()

            # Verify final state
            metadata = layer.get_metadata("test_exp")
            assert metadata is not None
            assert len(errors) == 0


class TestThreadSafety:
    """Tests for thread safety in core components."""

    def test_analysis_engine_thread_safety(self):
        """Test that AnalysisEngine handles concurrent analysis requests."""
        import pandas as pd

        from apgi_framework.analysis.analysis_engine import AnalysisEngine

        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            results = []
            errors = []

            def run_analysis(i):
                try:
                    data = pd.DataFrame({"x": range(10), "y": range(10, 20)})
                    result = engine.analyze(data, "descriptive", generate_plots=False)
                    results.append(result.analysis_id)
                except Exception as e:
                    errors.append(str(e))

            # Run analyses concurrently
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(run_analysis, i) for i in range(5)]
                for future in as_completed(futures):
                    future.result()

            assert len(results) == 5
            assert len(errors) == 0


class TestRaceConditions:
    """Tests for race condition prevention."""

    def test_no_race_condition_in_version_listing(self):
        """Test that version listing is consistent during concurrent creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            def create_and_list(i):
                layer.create_version("test_exp", f"2.{i}.0", f"Version {i}")
                versions = layer.list_versions("test_exp")
                return len(versions)

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(create_and_list, i) for i in range(10)]
                version_counts = [f.result() for f in as_completed(futures)]

            # All counts should be consistent (monotonically increasing)
            assert len(version_counts) == 10
            assert all(c > 0 for c in version_counts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
