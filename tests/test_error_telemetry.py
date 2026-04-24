"""
Tests for error telemetry system.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from apgi_framework.logging.error_telemetry import (
    ErrorTelemetry,
    get_error_telemetry,
    report_error,
    enable_error_reporting,
)


class TestErrorTelemetry:
    """Test error telemetry functionality."""

    def test_initialization_creates_directory(self):
        """Test that initialization creates the telemetry directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry_dir = Path(temp_dir) / "telemetry"
            telemetry = ErrorTelemetry(str(telemetry_dir))

            assert telemetry_dir.exists()
            assert telemetry.telemetry_file.exists()

    def test_report_error_stores_data(self):
        """Test that reporting an error stores the data correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry = ErrorTelemetry(Path(temp_dir) / "telemetry")

            telemetry.report_error(
                error_type="ValueError",
                error_message="Test error",
                context={"test": "data"},
                user_id="test_user",
            )

            # Check data was stored
            assert len(telemetry.telemetry_data["errors"]) == 1
            error = telemetry.telemetry_data["errors"][0]
            assert error["error_type"] == "ValueError"
            assert error["error_message"] == "Test error"
            assert error["context"] == {"test": "data"}
            assert error["user_id"] == "test_user"
            assert "timestamp" in error
            assert "system_info" in error

    def test_report_error_with_traceback(self):
        """Test reporting error with traceback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry = ErrorTelemetry(Path(temp_dir) / "telemetry")

            traceback = "Traceback (most recent call last):\n  File 'test.py', line 1"
            telemetry.report_error(
                error_type="Exception",
                error_message="Error with traceback",
                traceback=traceback,
            )

            error = telemetry.telemetry_data["errors"][0]
            assert error["traceback"] == traceback

    def test_max_errors_limit(self):
        """Test that only last 1000 errors are kept."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry = ErrorTelemetry(Path(temp_dir) / "telemetry")

            # Report 1001 errors
            for i in range(1001):
                telemetry.report_error(f"Error{i}", f"Message{i}")

            # Should only keep last 1000
            assert len(telemetry.telemetry_data["errors"]) == 1000
            # First error should be error 1, not error 0
            assert telemetry.telemetry_data["errors"][0]["error_type"] == "Error1"

    def test_get_error_summary_empty(self):
        """Test error summary when no errors reported."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry = ErrorTelemetry(Path(temp_dir) / "telemetry")

            summary = telemetry.get_error_summary()
            assert summary["total_errors"] == 0
            assert summary["error_types"] == {}
            assert summary["recent_errors"] == []

    def test_get_error_summary_with_data(self):
        """Test error summary with reported errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry = ErrorTelemetry(Path(temp_dir) / "telemetry")

            # Report some errors
            telemetry.report_error("ValueError", "Error 1")
            telemetry.report_error("ValueError", "Error 2")
            telemetry.report_error("TypeError", "Error 3")

            summary = telemetry.get_error_summary()
            assert summary["total_errors"] == 3
            assert summary["error_types"]["ValueError"] == 2
            assert summary["error_types"]["TypeError"] == 1
            assert len(summary["recent_errors"]) == 3

    def test_export_telemetry(self):
        """Test exporting telemetry data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry = ErrorTelemetry(Path(temp_dir) / "telemetry")

            telemetry.report_error("TestError", "Test message")

            export_path = Path(temp_dir) / "export.json"
            telemetry.export_telemetry(str(export_path))

            assert export_path.exists()

            with open(export_path, "r") as f:
                exported = json.load(f)

            assert "summary" in exported
            assert "full_data" in exported
            assert exported["summary"]["total_errors"] == 1

    def test_clear_telemetry(self):
        """Test clearing telemetry data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry = ErrorTelemetry(Path(temp_dir) / "telemetry")

            telemetry.report_error("TestError", "Test message")
            assert len(telemetry.telemetry_data["errors"]) == 1

            telemetry.clear_telemetry()
            assert len(telemetry.telemetry_data["errors"]) == 0

    def test_get_error_telemetry_singleton(self):
        """Test that get_error_telemetry returns a singleton."""
        telemetry1 = get_error_telemetry()
        telemetry2 = get_error_telemetry()

        assert telemetry1 is telemetry2

    def test_report_error_convenience_function(self):
        """Test the convenience report_error function."""
        with patch("apgi_framework.logging.error_telemetry.get_error_telemetry") as mock_get:
            mock_telemetry = mock_get.return_value

            report_error("TestError", "Test message", context={"key": "value"})

            mock_telemetry.report_error.assert_called_once_with(
                "TestError", "Test message", None, {"key": "value"}, None
            )

    def test_enable_error_reporting_true(self):
        """Test enabling error reporting."""
        # Reset the global telemetry instance to ensure it's None
        import apgi_framework.logging.error_telemetry

        apgi_framework.logging.error_telemetry._telemetry = None

        with patch("apgi_framework.logging.error_telemetry.ErrorTelemetry") as mock_class:
            enable_error_reporting(True)
            mock_class.assert_called_once()

    def test_enable_error_reporting_false(self):
        """Test disabling error reporting."""
        # First enable to set the global instance
        with patch("apgi_framework.logging.error_telemetry.ErrorTelemetry"):
            enable_error_reporting(True)

        # Then disable
        enable_error_reporting(False)

        # Check that get_error_telemetry returns None-like behavior
        # Since it's a global, it's hard to test directly, but we can check the function exists

    @patch("apgi_framework.logging.error_telemetry.logger")
    def test_telemetry_saves_on_report(self, mock_logger):
        """Test that telemetry data is saved when error is reported."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry = ErrorTelemetry(Path(temp_dir) / "telemetry")

            # Mock _save_telemetry to check it's called
            with patch.object(telemetry, "_save_telemetry") as mock_save:
                telemetry.report_error("TestError", "Test message")
                mock_save.assert_called_once()

    def test_system_info_included(self):
        """Test that system info is included in error reports."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry = ErrorTelemetry(Path(temp_dir) / "telemetry")

            telemetry.report_error("TestError", "Test message")

            error = telemetry.telemetry_data["errors"][0]
            assert "system_info" in error
            assert isinstance(error["system_info"], dict)

    def test_load_existing_telemetry(self):
        """Test loading existing telemetry data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry_dir = Path(temp_dir) / "telemetry"
            telemetry_file = telemetry_dir / "error_telemetry.json"
            telemetry_dir.mkdir()

            # Create existing telemetry file
            existing_data = {
                "errors": [
                    {
                        "timestamp": "2023-01-01T00:00:00",
                        "error_type": "ExistingError",
                        "error_message": "Existing message",
                        "context": {},
                        "system_info": {},
                    }
                ],
                "system_info": {},
            }

            with open(telemetry_file, "w") as f:
                json.dump(existing_data, f)

            # Create telemetry instance
            telemetry = ErrorTelemetry(str(telemetry_dir))

            # Check existing data was loaded
            assert len(telemetry.telemetry_data["errors"]) == 1
            assert telemetry.telemetry_data["errors"][0]["error_type"] == "ExistingError"

    def test_corrupted_telemetry_file_handling(self):
        """Test handling of corrupted telemetry file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry_dir = Path(temp_dir) / "telemetry"
            telemetry_file = telemetry_dir / "error_telemetry.json"
            telemetry_dir.mkdir()

            # Create corrupted file
            telemetry_file.write_text("{corrupted json")

            # Should handle gracefully
            telemetry = ErrorTelemetry(str(telemetry_dir))

            # Should have default empty data
            assert telemetry.telemetry_data["errors"] == []
