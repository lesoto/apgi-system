"""
Session Management Routes

API endpoints for creating, controlling, and managing APGI simulation sessions.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, status

from api.exceptions import SessionStateConflictError
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
from api.services.authorization import (
    Permission,
    Role,
    TokenPayload,
    get_current_user,
    has_any_role,
    require_permission,
    verify_session_owner,
)
from api.services.session_manager import (
    SessionLifecycleState,
    SessionManager,
    get_session_manager,
)

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


@router.get(
    "",
    response_model=SessionListResponse,
    summary="List sessions",
    description="Retrieve a list of simulation sessions, filtered by user permissions, with pagination",
    dependencies=[Depends(require_permission(Permission.SESSION_READ))],
)
async def list_sessions(
    limit: int = 50,
    cursor: Optional[str] = None,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
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

    # Determine user_id for filtering: None for admins, user_id for regular users
    user_id = None if has_any_role(current_user.roles, [Role.ADMIN]) else current_user.user_id

    result: Dict[str, Any] = await manager.list_sessions(
        user_id=user_id, limit=limit, cursor=cursor
    )

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


@router.post(
    "",
    response_model=SessionCreateResponse,
    summary="Create session",
    description="Create a new simulation session with specified configuration",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.SESSION_CREATE))],
)
async def create_session(
    request: SessionCreateRequest,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
) -> SessionCreateResponse:
    """
    Create new simulation session.

    Args:
        request: Session creation request with configuration
        manager: Session manager dependency
        current_user: Current authenticated user

    Returns:
        SessionCreateResponse with session ID and details

    Raises:
        HTTPException: If session creation fails
    """
    # Create session
    session_id = await manager.create_session(request, user_id=current_user.user_id)

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
    dependencies=[Depends(require_permission(Permission.SESSION_READ))],
)
async def get_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
    _owner_check: None = Depends(verify_session_owner),
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
    sim_session = await manager.get_session(session_id)

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
    dependencies=[Depends(require_permission(Permission.SESSION_CONTROL))],
)
async def start_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
    _owner_check: None = Depends(verify_session_owner),
) -> SessionActionResponse:
    """
    Start simulation.

    Args:
        session_id: Unique session identifier
        manager: Session manager dependency
        current_user: Current authenticated user

    Returns:
        SessionActionResponse with updated status

    Raises:
        HTTPException: If session not found or cannot be started
    """
    sim_session = await manager.get_session(session_id)

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
    dependencies=[Depends(require_permission(Permission.SESSION_CONTROL))],
)
async def pause_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
    _owner_check: None = Depends(verify_session_owner),
) -> SessionActionResponse:
    """
    Pause simulation.

    Args:
        session_id: Unique session identifier
        manager: Session manager dependency
        current_user: Current authenticated user

    Returns:
        SessionActionResponse with updated status

    Raises:
        HTTPException: If session not found or cannot be paused
    """
    sim_session = await manager.get_session(session_id)

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
    dependencies=[Depends(require_permission(Permission.SESSION_CONTROL))],
)
async def stop_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
    _owner_check: None = Depends(verify_session_owner),
) -> SessionActionResponse:
    """
    Stop simulation.

    Args:
        session_id: Unique session identifier
        manager: Session manager dependency
        current_user: Current authenticated user

    Returns:
        SessionActionResponse with updated status

    Raises:
        HTTPException: If session not found
    """
    sim_session = await manager.get_session(session_id)

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
    dependencies=[Depends(require_permission(Permission.SESSION_CONTROL))],
)
async def reset_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
    _owner_check: None = Depends(verify_session_owner),
) -> SessionActionResponse:
    """
    Reset simulation to initial state.

    Args:
        session_id: Unique session identifier
        manager: Session manager dependency
        current_user: Current authenticated user

    Returns:
        SessionActionResponse with updated status

    Raises:
        HTTPException: If session not found
    """
    sim_session = await manager.get_session(session_id)

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
    dependencies=[Depends(require_permission(Permission.SESSION_DELETE))],
)
async def delete_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
    _owner_check: None = Depends(verify_session_owner),
) -> None:
    """
    Delete session and clean up resources.

    Args:
        session_id: Unique session identifier
        manager: Session manager dependency
        current_user: Current authenticated user

    Returns:
        No content (204)

    Raises:
        HTTPException: If session not found or deletion fails
    """
    # Delete session
    await manager.delete_session(session_id)

    logger.info(f"Session {session_id} deleted")

    return None
