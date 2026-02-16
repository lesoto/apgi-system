"""
Tests for Session Manager

Unit tests for SessionManager and SimulationSession classes.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, Callable

from api.services.session_manager import SessionManager, SimulationSession, SessionLifecycleState
from api.models.schemas import SessionCreateRequest


class TestSimulationSession:
    """Tests for SimulationSession class."""

    @pytest.fixture
    def session_config(self) -> Dict[str, Any]:
        """Sample session configuration."""
        return {
            "config_path": "config/default.yaml",
            "custom_config": None,
            "description": "Test session",
        }

    @pytest.fixture
    def simulation_session(self, session_config: Dict[str, Any]) -> SimulationSession:
        """Create a SimulationSession instance."""
        return SimulationSession("test-session-id", session_config)

    @pytest.mark.asyncio
    async def test_session_initialization(self, simulation_session: SimulationSession) -> None:
        """Test that session initializes correctly."""
        assert simulation_session.session_id == "test-session-id"
        assert simulation_session.state == SessionLifecycleState.CREATED
        assert simulation_session.is_running is False
        assert simulation_session.is_paused is False
        assert simulation_session.apgi_system is not None

    @pytest.mark.asyncio
    async def test_start_session(self, simulation_session: SimulationSession) -> None:
        """Test starting a session."""
        result = await simulation_session.start()

        assert result["session_id"] == "test-session-id"
        assert result["status"] == "running"
        assert simulation_session.state == SessionLifecycleState.RUNNING
        assert simulation_session.is_running is True

    @pytest.mark.asyncio
    async def test_start_already_running_raises_error(
        self, simulation_session: SimulationSession
    ) -> None:
        """Test that starting an already running session raises error."""
        await simulation_session.start()

        with pytest.raises(ValueError, match="already running"):
            await simulation_session.start()

    @pytest.mark.asyncio
    async def test_pause_session(self, simulation_session: SimulationSession) -> None:
        """Test pausing a running session."""
        await simulation_session.start()
        result = await simulation_session.pause()

        assert result["session_id"] == "test-session-id"
        assert result["status"] == "paused"
        assert simulation_session.state == SessionLifecycleState.PAUSED
        assert simulation_session.is_paused is True
        assert simulation_session.is_running is False

    @pytest.mark.asyncio
    async def test_pause_not_running_raises_error(
        self, simulation_session: SimulationSession
    ) -> None:
        """Test that pausing a non-running session raises error."""
        with pytest.raises(ValueError, match="not running"):
            await simulation_session.pause()

    @pytest.mark.asyncio
    async def test_stop_session(self, simulation_session: SimulationSession) -> None:
        """Test stopping a session."""
        await simulation_session.start()
        result = await simulation_session.stop()

        assert result["session_id"] == "test-session-id"
        assert result["status"] == "stopped"
        assert simulation_session.state == SessionLifecycleState.STOPPED
        assert simulation_session.is_running is False

    @pytest.mark.asyncio
    async def test_reset_session(self, simulation_session: SimulationSession) -> None:
        """Test resetting a session."""
        await simulation_session.start()
        result = await simulation_session.reset()

        assert result["session_id"] == "test-session-id"
        assert result["status"] == "created"
        assert simulation_session.state == SessionLifecycleState.CREATED
        assert simulation_session.is_running is False
        assert simulation_session.apgi_system.time == 0.0

    @pytest.mark.asyncio
    async def test_reset_idempotence(self, simulation_session: SimulationSession) -> None:
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
    async def test_pause_preserves_state(self, simulation_session: SimulationSession) -> None:
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
    async def test_get_state(self, simulation_session: SimulationSession) -> None:
        """Test getting session state."""
        state = await simulation_session.get_state()

        assert "time" in state
        assert "session_metadata" in state
        assert state["session_metadata"]["session_id"] == "test-session-id"
        assert state["session_metadata"]["state"] == "created"

    @pytest.mark.asyncio
    async def test_step_requires_running(self, simulation_session: SimulationSession) -> None:
        """Test that step requires session to be running."""
        with pytest.raises(ValueError, match="not running"):
            await simulation_session.step(np.random.randn(256))

    @pytest.mark.asyncio
    async def test_step_execution(self, simulation_session: SimulationSession) -> None:
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
    def mock_redis(self) -> AsyncMock:
        """Mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.setex = AsyncMock()
        redis_mock.delete = MagicMock()
        return redis_mock

    @pytest.fixture
    def mock_db_session(self) -> MagicMock:
        """Mock database session."""
        db_mock = MagicMock()
        db_mock.add = MagicMock()
        db_mock.commit = MagicMock()
        db_mock.rollback = MagicMock()
        db_mock.close = MagicMock()
        db_mock.execute = MagicMock()
        return db_mock

    @pytest.fixture
    def mock_db_factory(self, mock_db_session: MagicMock) -> Callable[[], MagicMock]:
        """Mock database session factory."""
        return lambda: mock_db_session

    @pytest.fixture
    def session_manager(
        self, mock_redis: AsyncMock, mock_db_factory: Callable[[], MagicMock]
    ) -> SessionManager:
        """Create SessionManager instance."""
        mock_redis.delete = AsyncMock()
        return SessionManager(mock_redis, mock_db_factory)

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager: SessionManager) -> None:
        """Test creating a new session."""
        request = SessionCreateRequest(
            config_path="config/default.yaml", description="Test session", custom_config=None
        )

        session_id = await session_manager.create_session(request)

        assert session_id is not None
        assert len(session_id) == 36  # UUID format
        assert session_id in session_manager.sessions

    @pytest.mark.asyncio
    async def test_get_session_from_cache(self, session_manager: SessionManager) -> None:
        """Test retrieving session from memory cache."""
        request = SessionCreateRequest(
            config_path="config/default.yaml",
            description="Cache test",
            custom_config=None,
        )
        session_id = await session_manager.create_session(request)

        # Get session (should come from cache)
        session = await session_manager.get_session(session_id)

        assert session.session_id == session_id
        assert session.state == SessionLifecycleState.CREATED

    @pytest.mark.asyncio
    async def test_get_nonexistent_session_raises_error(
        self, session_manager: SessionManager, mock_db_session: MagicMock
    ) -> None:
        """Test that getting non-existent session raises error."""
        # Mock database to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Use a valid UUID format but non-existent session
        nonexistent_id = "12345678-1234-5678-9012-123456789012"

        with pytest.raises(ValueError, match="not found"):
            await session_manager.get_session(nonexistent_id)

    @pytest.mark.asyncio
    async def test_delete_session(
        self, session_manager: SessionManager, mock_db_session: MagicMock
    ) -> None:
        """Test deleting a session."""
        request = SessionCreateRequest(
            config_path="config/default.yaml",
            description="Delete test",
            custom_config=None,
        )
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
        session_manager.redis.delete.assert_awaited_once()  # type: ignore

    @pytest.mark.asyncio
    async def test_session_creation_round_trip(self, session_manager: SessionManager) -> None:
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


