"""
Tests for Session Manager

Unit tests for SessionManager and SimulationSession classes.
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime

from api.services.session_manager import SessionManager, SimulationSession, SessionLifecycleState
from api.models.schemas import SessionCreateRequest


class TestSimulationSession:
    """Tests for SimulationSession class."""

    @pytest.fixture
    def session_config(self):
        """Sample session configuration."""
        return {
            "config_path": "config/default.yaml",
            "custom_config": None,
            "description": "Test session",
        }

    @pytest.fixture
    def simulation_session(self, session_config):
        """Create a SimulationSession instance."""
        return SimulationSession("test-session-id", session_config)

    @pytest.mark.asyncio
    async def test_session_initialization(self, simulation_session):
        """Test that session initializes correctly."""
        assert simulation_session.session_id == "test-session-id"
        assert simulation_session.state == SessionLifecycleState.CREATED
        assert simulation_session.is_running is False
        assert simulation_session.is_paused is False
        assert simulation_session.apgi_system is not None

    @pytest.mark.asyncio
    async def test_start_session(self, simulation_session):
        """Test starting a session."""
        result = await simulation_session.start()

        assert result["session_id"] == "test-session-id"
        assert result["status"] == "running"
        assert simulation_session.state == SessionLifecycleState.RUNNING
        assert simulation_session.is_running is True

    @pytest.mark.asyncio
    async def test_start_already_running_raises_error(self, simulation_session):
        """Test that starting an already running session raises error."""
        await simulation_session.start()

        with pytest.raises(ValueError, match="already running"):
            await simulation_session.start()

    @pytest.mark.asyncio
    async def test_pause_session(self, simulation_session):
        """Test pausing a running session."""
        await simulation_session.start()
        result = await simulation_session.pause()

        assert result["session_id"] == "test-session-id"
        assert result["status"] == "paused"
        assert simulation_session.state == SessionLifecycleState.PAUSED
        assert simulation_session.is_paused is True
        assert simulation_session.is_running is False

    @pytest.mark.asyncio
    async def test_pause_not_running_raises_error(self, simulation_session):
        """Test that pausing a non-running session raises error."""
        with pytest.raises(ValueError, match="not running"):
            await simulation_session.pause()

    @pytest.mark.asyncio
    async def test_stop_session(self, simulation_session):
        """Test stopping a session."""
        await simulation_session.start()
        result = await simulation_session.stop()

        assert result["session_id"] == "test-session-id"
        assert result["status"] == "stopped"
        assert simulation_session.state == SessionLifecycleState.STOPPED
        assert simulation_session.is_running is False

    @pytest.mark.asyncio
    async def test_reset_session(self, simulation_session):
        """Test resetting a session."""
        await simulation_session.start()
        result = await simulation_session.reset()

        assert result["session_id"] == "test-session-id"
        assert result["status"] == "created"
        assert simulation_session.state == SessionLifecycleState.CREATED
        assert simulation_session.is_running is False
        assert simulation_session.apgi_system.time == 0.0

    @pytest.mark.asyncio
    async def test_reset_idempotence(self, simulation_session):
        """Test that resetting twice produces the same result."""
        # First reset
        result1 = await simulation_session.reset()
        state1 = await simulation_session.get_state()

        # Second reset
        result2 = await simulation_session.reset()
        state2 = await simulation_session.get_state()

        # Both should be in CREATED state with time = 0
        assert result1["status"] == result2["status"] == "created"
        assert state1["time"] == state2["time"] == 0.0

    @pytest.mark.asyncio
    async def test_pause_preserves_state(self, simulation_session):
        """Test that pausing preserves the current state."""
        await simulation_session.start()

        # Run a few steps
        for _ in range(5):
            await simulation_session.step(np.random.randn(256))

        # Get state before pause
        state_before = await simulation_session.get_state()
        time_before = state_before["time"]

        # Pause
        await simulation_session.pause()

        # Get state after pause
        state_after = await simulation_session.get_state()
        time_after = state_after["time"]

        # Time should be preserved
        assert time_before == time_after

    @pytest.mark.asyncio
    async def test_get_state(self, simulation_session):
        """Test getting session state."""
        state = await simulation_session.get_state()

        assert "time" in state
        assert "session_metadata" in state
        assert state["session_metadata"]["session_id"] == "test-session-id"
        assert state["session_metadata"]["state"] == "created"

    @pytest.mark.asyncio
    async def test_step_requires_running(self, simulation_session):
        """Test that step requires session to be running."""
        with pytest.raises(ValueError, match="not running"):
            await simulation_session.step(np.random.randn(256))

    @pytest.mark.asyncio
    async def test_step_execution(self, simulation_session):
        """Test executing a simulation step."""
        await simulation_session.start()

        extero_input = np.random.randn(256)
        state = await simulation_session.step(extero_input)

        assert "time" in state
        assert "ignition" in state
        assert state["time"] > 0


class TestSessionManager:
    """Tests for SessionManager class."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.setex = AsyncMock()
        redis_mock.delete = AsyncMock()
        return redis_mock

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        db_mock = MagicMock()
        db_mock.add = MagicMock()
        db_mock.commit = MagicMock()
        db_mock.rollback = MagicMock()
        db_mock.close = MagicMock()
        db_mock.execute = MagicMock()
        return db_mock

    @pytest.fixture
    def mock_db_factory(self, mock_db_session):
        """Mock database session factory."""
        return lambda: mock_db_session

    @pytest.fixture
    def session_manager(self, mock_redis, mock_db_factory):
        """Create SessionManager instance."""
        return SessionManager(mock_redis, mock_db_factory)

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Test creating a new session."""
        request = SessionCreateRequest(
            config_path="config/default.yaml", description="Test session"
        )

        session_id = await session_manager.create_session(request)

        assert session_id is not None
        assert len(session_id) == 36  # UUID format
        assert session_id in session_manager.sessions

    @pytest.mark.asyncio
    async def test_get_session_from_cache(self, session_manager):
        """Test retrieving session from memory cache."""
        request = SessionCreateRequest(config_path="config/default.yaml")
        session_id = await session_manager.create_session(request)

        # Get session (should come from cache)
        session = await session_manager.get_session(session_id)

        assert session.session_id == session_id
        assert session.state == SessionLifecycleState.CREATED

    @pytest.mark.asyncio
    async def test_get_nonexistent_session_raises_error(self, session_manager, mock_db_session):
        """Test that getting non-existent session raises error."""
        # Mock database to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await session_manager.get_session("nonexistent-id")

    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager, mock_db_session):
        """Test deleting a session."""
        request = SessionCreateRequest(config_path="config/default.yaml")
        session_id = await session_manager.create_session(request)

        # Mock database query
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_db_session.execute.return_value = mock_result

        await session_manager.delete_session(session_id)

        # Session should be removed from cache
        assert session_id not in session_manager.sessions

        # Redis delete should be called
        session_manager.redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_creation_round_trip(self, session_manager):
        """Test creating and retrieving a session."""
        request = SessionCreateRequest(
            config_path="config/default.yaml",
            custom_config={"system": {"timestep_ms": 15.0}},
            description="Round trip test",
        )

        # Create session
        session_id = await session_manager.create_session(request)

        # Retrieve session
        session = await session_manager.get_session(session_id)

        # Verify configuration matches
        assert session.config["config_path"] == "config/default.yaml"
        assert session.config["description"] == "Round trip test"
        assert session.config["custom_config"]["system"]["timestep_ms"] == 15.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
