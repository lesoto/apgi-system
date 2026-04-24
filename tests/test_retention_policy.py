"""
Retention Policy Enforcement Tests

Validates GDPR Article 5(1)(e) storage limitation compliance.
Tests automated data purging based on retention policies.
"""

from datetime import datetime, timedelta
from typing import List, Tuple

import pytest

from api.compliance.data_minimization import (
    DataMinimizationManager,
    RetentionPolicy,
    get_minimization_manager,
)


class TestRetentionPolicy:
    """Test retention policy enforcement."""

    @pytest.fixture
    def manager(self) -> DataMinimizationManager:
        """Create a fresh minimization manager for testing."""
        return DataMinimizationManager()

    def test_register_retention_policy(self, manager: DataMinimizationManager):
        """Test that retention policies can be registered."""
        policy = RetentionPolicy(
            data_type="test_data",
            retention_days=30,
            purpose="testing",
            legal_basis="consent",
        )

        manager.register_retention_policy(policy)

        assert "test_data" in manager._retention_policies
        assert manager._retention_policies["test_data"].retention_days == 30

    def test_check_retention_expired_true(self, manager: DataMinimizationManager):
        """Test that expired retention is detected."""
        policy = RetentionPolicy(
            data_type="session_data",
            retention_days=7,
            purpose="research",
            legal_basis="consent",
        )

        manager.register_retention_policy(policy)

        # Create a record from 10 days ago
        created_at = datetime.now() - timedelta(days=10)

        expired, _ = manager.check_retention_expired("session_data", created_at)

        assert expired is True

    def test_check_retention_expired_false(self, manager: DataMinimizationManager):
        """Test that non-expired retention is detected."""
        policy = RetentionPolicy(
            data_type="session_data",
            retention_days=30,
            purpose="research",
            legal_basis="consent",
        )

        manager.register_retention_policy(policy)

        # Create a record from 5 days ago
        created_at = datetime.now() - timedelta(days=5)

        expired, _ = manager.check_retention_expired("session_data", created_at)

        assert expired is False

    def test_get_purge_candidates(self, manager: DataMinimizationManager):
        """Test that purge candidates are correctly identified."""
        policy = RetentionPolicy(
            data_type="export_logs",
            retention_days=365,
            purpose="audit",
            legal_basis="legal_obligation",
        )

        manager.register_retention_policy(policy)

        # Create records with various ages
        records: List[Tuple[str, datetime]] = [
            ("record_1", datetime.now() - timedelta(days=400)),  # Expired
            ("record_2", datetime.now() - timedelta(days=500)),  # Expired
            ("record_3", datetime.now() - timedelta(days=30)),  # Not expired
            ("record_4", datetime.now() - timedelta(days=366)),  # Expired
        ]

        candidates = manager.get_purge_candidates("export_logs", records)

        assert len(candidates) == 3
        assert "record_1" in candidates
        assert "record_2" in candidates
        assert "record_4" in candidates
        assert "record_3" not in candidates

    def test_no_policy_returns_no_expiration(self, manager: DataMinimizationManager):
        """Test that data without a policy is not flagged."""
        created_at = datetime.now() - timedelta(days=1000)

        expired, policy = manager.check_retention_expired("unknown_type", created_at)

        assert expired is False
        assert policy is None

    def test_retention_policy_with_extension(self, manager: DataMinimizationManager):
        """Test retention policy with extension capability."""
        policy = RetentionPolicy(
            data_type="research_data",
            retention_days=2555,  # 7 years
            purpose="longitudinal_study",
            legal_basis="consent",
            can_extend=True,
            extension_reason="Long-term study requires extended retention",
        )

        manager.register_retention_policy(policy)

        # Check that extension info is preserved
        retrieved_policy = manager._retention_policies["research_data"]
        assert retrieved_policy.can_extend is True
        assert retrieved_policy.extension_reason == "Long-term study requires extended retention"

    def test_generate_data_inventory(self, manager: DataMinimizationManager):
        """Test that data inventory is generated correctly."""
        policy1 = RetentionPolicy(
            data_type="sessions",
            retention_days=2555,
            purpose="research",
            legal_basis="consent",
        )
        policy2 = RetentionPolicy(
            data_type="exports",
            retention_days=365,
            purpose="audit",
            legal_basis="legal_obligation",
        )

        manager.register_retention_policy(policy1)
        manager.register_retention_policy(policy2)

        inventory = manager.generate_data_inventory()

        assert "retention_policies" in inventory
        assert "sessions" in inventory["retention_policies"]
        assert "exports" in inventory["retention_policies"]
        assert inventory["retention_policies"]["sessions"]["retention_days"] == 2555
        assert inventory["retention_policies"]["exports"]["retention_days"] == 365

    def test_global_minimization_manager_singleton(self):
        """Test that the global manager is a singleton."""
        manager1 = get_minimization_manager()
        manager2 = get_minimization_manager()

        assert manager1 is manager2

    def test_edge_case_zero_retention(self, manager: DataMinimizationManager):
        """Test edge case with zero retention days."""
        policy = RetentionPolicy(
            data_type="temp_data",
            retention_days=0,
            purpose="temporary",
            legal_basis="consent",
        )

        manager.register_retention_policy(policy)

        # Any record created in the past should be expired
        created_at = datetime.now() - timedelta(seconds=1)

        expired, _ = manager.check_retention_expired("temp_data", created_at)

        assert expired is True

    def test_edge_case_future_creation_date(self, manager: DataMinimizationManager):
        """Test edge case with future creation date."""
        policy = RetentionPolicy(
            data_type="future_data",
            retention_days=30,
            purpose="testing",
            legal_basis="consent",
        )

        manager.register_retention_policy(policy)

        # Future creation date should not be expired
        created_at = datetime.now() + timedelta(days=10)

        expired, _ = manager.check_retention_expired("future_data", created_at)

        assert expired is False


class TestRetentionPolicyIntegration:
    """Integration tests for retention policy enforcement."""

    def test_default_retention_policies_exist(self):
        """Test that default retention policies are registered."""
        from api.middleware.compliance import DEFAULT_RETENTION_POLICIES

        assert len(DEFAULT_RETENTION_POLICIES) >= 3

        # Check session data policy
        session_policy = next(
            (p for p in DEFAULT_RETENTION_POLICIES if p.data_type == "session_data"),
            None,
        )
        assert session_policy is not None
        assert session_policy.retention_days == 2555  # 7 years

        # Check export logs policy
        export_policy = next(
            (p for p in DEFAULT_RETENTION_POLICIES if p.data_type == "export_logs"),
            None,
        )
        assert export_policy is not None
        assert export_policy.retention_days == 365  # 1 year


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
