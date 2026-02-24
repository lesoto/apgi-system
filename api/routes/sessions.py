"""
Session Management Routes

API endpoints for creating, controlling, and managing APGI simulation sessions.
"""

import logging
from typing import Dict, Any, Optional

import redis.asyncio as redis
from fastapi import APIRouter, Depends, status

from api.exceptions import ServiceUnavailableError, SessionNotFoundError, SessionStateConflictError
from api.models.schemas import (
    ErrorResponse,
    PaginationInfo,
    SessionActionResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionListItem,
    SessionListResponse,
    SessionResponse,
)
from api.services.session_manager import SessionLifecycleState, SessionManager
from api.database.connection import SessionLocal

logger = logging.getLogger(__name__)


# Create router
router = APIRouter(
    prefix="/v1/sessions",
    tags=["Sessions"],
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)


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


@router.get(
    "",
    response_model=SessionListResponse,
    summary="List sessions",
    description="Retrieve a list of simulation sessions, filtered by user permissions, with pagination",
    dependencies=[],
)
async def list_sessions(
    limit: int = 50,
    cursor: Optional[str] = None,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionListResponse:
    """
    List sessions.

    Returns sessions owned by the current user, or all sessions if user is admin, with pagination.

    Args:
        limit: Maximum number of sessions to return (1-100, default 50)
        cursor: Cursor for pagination (ISO timestamp)
        manager: Session manager dependency
        current_user: Current authenticated user

    Returns:
        SessionListResponse with list of sessions and pagination info
    """
    # Validate limit
    limit = min(max(1, limit), 100)

    # List all sessions (no user filtering)
    result: Dict[str, Any] = await manager.list_sessions(user_id=None, limit=limit, cursor=cursor)

    # Convert to response format
    sessions = [
        SessionListItem(
            session_id=s["session_id"],
            user_id=s["user_id"],
            state=s["state"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            description=s["description"],
        )
        for s in result["sessions"]
    ]

    pagination = (
        PaginationInfo(
            next_cursor=result["pagination"]["next_cursor"],
            has_more=result["pagination"]["has_more"],
        )
        if result["pagination"]["next_cursor"] or result["pagination"]["has_more"]
        else None
    )

    return SessionListResponse(sessions=sessions, pagination=pagination)


async def create_session(
    request: SessionCreateRequest,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionCreateResponse:
    """
    Create new simulation session.

    Args:
        request: Session creation request with configuration
        manager: Session manager dependency

    Returns:
        SessionCreateResponse with session ID and details

    Raises:
        HTTPException: If session creation fails
    """
    # Create session
    session_id = await manager.create_session(request)

    # Get session details
    sim_session = await manager.get_session(session_id)

    logger.info(f"Session {session_id} created successfully")

    return SessionCreateResponse(
        session_id=session_id,
        status=sim_session.state.value,
        created_at=sim_session.created_at,
        config=sim_session.config,
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session details",
    description="Retrieve detailed information about a specific simulation session",
    dependencies=[],
)
async def get_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionResponse:
    """
    Get session details.

    Args:
        session_id: Unique session identifier
        manager: Session manager dependency

    Returns:
        SessionResponse with session details

    Raises:
        HTTPException: If session not found
    """
    try:
        sim_session = await manager.get_session(session_id)
    except ValueError:
        raise SessionNotFoundError(session_id)

    return SessionResponse(
        session_id=session_id,
        status=sim_session.state.value,
        created_at=sim_session.created_at,
        updated_at=sim_session.updated_at,
        config=sim_session.config,
        description=sim_session.config.get("description"),
    )


@router.post(
    "/{session_id}/start",
    response_model=SessionActionResponse,
    summary="Start simulation",
    description="Start or resume simulation for specified session",
    dependencies=[],
)
async def start_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionActionResponse:
    """
    Start simulation.

    Args:
        session_id: Unique session identifier
        manager: Session manager dependency

    Returns:
        SessionActionResponse with updated status

    Raises:
        HTTPException: If session not found or cannot be started
    """
    try:
        sim_session = await manager.get_session(session_id)
    except ValueError:
        raise SessionNotFoundError(session_id)

    try:
        result = await sim_session.start()
    except ValueError:
        # State conflict - trying to start session in invalid state
        raise SessionStateConflictError(session_id, sim_session.state.value, "start")

    # Update state in database
    await manager.update_session_state(session_id, SessionLifecycleState.RUNNING)

    logger.info(f"Session {session_id} started")

    return SessionActionResponse(
        session_id=session_id, status=result["status"], timestamp=sim_session.updated_at
    )


@router.post(
    "/{session_id}/pause",
    response_model=SessionActionResponse,
    summary="Pause simulation",
    description="Pause simulation while preserving current state",
    dependencies=[],
)
async def pause_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionActionResponse:
    """
    Pause simulation.

    Args:
        session_id: Unique session identifier
        manager: Session manager dependency

    Returns:
        SessionActionResponse with updated status

    Raises:
        HTTPException: If session not found or cannot be paused
    """
    try:
        sim_session = await manager.get_session(session_id)
    except ValueError:
        raise SessionNotFoundError(session_id)

    try:
        result = await sim_session.pause()
    except ValueError:
        # State conflict - trying to pause session in invalid state
        raise SessionStateConflictError(session_id, sim_session.state.value, "pause")

    # Update state in database
    await manager.update_session_state(session_id, SessionLifecycleState.PAUSED)

    logger.info(f"Session {session_id} paused")

    return SessionActionResponse(
        session_id=session_id, status=result["status"], timestamp=sim_session.updated_at
    )


@router.post(
    "/{session_id}/stop",
    response_model=SessionActionResponse,
    summary="Stop simulation",
    description="Stop simulation for specified session",
    dependencies=[],
)
async def stop_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionActionResponse:
    """
    Stop simulation.

    Args:
        session_id: Unique session identifier
        manager: Session manager dependency

    Returns:
        SessionActionResponse with updated status

    Raises:
        HTTPException: If session not found
    """
    try:
        sim_session = await manager.get_session(session_id)
    except ValueError:
        raise SessionNotFoundError(session_id)

    result = await sim_session.stop()

    # Update state in database
    await manager.update_session_state(session_id, SessionLifecycleState.STOPPED)

    logger.info(f"Session {session_id} stopped")

    return SessionActionResponse(
        session_id=session_id, status=result["status"], timestamp=sim_session.updated_at
    )


@router.post(
    "/{session_id}/reset",
    response_model=SessionActionResponse,
    summary="Reset simulation",
    description="Reset simulation to initial conditions",
    dependencies=[],
)
async def reset_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
) -> SessionActionResponse:
    """
    Reset simulation to initial state.

    Args:
        session_id: Unique session identifier
        manager: Session manager dependency

    Returns:
        SessionActionResponse with updated status

    Raises:
        HTTPException: If session not found
    """
    try:
        sim_session = await manager.get_session(session_id)
    except ValueError:
        raise SessionNotFoundError(session_id)

    result = await sim_session.reset()

    # Update state in database
    await manager.update_session_state(session_id, SessionLifecycleState.CREATED)

    logger.info(f"Session {session_id} reset")

    return SessionActionResponse(
        session_id=session_id, status=result["status"], timestamp=sim_session.updated_at
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
    description="Delete session and clean up all associated resources",
    dependencies=[],
)
async def delete_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
) -> None:
    """
    Delete session and clean up resources.

    Args:
        session_id: Unique session identifier
        manager: Session manager dependency

    Returns:
        No content (204)

    Raises:
        HTTPException: If session not found or deletion fails
    """
    # Verify session exists in manager (this will raise if not found)
    try:
        await manager.get_session(session_id)
    except ValueError:
        raise SessionNotFoundError(session_id)

    # Delete session
    await manager.delete_session(session_id)

    logger.info(f"Session {session_id} deleted")

    return None
