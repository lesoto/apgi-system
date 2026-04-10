"""
Session Manager

Manages APGI simulation sessions with Redis caching and database persistence.
"""

import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict

# from sqlalchemy.orm import Session

import redis.asyncio as redis
from sqlalchemy import select

from api.database.models import Session as SessionModel
from api.database.models import SessionState

from api.exceptions import ServiceUnavailableError
from sqlalchemy.orm import Session as SessionLocal

# Import circuit breaker utilities
from utils.circuit_breaker_utils import (
    circuit_breaker,
    CircuitBreakerException,
)

from apgi_system.system import APGISystem
from api.models.schemas import SessionCreateRequest

logger = logging.getLogger(__name__)

# UUID validation pattern
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def validate_session_id(session_id: str) -> str:
    """
    Validate session ID format to prevent SQL injection.

    Args:
        session_id: Session identifier to validate

    Returns:
        Validated session ID

    Raises:
        ValueError: If session ID is not a valid UUID
    """
    if not session_id or not isinstance(session_id, str):
        raise ValueError("Session ID must be a non-empty string")

    if not UUID_PATTERN.match(session_id):
        raise ValueError(f"Invalid session ID format: {session_id}")

    return session_id


class SessionLifecycleState(str, Enum):
    """Session lifecycle states."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class SimulationSession:
    """
    Represents a single APGI simulation instance with async interface.

    Wraps APGISystem with thread-safe locking for concurrent access.
    """

    def __init__(self, session_id: str, config: Dict[str, Any], user_id: Optional[str] = None):
        """
        Initialize simulation session.

        Args:
            session_id: Unique session identifier
            config: Session configuration dictionary
            user_id: User identifier (optional)
        """
        self.session_id = session_id
        self.config = config
        self.user_id = user_id
        self.state = SessionLifecycleState.CREATED
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Thread-safe lock for concurrent access
        self.lock = asyncio.Lock()

        # Initialize APGI system
        config_path = config.get("config_path")
        self.apgi_system = APGISystem(config_path=config_path)

        # Apply custom config overrides if provided
        if "custom_config" in config and config["custom_config"]:
            self._apply_custom_config(config["custom_config"])

        # Simulation control
        self.is_running = False
        self.is_paused = False

        # Store state snapshot for pause/resume
        self._paused_state: Optional[Dict[str, Any]] = None

        logger.info(f"SimulationSession {session_id} initialized")

    def _apply_custom_config(self, custom_config: Dict[str, Any]) -> None:
        """Apply custom configuration overrides to APGI system."""

        # Deep merge custom config into system config
        def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value

        deep_merge(self.apgi_system.config, custom_config)

        # Reinitialize subsystems with new config
        self.apgi_system._initialize_subsystems()

    async def start(self) -> Dict[str, Any]:
        """
        Start simulation.

        Returns:
            Dict with status information
        """
        async with self.lock:
            if self.state == SessionLifecycleState.RUNNING:
                raise ValueError(f"Session {self.session_id} is already running")

            if self.state == SessionLifecycleState.PAUSED:
                # Resume from paused state
                if self._paused_state:
                    self._restore_state(self._paused_state)
                    self._paused_state = None

            self.is_running = True
            self.is_paused = False
            self.state = SessionLifecycleState.RUNNING
            self.updated_at = datetime.utcnow()

            logger.info(f"Session {self.session_id} started")

            return {
                "session_id": self.session_id,
                "status": self.state.value,
                "started_at": self.updated_at.isoformat() + "Z",
            }

    async def pause(self) -> Dict[str, Any]:
        """
        Pause simulation while preserving current state.

        Returns:
            Dict with status information
        """
        async with self.lock:
            if self.state != SessionLifecycleState.RUNNING:
                raise ValueError(f"Session {self.session_id} is not running")

            # Capture current state
            self._paused_state = self._capture_state()

            self.is_running = False
            self.is_paused = True
            self.state = SessionLifecycleState.PAUSED
            self.updated_at = datetime.utcnow()

            logger.info(f"Session {self.session_id} paused")

            return {
                "session_id": self.session_id,
                "status": self.state.value,
                "paused_at": self.updated_at.isoformat() + "Z",
            }

    async def stop(self) -> Dict[str, Any]:
        """
        Stop simulation.

        Returns:
            Dict with status information
        """
        async with self.lock:
            self.is_running = False
            self.is_paused = False
            self.state = SessionLifecycleState.STOPPED
            self.updated_at = datetime.utcnow()

            logger.info(f"Session {self.session_id} stopped")

            return {
                "session_id": self.session_id,
                "status": self.state.value,
                "stopped_at": self.updated_at.isoformat() + "Z",
            }

    async def reset(self) -> Dict[str, Any]:
        """
        Reset simulation to initial conditions.

        Returns:
            Dict with status information
        """
        async with self.lock:
            # Reset APGI system
            self.apgi_system.reset()

            # Clear paused state
            self._paused_state = None

            # Reset control flags
            self.is_running = False
            self.is_paused = False
            self.state = SessionLifecycleState.CREATED
            self.updated_at = datetime.utcnow()

            logger.info(f"Session {self.session_id} reset")

            return {
                "session_id": self.session_id,
                "status": self.state.value,
                "reset_at": self.updated_at.isoformat() + "Z",
            }

    async def step(self, extero_input: Any) -> Dict[str, Any]:
        """
        Execute single simulation step.

        Args:
            extero_input: Exteroceptive input for this step

        Returns:
            System state after step
        """
        async with self.lock:
            if not self.is_running:
                raise ValueError(f"Session {self.session_id} is not running")

            # Execute step in APGI system
            state = self.apgi_system.step(extero_input)
            self.updated_at = datetime.utcnow()

            return state

    async def get_state(self) -> Dict[str, Any]:
        """
        Get current system state.

        Returns:
            Complete system state
        """
        async with self.lock:
            state = self.apgi_system.get_state()

            # Add session metadata
            state["session_metadata"] = {
                "session_id": self.session_id,
                "state": self.state.value,
                "is_running": self.is_running,
                "is_paused": self.is_paused,
                "created_at": self.created_at.isoformat() + "Z",
                "updated_at": self.updated_at.isoformat() + "Z",
            }

            return state

    def _capture_state(self) -> Dict[str, Any]:
        """Capture complete system state for pause/resume."""
        return self.apgi_system.get_state()

    def _restore_state(self, state: Dict[str, Any]) -> None:
        """Restore system state from snapshot."""
        # Restore basic system state
        self.apgi_system.time = state.get("time", 0.0)
        self.apgi_system.history = state.get("history", {})

        # Restore core subsystems
        if "core" in state:
            core_state = state["core"]
            if "precision" in core_state:
                self.apgi_system.precision.__dict__.update(core_state["precision"])
            if "active_inference" in core_state:
                ai_state = core_state["active_inference"]
                self.apgi_system.active_inference.time = ai_state.get("time", 0.0)
                # Restore beliefs if present
                if "beliefs" in ai_state:
                    for i, belief_data in enumerate(ai_state["beliefs"]):
                        if i < len(self.apgi_system.active_inference.filter.beliefs):
                            belief = self.apgi_system.active_inference.filter.beliefs[i]
                            belief.mean = belief_data.get("mean", belief.mean)
                            belief.covariance = belief_data.get("covariance", belief.covariance)
                            belief.precision = belief_data.get("precision", belief.precision)
                            belief.prediction = belief_data.get("prediction", belief.prediction)
                            belief.prediction_error = belief_data.get(
                                "prediction_error", belief.prediction_error
                            )

        # Restore ignition subsystem
        if "ignition" in state:
            ignition_state = state["ignition"]
            if "threshold_stats" in ignition_state:
                self.apgi_system.ignition_threshold.__dict__.update(
                    ignition_state["threshold_stats"]
                )

        # Restore interoception subsystems
        if "interoception" in state:
            intero_state = state["interoception"]
            if "body_state" in intero_state:
                self.apgi_system.body_model.__dict__.update(intero_state["body_state"])
            if "allostatic_load" in intero_state:
                self.apgi_system.allostasis.__dict__.update(
                    {"allostatic_load": intero_state["allostatic_load"]}
                )
            if "somatic_markers" in intero_state:
                self.apgi_system.somatic_markers.__dict__.update(intero_state["somatic_markers"])

        # Restore self-model subsystems
        if "self_model" in state:
            self_state = state["self_model"]
            if "minimal_self" in self_state:
                self.apgi_system.minimal_self.__dict__.update(self_state["minimal_self"])
            if "narrative_self" in self_state:
                self.apgi_system.narrative_self.__dict__.update(self_state["narrative_self"])
            if "coherence" in self_state:
                self.apgi_system.coherence.__dict__.update(self_state["coherence"])

        # Restore thermodynamic subsystems
        if "thermodynamic" in state:
            thermo_state = state["thermodynamic"]
            if "metabolic_reserves" in thermo_state:
                self.apgi_system.metabolism.__dict__.update(
                    {"current_reserves": thermo_state["metabolic_reserves"]}
                )
            if "entropy_stats" in thermo_state:
                self.apgi_system.entropy.__dict__.update(thermo_state["entropy_stats"])

        # Restore neural subsystems
        if "neural" in state:
            neural_state = state["neural"]
            if "oscillations" in neural_state:
                self.apgi_system.oscillations.__dict__.update(neural_state["oscillations"])
            if "networks" in neural_state:
                self.apgi_system.networks.__dict__.update(neural_state["networks"])

        logger.info(f"Session {self.session_id} state restored")


class SessionManager:
    """
    Manages APGI simulation sessions with Redis caching and database persistence.

    Handles session lifecycle, state caching, and resource cleanup.
    """

    def __init__(self, redis_client: redis.Redis, db_session_factory: Any):
        """
        Initialize session manager.

        Args:
            redis_client: Async Redis client for caching
            db_session_factory: SQLAlchemy session factory for database access
        """
        self.redis = redis_client
        self.db_session_factory = db_session_factory

        # In-memory session cache with TTL and size limits
        self.session_cache_max_size = 1000  # Maximum number of sessions to cache
        self.session_ttl_seconds = 3600  # 1 hour TTL for cached sessions
        self.sessions: OrderedDict[str, Tuple[SimulationSession, float]] = (
            OrderedDict()
        )  # (session, last_access_time)

        # Lock for session cache access
        self.cache_lock = asyncio.Lock()

        logger.info("SessionManager initialized")

    def _cleanup_expired_sessions(self) -> None:
        """Remove expired sessions from cache (called within lock)."""
        current_time = time.time()
        expired_keys = []

        for session_id, (_, last_access) in self.sessions.items():
            if current_time - last_access > self.session_ttl_seconds:
                expired_keys.append(session_id)

        for key in expired_keys:
            del self.sessions[key]
            logger.debug(f"Removed expired session {key} from cache")

    def _evict_oldest_sessions(self) -> None:
        """Remove oldest sessions to maintain cache size limit (called within lock)."""
        while len(self.sessions) > self.session_cache_max_size:
            oldest_key = next(iter(self.sessions))  # OrderedDict preserves insertion order
            del self.sessions[oldest_key]
            logger.debug(f"Evicted oldest session {oldest_key} from cache")

    async def create_session(
        self, request: SessionCreateRequest, user_id: str = "default_user"
    ) -> str:
        """
        Create new simulation session.

        Args:
            request: Session creation request
            user_id: User identifier

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())

        # Prepare configuration
        config = {
            "config_path": request.config_path,
            "custom_config": request.custom_config,
            "description": request.description,
        }

        # Create simulation session
        sim_session = SimulationSession(session_id, config, user_id)

        # Atomic cache + database operation
        async with self.cache_lock:
            # Cleanup expired sessions before adding new one
            self._cleanup_expired_sessions()

            # First try to persist to database with circuit breaker
            await self._persist_session_to_database(
                session_id, user_id, config, request.description
            )

            # Only add to cache after successful DB write
            self.sessions[session_id] = (sim_session, time.time())  # Store with timestamp
            logger.info(f"Session {session_id} created and persisted")

            # Enforce cache size limit
            self._evict_oldest_sessions()

        # Cache session metadata in Redis with circuit breaker
        await self._cache_session_metadata_safe(session_id, sim_session)

        return session_id

    @circuit_breaker(name="database_session_persist", failure_threshold=3, recovery_timeout=30.0)
    async def _persist_session_to_database(
        self,
        session_id: str,
        user_id: str,
        config: Dict[str, Any],
        description: Optional[str] = None,
    ) -> None:
        """Persist session to database with circuit breaker protection."""
        db_session = self.db_session_factory()
        try:
            db_model = SessionModel(
                session_id=session_id,
                user_id=user_id,
                config=config,
                state=SessionState.CREATED.value,
                description=description,
                tags=[],
            )
            db_session.add(db_model)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            logger.error(f"Database error persisting session {session_id}: {e}")
            raise CircuitBreakerException(f"Database operation failed: {e}")
        finally:
            db_session.close()

    @circuit_breaker(name="redis_session_cache", failure_threshold=5, recovery_timeout=60.0)
    async def _cache_session_metadata_safe(
        self, session_id: str, sim_session: SimulationSession
    ) -> None:
        """Cache session metadata in Redis with circuit breaker protection."""
        try:
            await self._cache_session_metadata(session_id, sim_session)
        except Exception as e:
            logger.error(f"Redis cache error for session {session_id}: {e}")
            raise CircuitBreakerException(f"Redis operation failed: {e}")

    async def get_session(self, session_id: str) -> SimulationSession:
        """
        Retrieve existing session.

        Args:
            session_id: Session identifier

        Returns:
            SimulationSession instance

        Raises:
            ValueError: If session not found or invalid session ID
        """
        # Validate session ID format
        validate_session_id(session_id)

        # Check memory cache first
        async with self.cache_lock:
            # Cleanup expired sessions
            self._cleanup_expired_sessions()

            if session_id in self.sessions:
                session_data, last_access = self.sessions[session_id]
                # Update access time and move to end (LRU)
                self.sessions.move_to_end(session_id)
                self.sessions[session_id] = (session_data, time.time())
                return session_data

        # Check Redis cache
        cached_data = await self.redis.get(f"session:{session_id}")
        if cached_data:
            # Reconstruct session from cache
            metadata = json.loads(cached_data)
            sim_session = SimulationSession(session_id, metadata["config"], metadata.get("user_id"))
            sim_session.state = SessionLifecycleState(metadata["state"])
            sim_session.created_at = datetime.fromisoformat(
                metadata["created_at"].replace("Z", "+00:00")
            )
            sim_session.updated_at = datetime.fromisoformat(
                metadata["updated_at"].replace("Z", "+00:00")
            )

            # Add to memory cache
            async with self.cache_lock:
                self.sessions[session_id] = (sim_session, time.time())  # Store with timestamp

            return sim_session

        # Load from database
        db_session = self.db_session_factory()
        try:
            stmt = select(SessionModel).where(SessionModel.session_id == session_id)
            result = db_session.execute(stmt)
            db_model = result.scalar_one_or_none()

            if not db_model:
                raise ValueError(f"Session {session_id} not found")

            # Reconstruct session
            sim_session = SimulationSession(session_id, db_model.config, db_model.user_id)
            sim_session.state = SessionLifecycleState(db_model.state)
            sim_session.created_at = db_model.created_at
            sim_session.updated_at = db_model.updated_at

            # Add to caches
            async with self.cache_lock:
                self.sessions[session_id] = (sim_session, time.time())  # Store with timestamp

            await self._cache_session_metadata(session_id, sim_session)

            logger.info(f"Session {session_id} loaded from database")

            return sim_session
        finally:
            db_session.close()

    async def delete_session(self, session_id: str) -> None:
        """
        Clean up session resources.

        Args:
            session_id: Session identifier

        Raises:
            ValueError: If session ID is invalid
        """
        # Validate session ID format
        validate_session_id(session_id)

        # First check if session exists in database (even if not in cache)
        db_session = self.db_session_factory()
        try:
            stmt = select(SessionModel).where(SessionModel.session_id == session_id)
            result = db_session.execute(stmt)
            db_model = result.scalar_one_or_none()

            if not db_model:
                raise ValueError(f"Session {session_id} not found")
        finally:
            db_session.close()

        # Remove from memory cache if present (check existence inside lock for concurrency safety)
        async with self.cache_lock:
            if session_id not in self.sessions:
                # Already deleted by another concurrent call
                raise ValueError(f"Session {session_id} not found")
            del self.sessions[session_id]

        # Remove from Redis cache
        await self.redis.delete(f"session:{session_id}")

        # Delete from database
        db_session = self.db_session_factory()
        try:
            stmt = select(SessionModel).where(SessionModel.session_id == session_id)
            result = db_session.execute(stmt)
            db_model = result.scalar_one_or_none()

            if db_model:
                db_session.delete(db_model)
                db_session.commit()
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise
        finally:
            db_session.close()

        logger.info(f"Session {session_id} cleaned up")

    async def update_session_state(self, session_id: str, new_state: SessionLifecycleState) -> None:
        """
        Update session state in database and cache.

        Args:
            session_id: Session identifier
            new_state: New session state

        Raises:
            ValueError: If session ID is invalid
        """
        # Validate session ID format
        validate_session_id(session_id)
        # Update database
        db_session = self.db_session_factory()
        try:
            stmt = select(SessionModel).where(SessionModel.session_id == session_id)
            result = db_session.execute(stmt)
            db_model = result.scalar_one_or_none()

            if db_model:
                db_model.state = new_state.value
                db_model.updated_at = datetime.utcnow()
                db_session.commit()
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to update session {session_id} state: {e}")
            raise
        finally:
            db_session.close()

        # Update Redis cache
        sim_session = await self.get_session(session_id)
        await self._cache_session_metadata(session_id, sim_session)

    async def _cache_session_metadata(
        self, session_id: str, sim_session: SimulationSession
    ) -> None:
        """Cache session metadata in Redis."""
        metadata = {
            "session_id": session_id,
            "state": sim_session.state.value,
            "config": sim_session.config,
            "user_id": sim_session.user_id,
            "created_at": sim_session.created_at.isoformat() + "Z",
            "updated_at": sim_session.updated_at.isoformat() + "Z",
        }

        # Cache for 1 hour
        await self.redis.setex(f"session:{session_id}", 3600, json.dumps(metadata))

    async def list_sessions(
        self, user_id: Optional[str] = None, limit: int = 50, cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all sessions, optionally filtered by user, with pagination.

        Args:
            user_id: Optional user ID filter
            limit: Maximum number of sessions to return (default 50, max 100)
            cursor: Cursor for pagination (ISO timestamp)

        Returns:
            Dict with sessions list and pagination info
        """
        # Validate limit
        limit = min(max(1, limit), 100)  # Between 1 and 100

        db_session = self.db_session_factory()
        try:
            stmt = select(SessionModel).order_by(SessionModel.created_at.desc())

            if user_id:
                stmt = stmt.where(SessionModel.user_id == user_id)

            # Apply cursor if provided
            if cursor:
                from datetime import datetime

                try:
                    cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
                    stmt = stmt.where(SessionModel.created_at < cursor_dt)
                except ValueError:
                    # Invalid cursor, ignore
                    pass

            # Limit results
            stmt = stmt.limit(limit + 1)  # Get one extra to check if there are more

            result = db_session.execute(stmt)
            db_sessions = result.scalars().all()

            # Check if there are more results
            has_more = len(db_sessions) > limit
            sessions = db_sessions[:limit]

            # Next cursor is the created_at of the last session
            next_cursor = None
            if has_more and sessions:
                next_cursor = sessions[-1].created_at.isoformat() + "Z"

            return {
                "sessions": [
                    {
                        "session_id": s.session_id,
                        "user_id": s.user_id,
                        "state": s.state,
                        "created_at": s.created_at.isoformat() + "Z",
                        "updated_at": s.updated_at.isoformat() + "Z",
                        "description": s.description,
                    }
                    for s in sessions
                ],
                "pagination": {
                    "next_cursor": next_cursor,
                    "has_more": has_more,
                },
            }
        finally:
            db_session.close()


# Redis client (will be initialized in main app)
_redis_client: Optional[redis.Redis] = None
_session_manager: Optional[SessionManager] = None


def get_redis_client() -> redis.Redis:
    """Get Redis client dependency."""
    if _redis_client is None:
        raise ServiceUnavailableError("Redis", "Redis client not initialized")
    return _redis_client


def get_session_manager() -> SessionManager:
    """Get SessionManager dependency."""
    if _session_manager is None:
        raise ServiceUnavailableError("SessionManager", "Session manager not initialized")
    return _session_manager


def init_session_routes(redis_client: redis.Redis) -> None:
    """
    Initialize session routes with Redis client.

    Args:
        redis_client: Redis client for session caching
    """
    global _redis_client, _session_manager
    _redis_client = redis_client
    _session_manager = SessionManager(redis_client, SessionLocal)
    logger.info("Session routes initialized")