class TestSessionManagerConcurrency:
    """Tests for concurrent session management operations."""

    @pytest.fixture
    def concurrent_session_manager(self) -> SessionManager:
        """Create SessionManager for concurrency testing."""
        from unittest.mock import AsyncMock, MagicMock

        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.setex = AsyncMock()
        redis_mock.delete = AsyncMock()

        db_mock = MagicMock()
        db_mock.add = MagicMock()
        db_mock.commit = MagicMock()
        db_mock.rollback = MagicMock()
        db_mock.close = MagicMock()
        db_mock.execute = MagicMock()

        return SessionManager(redis_mock, lambda: db_mock)

    @pytest.mark.asyncio
    async def test_concurrent_session_creation(
        self, concurrent_session_manager: SessionManager
    ) -> None:
        """Test creating multiple sessions concurrently."""
        import asyncio

        async def create_session(i: int) -> str:
            request = SessionCreateRequest(
                config_path="config/default.yaml",
                description=f"Concurrent session {i}",
                custom_config=None,
            )
            return await concurrent_session_manager.create_session(request)

        # Create 10 sessions concurrently
        tasks = [create_session(i) for i in range(10)]
        session_ids = await asyncio.gather(*tasks)

        # Verify all sessions were created
        assert len(session_ids) == 10
        assert len(set(session_ids)) == 10  # All IDs should be unique

        # Verify all sessions are in cache
        for session_id in session_ids:
            assert session_id in concurrent_session_manager.sessions

    @pytest.mark.asyncio
    async def test_concurrent_session_operations(
        self, concurrent_session_manager: SessionManager
    ) -> None:
        """Test concurrent operations on the same session."""
        import asyncio

        # Create a session
        request = SessionCreateRequest(
            config_path="config/default.yaml",
            description="Operations test",
            custom_config=None,
        )
        session_id = await concurrent_session_manager.create_session(request)
        session, _ = concurrent_session_manager.sessions[session_id]

        # Start the session first
        await session.start()

        async def perform_operation(operation_name: str) -> dict[str, Any]:
            if operation_name == "step":
                return await session.step(np.random.randn(256))
            elif operation_name == "pause":
                return await session.pause()
            elif operation_name == "get_state":
                return await session.get_state()
            return {}

        # Perform various operations concurrently (assuming session is already started)
        operations = ["get_state", "get_state", "step", "pause", "get_state", "get_state"]

        tasks = [perform_operation(op) for op in operations]

        # Should complete without race conditions
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that no exceptions occurred
        for result in results:
            assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_session_lifecycle_concurrency(
        self, concurrent_session_manager: SessionManager
    ) -> None:
        """Test session lifecycle operations under concurrent access."""
        import asyncio

        # Create multiple sessions
        session_ids = []
        for i in range(5):
            request = SessionCreateRequest(
                config_path="config/default.yaml",
                description=f"Lifecycle test {i}",
                custom_config=None,
            )
            session_id = await concurrent_session_manager.create_session(request)
            session_ids.append(session_id)

        async def lifecycle_test(session_id: str) -> str:
            session = await concurrent_session_manager.get_session(session_id)

            # Perform lifecycle operations
            await session.start()
            await session.step(np.random.randn(256))
            await session.pause()
            await session.stop()
            await session.reset()

            # Verify final state
            state = await session.get_state()
            return state["session_metadata"]["state"]

        # Run lifecycle tests concurrently
        tasks = [lifecycle_test(session_id) for session_id in session_ids]
        final_states = await asyncio.gather(*tasks)

        # All sessions should end in CREATED state after reset
        assert all(state == "created" for state in final_states)

    @pytest.mark.asyncio
    async def test_cache_consistency_under_concurrency(
        self, concurrent_session_manager: SessionManager
    ) -> None:
        """Test that cache remains consistent under concurrent access."""
        import asyncio

        # Create a session
        request = SessionCreateRequest(
            config_path="config/default.yaml",
            description="Consistency test",
            custom_config=None,
        )
        session_id = await concurrent_session_manager.create_session(request)

        async def access_session() -> None:
            # Get session multiple times
            for _ in range(10):
                session = await concurrent_session_manager.get_session(session_id)
                assert session.session_id == session_id
                # Small delay to increase chance of interleaving
                await asyncio.sleep(0.001)

        # Run multiple concurrent accessors
        tasks = [access_session() for _ in range(5)]
        await asyncio.gather(*tasks)

        # Session should still be accessible
        session = await concurrent_session_manager.get_session(session_id)
        assert session is not None

    @pytest.mark.asyncio
    async def test_session_deletion_concurrency(
        self, concurrent_session_manager: SessionManager
    ) -> None:
        """Test concurrent session deletion operations."""
        import asyncio

        # Create multiple sessions
        session_ids = []
        for i in range(3):
            request = SessionCreateRequest(
                config_path="config/default.yaml",
                description=f"Deletion test {i}",
                custom_config=None,
            )
            session_id = await concurrent_session_manager.create_session(request)
            session_ids.append(session_id)

        async def delete_session(session_id: str) -> str:
            try:
                await concurrent_session_manager.delete_session(session_id)
                return "deleted"
            except ValueError:
                return "not_found"

        # Try to delete the same session concurrently
        target_session = session_ids[0]
        tasks = [delete_session(target_session) for _ in range(5)]

        results = await asyncio.gather(*tasks)

        # Only one deletion should succeed, others should get "not found"
        delete_count = sum(1 for result in results if result == "deleted")
        not_found_count = sum(1 for result in results if result == "not_found")

        assert delete_count == 1
        assert not_found_count == 4

        # Session should be removed from cache
        assert target_session not in concurrent_session_manager.sessions

    @pytest.mark.asyncio
    async def test_redis_cache_concurrency(
        self, concurrent_session_manager: SessionManager
    ) -> None:
        """Test Redis cache operations under concurrency."""
        import asyncio

        # Mock Redis to simulate some latency
        async def delayed_get(key: str) -> None:
            await asyncio.sleep(0.01)
            return None

        async def delayed_setex(key: str, time: int, value: Any) -> None:
            await asyncio.sleep(0.01)

        # Assign to mock methods
        setattr(concurrent_session_manager.redis, "get", delayed_get)
        setattr(concurrent_session_manager.redis, "setex", delayed_setex)

        async def create_and_access() -> str:
            request = SessionCreateRequest(
                config_path="config/default.yaml",
                description="Redis test",
                custom_config=None,
            )
            session_id = await concurrent_session_manager.create_session(request)

            # Immediately try to access the session
            session = await concurrent_session_manager.get_session(session_id)
            return session.session_id

        # Run concurrent creation and access
        tasks = [create_and_access() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All operations should succeed
        assert len(results) == 10
        assert len(set(results)) == 10  # All session IDs unique

    @pytest.mark.asyncio
    async def test_simulation_step_concurrency(
        self, concurrent_session_manager: SessionManager
    ) -> None:
        """Test concurrent simulation steps within a session."""
        import asyncio

        # Create and start a session
        request = SessionCreateRequest(
            config_path="config/default.yaml",
            description="Concurrency step test",
            custom_config=None,
        )
        session_id = await concurrent_session_manager.create_session(request)
        session = await concurrent_session_manager.get_session(session_id)
        await session.start()

        async def simulation_step(step_id: int) -> float:
            input_data = np.random.randn(256)
            result = await session.step(input_data)
            return result["time"]

        # Run multiple simulation steps concurrently
        tasks = [simulation_step(i) for i in range(20)]
        timestamps = await asyncio.gather(*tasks)

        # All timestamps should be valid and increasing
        assert all(t > 0 for t in timestamps)
        # Note: Due to concurrency, exact ordering may vary, but all should be positive

    @pytest.mark.asyncio
    async def test_session_manager_thread_safety(
        self, concurrent_session_manager: SessionManager
    ) -> None:
        """Test overall thread safety of SessionManager."""
        import asyncio
        import threading

        results = []
        errors = []

        def run_async_test() -> None:
            """Run async test in a thread."""

            async def test() -> None:
                try:
                    # Create session
                    request = SessionCreateRequest(
                        config_path="config/default.yaml",
                        description="Thread test",
                        custom_config=None,
                    )
                    session_id = await concurrent_session_manager.create_session(request)

                    # Get session
                    session = await concurrent_session_manager.get_session(session_id)

                    # Perform operations
                    await session.start()
                    await session.step(np.random.randn(256))
                    state = await session.get_state()

                    results.append(
                        {
                            "session_id": session_id,
                            "time": state["time"],
                            "state": state["session_metadata"]["state"],
                        }
                    )
                except Exception as e:
                    errors.append(str(e))

            # Run the async test
            asyncio.run(test())

        # Run multiple threads concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=run_async_test)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0

        # Verify results
        assert len(results) == 5
        for result in results:
            assert result["time"] > 0
            assert result["state"] == "running"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
