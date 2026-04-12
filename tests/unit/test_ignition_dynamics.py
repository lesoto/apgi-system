"""
Unit tests for ignition dynamics components.

Tests specific threshold scenarios, broadcasting mechanics, and temporal orchestration
for IgnitionThreshold, GlobalWorkspace, and IgnitionTimeline components.
"""

from typing import Any, Dict

import numpy as np
import pytest

from apgi_system.ignition.global_workspace import BroadcastContent, GlobalWorkspace, WorkspaceState

# from apgi_system.ignition.temporal_dynamics import IgnitionTimeline, TimelinePhase  # Module removed in cleanup
from apgi_system.ignition.threshold import IgnitionThreshold


class TestIgnitionThreshold:
    """Unit tests for IgnitionThreshold component."""

    @pytest.fixture
    def threshold_config(self) -> Dict[str, Any]:
        """Configuration for threshold tests."""
        return {
            "ignition": {
                "baseline_threshold": 2.0,
                "threshold_range": [1.0, 5.0],
                "sigmoid_alpha": 5.0,
                "refractory_period_ms": 200,
            }
        }

    @pytest.fixture
    def threshold(self, threshold_config: Dict[str, Any]) -> IgnitionThreshold:
        """Create IgnitionThreshold instance."""
        return IgnitionThreshold(threshold_config)

    def test_initialization(self, threshold) -> None:
        """Test proper initialization of IgnitionThreshold."""
        assert threshold.baseline_threshold == 2.0
        assert threshold.threshold_range == [1.0, 5.0]
        assert threshold.sigmoid_alpha == 5.0
        assert threshold.refractory_period_ms == 200
        assert threshold.current_threshold == 2.0
        assert threshold.current_signal == 0.0
        assert threshold.metabolic_reserves == 1.0
        assert threshold.allostatic_load == 0.0
        assert len(threshold.recent_ignitions) == 0

    def test_basic_signal_computation(self, threshold) -> None:
        """Test basic ignition signal computation."""
        extero_error = np.array([1.0, 2.0, 1.5])
        intero_error = np.array([0.5, 0.3])

        ignited, components = threshold.compute_ignition_signal(
            extero_error=extero_error,
            extero_precision=1.5,
            intero_error=intero_error,
            intero_precision=1.0,
            somatic_marker_gain=1.2,
            current_time=100.0,
        )

        # Check signal components
        expected_extero = 1.5 * np.linalg.norm(extero_error)
        expected_intero = 1.0 * 1.2 * np.linalg.norm(intero_error)
        expected_total = expected_extero + expected_intero

        assert abs(components["extero_signal"] - expected_extero) < 1e-6
        assert abs(components["intero_signal"] - expected_intero) < 1e-6
        assert abs(components["total_signal"] - expected_total) < 1e-6
        assert components["threshold"] == 2.0  # Baseline threshold
        assert 0 <= components["ignition_probability"] <= 1
        assert components["somatic_marker_gain"] == 1.2
        assert isinstance(ignited, bool)

    def test_threshold_exceeding_ignition(self, threshold) -> None:
        """Test ignition when signal exceeds threshold."""
        # Create large error to exceed threshold
        extero_error = np.array([3.0, 4.0, 2.0])  # Large error
        intero_error = np.array([1.0, 1.5])

        # Multiple attempts to account for stochastic nature
        ignition_occurred = False
        for _ in range(50):  # Try multiple times
            ignited, components = threshold.compute_ignition_signal(
                extero_error=extero_error,
                extero_precision=2.0,
                intero_error=intero_error,
                intero_precision=1.5,
                current_time=100.0,
            )
            if ignited:
                ignition_occurred = True
                break

        # With such large signals, ignition should occur eventually
        assert ignition_occurred, "Large signal should eventually trigger ignition"

    def test_refractory_period_enforcement(self, threshold) -> None:
        """Test that refractory period prevents immediate re-ignition."""
        # Create large error that should trigger ignition
        extero_error = np.array([5.0, 5.0])
        intero_error = np.array([2.0])

        # First ignition
        ignited1, _ = threshold.compute_ignition_signal(
            extero_error=extero_error,
            extero_precision=3.0,
            intero_error=intero_error,
            intero_precision=2.0,
            current_time=100.0,
        )

        # If first attempt didn't ignite, keep trying until it does
        current_time = 100.0
        while not ignited1:
            current_time += 1.0
            ignited1, _ = threshold.compute_ignition_signal(
                extero_error=extero_error,
                extero_precision=3.0,
                intero_error=intero_error,
                intero_precision=2.0,
                current_time=current_time,
            )

        # Immediate second attempt (within refractory period)
        ignited2, _ = threshold.compute_ignition_signal(
            extero_error=extero_error,
            extero_precision=3.0,
            intero_error=intero_error,
            intero_precision=2.0,
            current_time=current_time + 50.0,  # 50ms later, within 200ms refractory
        )

        # Should not ignite due to refractory period
        assert not ignited2, "Should not ignite within refractory period"

        # After refractory period
        ignited3, _ = threshold.compute_ignition_signal(
            extero_error=extero_error,
            extero_precision=3.0,
            intero_error=intero_error,
            intero_precision=2.0,
            current_time=current_time + 250.0,  # 250ms later, after refractory
        )

        # May ignite again (stochastic, but not blocked by refractory period)
        assert isinstance(ignited3, bool)

    def test_metabolic_state_modulation(self, threshold) -> None:
        """Test threshold modulation by metabolic state."""
        # Test with full reserves
        threshold.update_metabolic_state(reserves=1.0, allostatic_load=0.0)
        threshold._update_threshold(100.0)
        full_reserves_threshold = threshold.current_threshold

        # Test with depleted reserves
        threshold.update_metabolic_state(reserves=0.2, allostatic_load=0.0)
        threshold._update_threshold(100.0)
        depleted_reserves_threshold = threshold.current_threshold

        # Depleted reserves should increase threshold
        assert depleted_reserves_threshold > full_reserves_threshold

        # Test with high allostatic load
        threshold.update_metabolic_state(reserves=1.0, allostatic_load=0.8)
        threshold._update_threshold(100.0)
        high_load_threshold = threshold.current_threshold

        # High load should increase threshold
        assert high_load_threshold > full_reserves_threshold

    def test_somatic_marker_gain_modulation(self, threshold):
        """Test somatic marker gain effects on interoceptive signal."""
        extero_error = np.array([1.0])
        intero_error = np.array([1.0])

        # Test with low gain (aversive context)
        _, components_low = threshold.compute_ignition_signal(
            extero_error=extero_error,
            extero_precision=1.0,
            intero_error=intero_error,
            intero_precision=1.0,
            somatic_marker_gain=0.6,
            current_time=100.0,
        )

        # Test with high gain (appetitive context)
        _, components_high = threshold.compute_ignition_signal(
            extero_error=extero_error,
            extero_precision=1.0,
            intero_error=intero_error,
            intero_precision=1.0,
            somatic_marker_gain=1.8,
            current_time=200.0,
        )

        # Higher gain should produce higher interoceptive signal
        assert components_high["intero_signal"] > components_low["intero_signal"]
        assert components_high["total_signal"] > components_low["total_signal"]

    def test_input_validation(self, threshold) -> None:
        """Test input validation for compute_ignition_signal."""
        valid_extero = np.array([1.0, 2.0])
        valid_intero = np.array([0.5])

        # Test invalid extero_error type
        with pytest.raises(TypeError):
            threshold.compute_ignition_signal(
                extero_error=[1.0, 2.0],  # List instead of array
                extero_precision=1.0,
                intero_error=valid_intero,
                intero_precision=1.0,
            )

        # Test negative precision
        with pytest.raises(ValueError):
            threshold.compute_ignition_signal(
                extero_error=valid_extero,
                extero_precision=-1.0,  # Negative
                intero_error=valid_intero,
                intero_precision=1.0,
            )

        # Test somatic marker gain out of range
        with pytest.raises(ValueError):
            threshold.compute_ignition_signal(
                extero_error=valid_extero,
                extero_precision=1.0,
                intero_error=valid_intero,
                intero_precision=1.0,
                somatic_marker_gain=3.0,  # Out of range [0.5, 2.0]
            )

    def test_statistics_computation(self, threshold) -> None:
        """Test statistics computation."""
        # Initially empty
        stats = threshold.get_statistics()
        assert stats["mean_signal"] == 0.0
        assert stats["recent_ignitions"] == 0

        # Add some history
        extero_error = np.array([1.0, 1.5])
        intero_error = np.array([0.5])

        for i in range(10):
            threshold.compute_ignition_signal(
                extero_error=extero_error,
                extero_precision=1.0,
                intero_error=intero_error,
                intero_precision=1.0,
                current_time=float(i * 10),
            )

        stats = threshold.get_statistics()
        assert stats["mean_signal"] > 0
        assert "std_signal" in stats
        assert "mean_threshold" in stats
        assert "ignition_rate" in stats

    def test_reset_functionality(self, threshold: IgnitionThreshold) -> None:
        """Test reset restores initial state."""
        # Modify state
        threshold.metabolic_reserves = 0.5
        threshold.allostatic_load = 0.3
        threshold.current_signal = 5.0
        threshold.recent_ignitions.append({"time": 100, "signal": 3.0})

        # Reset
        threshold.reset()

        # Check restoration
        assert threshold.current_threshold == threshold.baseline_threshold
        assert threshold.current_signal == 0.0
        assert threshold.metabolic_reserves == 1.0
        assert threshold.allostatic_load == 0.0
        assert len(threshold.recent_ignitions) == 0
        assert len(threshold.signal_history) == 0


