"""
Comprehensive tests for export module.

Tests BIDS export functionality, file validation, sanitization,
and export of various data types (EEG, behavioral, physiological).
"""

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from apgi_framework.export.bids_export import BIDSExporter, export_apgi_to_bids


class TestBIDSExporter:
    """Test suite for BIDSExporter."""

    def setup_method(self):
        """Set up test environment."""
        import tempfile

        self.temp_dir = Path(tempfile.mkdtemp())
        self.exporter = BIDSExporter(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_default_directory(self):
        """Test exporter initialization with default directory."""
        exporter = BIDSExporter()
        assert exporter.bids_root.name == "bids_dataset"
        assert exporter.bids_root.exists()

    def test_init_custom_directory(self):
        """Test exporter initialization with custom directory."""
        custom_dir = Path("/tmp/test_bids")
        exporter = BIDSExporter(custom_dir)
        assert exporter.bids_root == custom_dir

    def test_create_bids_structure(self):
        """Test BIDS directory structure creation."""
        # Check that all required directories are created
        required_dirs = [
            "sub-01",
            "sub-01/ses-01",
            "sub-01/ses-01/eeg",
            "sub-01/ses-01/beh",
            "sub-01/ses-01/physio",
            "derivatives",
            "derivatives/analysis",
            "code",
            "stimuli",
            "sourcedata",
        ]

        for dir_name in required_dirs:
            assert (self.temp_dir / dir_name).exists()

    def test_sanitize_string_valid(self):
        """Test string sanitization with valid input."""
        valid_cases = [
            ("subject-01", "subject-01"),
            ("session-A", "session-A"),
            ("task-rest", "task-rest"),
            ("Test-File", "Test-File"),
            ("data-with-hyphens", "data-with-hyphens"),
            ("multiple---hyphens", "multiple-hyphens"),
        ]

        for input_str, expected in valid_cases:
            result = self.exporter._sanitize_string(input_str)
            assert result == expected

    def test_sanitize_string_invalid(self):
        """Test string sanitization with invalid input."""
        invalid_cases = [
            None,
            123,
            "path/with/slashes",
            "path\\with\\backslashes",
            "string with spaces",
            "",  # Empty string
            "___",  # Only underscores
        ]

        for invalid in invalid_cases:
            with pytest.raises(ValueError):
                self.exporter._sanitize_string(invalid)

    def test_create_bids_filename(self):
        """Test BIDS filename creation."""
        entities = {"sub": "test-01", "ses": "session-A", "task": "rest"}

        filename = self.exporter._create_bids_filename(entities, "eeg", "set")
        expected = "sub-test-01_ses-session-A_task-rest_eeg.set"

        assert filename == expected

    def test_create_bids_filename_missing_entities(self):
        """Test BIDS filename with missing entities."""
        entities = {"sub": "test-01"}  # Missing ses and task

        filename = self.exporter._create_bids_filename(entities, "eeg", "set")
        expected = "sub-test-01_eeg.set"

        assert filename == expected

    def test_export_eeg_data_basic(self):
        """Test basic EEG data export."""
        # Create test data
        data = np.random.rand(4, 1000)  # 4 channels, 1000 timepoints
        subject_id = "test-01"
        channels = ["Fz", "Cz", "Pz", "Oz"]
        sampling_rate = 1000.0

        # Export data
        result_path = self.exporter.export_eeg_data(
            data=data,
            subject_id=subject_id,
            channels=channels,
            sampling_rate=sampling_rate,
        )

        # Verify file structure
        expected_dir = self.temp_dir / "sub-test-01/eeg"
        assert expected_dir.exists()
        assert result_path.parent == expected_dir

        # Check EEG set file
        eeg_file = result_path.with_suffix(".csv")
        assert eeg_file.exists()

        # Check channels file (BIDS format: sub-test-01_task-rest_eeg_channels.tsv)
        channels_file = expected_dir / "sub-test-01_task-rest_eeg_channels.tsv"
        assert channels_file.exists()

        # Check JSON sidecar (BIDS format: sub-test-01_task-rest_eeg.json)
        json_file = expected_dir / "sub-test-01_task-rest_eeg.json"
        assert json_file.exists()

        # Verify JSON content
        with open(json_file, "r") as f:
            json_data = json.load(f)
            assert json_data["SamplingFrequency"] == sampling_rate
            assert json_data["ChannelCount"] == len(channels)

    def test_export_eeg_data_with_session(self):
        """Test EEG data export with session."""
        data = np.random.rand(2, 1000)
        subject_id = "test-01"
        session_id = "session-A"
        channels = ["Fz", "Cz"]

        result_path = self.exporter.export_eeg_data(
            data=data, subject_id=subject_id, session_id=session_id, channels=channels
        )

        # Verify session directory structure
        expected_dir = self.temp_dir / "sub-test-01/ses-session-A/eeg"
        assert expected_dir.exists()
        assert result_path.parent == expected_dir

    def test_export_eeg_data_invalid_subject_id(self):
        """Test EEG export with invalid subject ID (path traversal)."""
        data = np.random.rand(1, 1000)

        with pytest.raises(ValueError, match="Invalid characters in string"):
            self.exporter.export_eeg_data(
                data=data, subject_id="../../../etc/passwd", channels=["Fz"]
            )

    def test_export_behavioral_data(self):
        """Test behavioral data export."""
        # Create test behavioral data
        data = pd.DataFrame(
            {
                "trial_number": range(1, 11),
                "reaction_time": np.random.normal(300, 50, 10),
                "accuracy": np.random.choice([0, 1], 10),
                "condition": np.random.choice(["easy", "hard"], 10),
            }
        )
        subject_id = "test-01"
        task_name = "experiment"

        result_path = self.exporter.export_behavioral_data(
            data=data, subject_id=subject_id, task_name=task_name
        )

        # Verify file structure
        expected_dir = self.temp_dir / "sub-test-01/beh"
        assert expected_dir.exists()
        assert result_path.parent == expected_dir

        # Check TSV file
        tsv_file = result_path.with_suffix(".tsv")
        assert tsv_file.exists()

        # Check JSON sidecar
        json_file = expected_dir / result_path.name.replace(".tsv", ".json")
        assert json_file.exists()

    def test_export_physiological_data(self):
        """Test physiological data export."""
        # Create test physiological data
        data = {
            "pupil": np.random.rand(1000),  # Pupil diameter over time
            "cardiac": np.random.rand(500),  # Heart rate data
        }
        subject_id = "test-01"
        sampling_rates = {"pupil": 1000.0, "cardiac": 250.0}

        self.exporter.export_physiological_data(
            data=data, subject_id=subject_id, sampling_rates=sampling_rates
        )

        # Verify files were created
        for data_type in data.keys():
            expected_dir = self.temp_dir / "sub-test-01/physio"
            assert expected_dir.exists()

            # Check for expected files
            files = list(expected_dir.glob(f"*{data_type}*"))
            assert len(files) >= 2  # At least TSV and JSON

            # Check JSON sidecar exists (BIDS format: sub-test-01_task-rest_{data_type}.json)
            json_file = expected_dir / f"sub-test-01_task-rest_{data_type}.json"
            assert json_file.exists()

    def test_create_dataset_description(self):
        """Test dataset description creation."""
        name = "Test Dataset"
        authors = ["Test Author", "Another Author"]
        description = "A test dataset for BIDS export"
        doi = "10.1234/test.doi"

        result_path = self.exporter.create_dataset_description(
            name=name, authors=authors, description=description, doi=doi
        )

        assert result_path.exists()
        assert result_path.name == "dataset_description.json"

        # Verify content
        with open(result_path, "r") as f:
            data = json.load(f)
            assert data["Name"] == name
            assert data["Authors"] == authors
            assert data["Description"] == description
            assert data["DOI"] == doi
            assert data["BIDSVersion"] == "1.7.0"

    def test_create_participants_tsv(self):
        """Test participants TSV creation."""
        participants = [
            {"participant_id": "01", "age": 25, "sex": "M", "handedness": "R"},
            {"participant_id": "02", "age": 30, "sex": "F", "handedness": "L"},
        ]

        result_path = self.exporter.create_participants_tsv(participants)

        assert result_path.exists()
        assert result_path.name == "participants.tsv"

        # Verify TSV and JSON files created
        json_path = self.temp_dir / "participants.json"
        assert json_path.exists()

    def test_validate_bids_structure_success(self):
        """Test BIDS structure validation with valid structure."""
        # Create a valid BIDS structure
        self.exporter._create_bids_structure()

        # Add some valid files
        (self.temp_dir / "sub-01/eeg").mkdir(parents=True, exist_ok=True)
        (self.temp_dir / "sub-01/beh").mkdir(parents=True, exist_ok=True)
        (self.temp_dir / "dataset_description.json").touch()
        (self.temp_dir / "README.md").touch()

        validation = self.exporter.validate_bids_structure()

        assert len(validation.get("errors", [])) == 0
        assert "info" in validation

    def test_validate_bids_structure_missing_files(self):
        """Test BIDS structure validation with missing required files."""
        # Create incomplete structure
        self.exporter._create_bids_structure()

        validation = self.exporter.validate_bids_structure()

        assert len(validation["errors"]) > 0
        assert any("Missing required file" in error for error in validation["errors"])

    def test_validate_bids_structure_no_subjects(self):
        """Test BIDS structure validation with no subject directories."""
        # Create structure but remove default subject directories
        self.exporter._create_bids_structure()
        import shutil

        shutil.rmtree(self.temp_dir / "sub-01")
        (self.temp_dir / "dataset_description.json").touch()
        (self.temp_dir / "README.md").touch()

        validation = self.exporter.validate_bids_structure()

        assert any("No subject directories found" in error for error in validation["errors"])

    def test_export_apgi_to_bids_complete(self):
        """Test complete APGI to BIDS export."""
        # Create comprehensive test data
        test_data = {
            "test-01": {
                "eeg": {
                    "data": np.random.rand(6, 1000),
                    "channels": ["Fz", "Cz", "Pz", "Oz", "T7", "T8"],
                    "sampling_rate": 1000.0,
                    "task": "rest",
                    "metadata": {"experiment": "baseline"},
                },
                "behavioral": {
                    "data": pd.DataFrame(
                        {
                            "trial": range(1, 6),
                            "response": np.random.choice(["A", "B"], 5),
                        }
                    ),
                    "task": "experiment",
                },
                "physiological": {
                    "data": {
                        "pupil": np.random.rand(1000),
                        "cardiac": np.random.rand(500),
                    },
                    "sampling_rates": {"pupil": 1000.0, "cardiac": 250.0},
                },
            }
        }

        with patch("apgi_framework.export.bids_export.logger"):
            result_paths = export_apgi_to_bids(
                data=test_data,
                bids_root=self.temp_dir,
                dataset_name="Test Export",
                authors=["Test Author"],
                description="Complete test dataset",
            )

            # Verify export completed
            assert isinstance(result_paths, dict)
            assert "dataset_description" in result_paths

            # Verify all expected files were created
            assert (self.temp_dir / "dataset_description.json").exists()
            assert (self.temp_dir / "participants.tsv").exists()
            assert (self.temp_dir / "participants.json").exists()

            # Verify subject data
            for subject_id in test_data.keys():
                subject_dir = self.temp_dir / f"sub-{subject_id}"
                assert subject_dir.exists()

                # Check for modality files
                for modality in ["eeg", "beh", "physio"]:
                    modality_dir = subject_dir / modality
                    if modality_dir.exists():
                        files = list(modality_dir.glob("*"))
                        assert len(files) > 0

    def test_export_apgi_to_bids_minimal_data(self):
        """Test APGI to BIDS export with minimal data."""
        # Test with empty data
        export_apgi_to_bids(data={}, bids_root=self.temp_dir)

        # Should still create basic structure
        assert (self.temp_dir / "dataset_description.json").exists()
        assert (self.temp_dir / "participants.json").exists()

    def test_export_apgi_to_bids_validation_errors(self):
        """Test APGI to BIDS export with validation warnings."""
        # Create data that will work but trigger validation warnings (no required files)
        test_data = {
            "01": {
                "eeg": {
                    "data": np.random.rand(2, 1000),
                    "channels": ["Fz", "Cz"],
                    "sampling_rate": 1000.0,
                }
            }
        }

        with patch("apgi_framework.export.bids_export.warnings") as mock_warnings:
            result_paths = export_apgi_to_bids(data=test_data, bids_root=self.temp_dir)

            # Should still export but have validation warnings
            assert isinstance(result_paths, dict)
            # Validation warnings should be issued (missing README, etc.)
            mock_warnings.warn.assert_called()