class TestGlobalWorkspace:
    """Unit tests for GlobalWorkspace component."""

    @pytest.fixture
    def workspace_config(self) -> Dict[str, Any]:
        """Configuration for workspace tests."""
        return {"ignition": {"amplification_duration_ms": 300}}

    @pytest.fixture
    def workspace(self, workspace_config: Dict[str, Any]) -> GlobalWorkspace:
        """Create GlobalWorkspace instance."""
        return GlobalWorkspace(workspace_config)

    def test_initialization(self, workspace: GlobalWorkspace) -> None:
        """Test proper initialization of GlobalWorkspace."""
        assert workspace.amplification_duration_ms == 300
        assert workspace.state == WorkspaceState.IDLE
        assert workspace.current_content is None
        assert workspace.state_time == 0.0
        assert len(workspace.competing_contents) == 0
        assert len(workspace.subscribers) == 0

    def test_idle_to_igniting_transition(self, workspace: GlobalWorkspace) -> None:
        """Test transition from IDLE to IGNITING state."""
        # Add candidate content
        candidate = np.random.randn(256)
        state = workspace.update(
            ignition_occurred=False,
            candidate_content=candidate,
            source="visual_cortex",
            priority=1.5,
        )

        assert state["state"] == "idle"
        assert state["num_competitors"] == 1

        # Trigger ignition
        state = workspace.update(ignition_occurred=True)

        assert state["state"] == "igniting"
        assert state["state_time"] == 0.0

    def test_competition_resolution(self, workspace) -> None:
        """Test winner selection from competing contents."""
        # Add multiple candidates with different priorities
        candidates = [
            (np.random.randn(256), "source1", 1.0),
            (np.random.randn(256), "source2", 2.0),  # Higher priority
            (np.random.randn(256), "source3", 0.5),
        ]

        for content, source, priority in candidates:
            workspace.update(
                ignition_occurred=False, candidate_content=content, source=source, priority=priority
            )

        # Trigger ignition and progress through competition
        workspace.update(ignition_occurred=True)

        # Progress through igniting phase (50ms)
        for _ in range(60):  # 60ms to ensure transition
            state = workspace.update(ignition_occurred=False, dt=1.0)

        # Should have transitioned to broadcasting with a winner
        assert state["state"] == "broadcasting"
        assert "broadcast_content" in state
        # Higher priority should have better chance of winning (though stochastic)

    def test_broadcasting_phase(self, workspace: GlobalWorkspace) -> None:
        """Test broadcasting phase mechanics."""
        # Set up and trigger ignition
        candidate = np.random.randn(256)
        workspace.update(ignition_occurred=False, candidate_content=candidate, source="test_source")
        workspace.update(ignition_occurred=True)

        # Progress to broadcasting
        for _ in range(60):
            workspace.update(ignition_occurred=False, dt=1.0)

        # Should be broadcasting
        state = workspace.update(ignition_occurred=False, dt=1.0)
        assert state["state"] == "broadcasting"
        assert state["is_broadcasting"]
        assert state["is_reportable"]

    def test_subscriber_notification(self, workspace: GlobalWorkspace) -> None:
        """Test subscriber notification during broadcasting."""
        # Set up subscriber
        received_content = []

        def test_subscriber(content: BroadcastContent) -> None:
            received_content.append(content)

        workspace.subscribe(test_subscriber)

        # Trigger ignition and progress to broadcasting
        candidate = np.random.randn(256)
        workspace.update(ignition_occurred=False, candidate_content=candidate, source="test_source")
        workspace.update(ignition_occurred=True)

        # Progress through states
        for _ in range(100):  # Enough to reach broadcasting
            workspace.update(ignition_occurred=False, dt=1.0)

        # Should have received broadcasts
        assert len(received_content) > 0
        assert isinstance(received_content[0], BroadcastContent)

    def test_state_machine_progression(self, workspace: GlobalWorkspace) -> None:
        """Test complete state machine progression."""
        # Start in IDLE
        assert workspace.state == WorkspaceState.IDLE

        # Add content and trigger ignition
        candidate = np.random.randn(256)
        workspace.update(ignition_occurred=False, candidate_content=candidate)
        workspace.update(ignition_occurred=True)

        # Should be IGNITING
        assert workspace.state == WorkspaceState.IGNITING  # type: ignore[comparison-overlap]

        # Progress through IGNITING (50ms)
        for _ in range(60):  # type: ignore[unreachable]
            workspace.update(ignition_occurred=False, dt=1.0)
            if workspace.state != WorkspaceState.IGNITING:
                break

        # Should be BROADCASTING
        assert workspace.state == WorkspaceState.BROADCASTING

        # Progress through BROADCASTING (300ms)
        for _ in range(350):
            workspace.update(ignition_occurred=False, dt=1.0)

        # Should be MAINTAINING
        assert workspace.state == WorkspaceState.MAINTAINING

        # Progress through MAINTAINING (1000ms)
        for _ in range(1100):
            workspace.update(ignition_occurred=False, dt=1.0)

        # Should be FADING
        assert workspace.state == WorkspaceState.FADING

        # Progress through FADING (200ms)
        for _ in range(250):
            workspace.update(ignition_occurred=False, dt=1.0)

        # Should return to IDLE
        assert workspace.state == WorkspaceState.IDLE

    def test_reportability_timing(self, workspace):
        """Test reportability during appropriate phases."""
        # Set up ignition
        candidate = np.random.randn(256)
        workspace.update(ignition_occurred=False, candidate_content=candidate)
        workspace.update(ignition_occurred=True)

        # Not reportable during IGNITING
        assert not workspace.is_reportable()

        # Progress to BROADCASTING
        for _ in range(60):
            workspace.update(ignition_occurred=False, dt=1.0)

        # Should be reportable during BROADCASTING
        assert workspace.is_reportable()

        # Progress to MAINTAINING
        for _ in range(350):
            workspace.update(ignition_occurred=False, dt=1.0)

        # Should still be reportable during MAINTAINING
        assert workspace.is_reportable()

        # Progress to FADING
        for _ in range(1100):
            workspace.update(ignition_occurred=False, dt=1.0)

        # Should not be reportable during FADING
        assert not workspace.is_reportable()

    def test_input_validation(self, workspace):
        """Test input validation for update method."""
        # Test invalid ignition_occurred type
        with pytest.raises(TypeError):
            workspace.update(ignition_occurred="true")  # String instead of bool

        # Test invalid candidate_content type
        with pytest.raises(TypeError):
            workspace.update(
                ignition_occurred=False, candidate_content=[1, 2, 3]  # List instead of array
            )

        # Test invalid source type
        with pytest.raises(TypeError):
            workspace.update(ignition_occurred=False, source=123)  # Number instead of string

        # Test negative priority
        with pytest.raises(ValueError):
            workspace.update(ignition_occurred=False, priority=-1.0)  # Negative priority

    def test_reset_functionality(self, workspace):
        """Test reset restores initial state."""
        # Modify state
        workspace.state = WorkspaceState.BROADCASTING
        workspace.state_time = 100.0
        workspace.current_content = BroadcastContent(
            content=np.random.randn(256), ignition_time=0.0, source="test"
        )
        workspace.competing_contents.append(workspace.current_content)
        workspace.subscribe(lambda x: None)

        # Reset
        workspace.reset()

        # Check restoration
        assert workspace.state == WorkspaceState.IDLE
        assert workspace.current_content is None
        assert workspace.state_time == 0.0
        assert len(workspace.competing_contents) == 0
        assert len(workspace.subscribers) == 0
