"""
State Access Routes

API endpoints for accessing APGI system state, ignition history, and subsystem data.
"""

import base64
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request

from api.models.schemas import (
    AllostaticState,
    BodyState,
    ErrorResponse,
    IgnitionEvent,
    IgnitionHistoryResponse,
    IgnitionState,
    MetabolicState,
    MinimalSelfState,
    NarrativeSelfState,
    PaginationInfo,
    PrecisionState,
    SelfModelState,
    SystemStateResponse,
    WorkspaceState,
    PredictionErrorsResponse,
    SomaticMarkersResponse,
    SummaryStatistics,
)
from api.services.authorization import (
    require_permission,
    Permission,
    get_current_user,
    TokenPayload,
    has_any_role,
    Role,
)
from api.services.session_manager import SessionManager, get_session_manager

logger = logging.getLogger(__name__)


# Create router
router = APIRouter(
    prefix="/v1/sessions",
    tags=["State Access"],
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)


@router.get(
    "/{session_id}/state",
    response_model=SystemStateResponse,
    summary="Get complete system state",
    description="Retrieve the complete current state of all APGI subsystems for the specified session",
    dependencies=[Depends(require_permission(Permission.DATA_READ))],
)
async def get_system_state(
    session_id: str,
    request: Request,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
) -> SystemStateResponse:
    """
    Get complete system state.

    Returns comprehensive state information including:
    - Ignition status and dynamics
    - Global workspace state
    - Interoceptive body state
    - Allostatic regulation
    - Precision weighting
    - Metabolic reserves
    - Self-model state

    Args:
        session_id: Unique session identifier
        request: HTTP request for authentication check
        manager: Session manager dependency

    Returns:
        SystemStateResponse with complete state

    Raises:
        HTTPException: If session not found or state cannot be retrieved
    """
    try:
        # Get session
        sim_session = await manager.get_session(session_id)

        # Check ownership
        if sim_session.user_id != current_user.user_id and not has_any_role(
            current_user.roles, [Role.ADMIN]
        ):
            raise HTTPException(status_code=403, detail="Not authorized to access this session")

        # Get complete state
        state = await sim_session.get_state()

        # Extract and format state components
        ignition_data = state.get("ignition", {})
        workspace_data = state.get("workspace", {})
        body_data = state.get("body", {})
        allostasis_data = state.get("allostasis", {})
        precision_data = state.get("precision", {})
        metabolism_data = state.get("metabolism", {})
        self_model_data = state.get("self_model", {})

        # Build response
        response = SystemStateResponse(
            time_ms=state.get("time", 0.0),
            ignition=IgnitionState(
                ignition_occurred=ignition_data.get("ignition_occurred", False),
                total_signal=ignition_data.get("total_signal", 0.0),
                threshold=ignition_data.get("threshold", 0.0),
                duration_ms=ignition_data.get("duration_ms"),
            ),
            workspace=WorkspaceState(
                is_broadcasting=workspace_data.get("is_broadcasting", False),
                content=workspace_data.get("content"),
                broadcast_duration_ms=workspace_data.get("broadcast_duration_ms"),
            ),
            body=BodyState(
                heart_rate=body_data.get("heart_rate", 70.0),
                cortisol=body_data.get("cortisol", 0.1),
                temperature=body_data.get("temperature", 37.0),
            ),
            allostasis=AllostaticState(allostatic_load=allostasis_data.get("allostatic_load", 0.0)),
            precision=PrecisionState(
                exteroceptive=precision_data.get("exteroceptive", 1.0),
                interoceptive=precision_data.get("interoceptive", 1.0),
            ),
            metabolism=MetabolicState(
                reserves=metabolism_data.get("reserves", 1000.0),
                reserve_fraction=metabolism_data.get("reserve_fraction", 1.0),
            ),
            self_model=SelfModelState(
                minimal=MinimalSelfState(
                    coherence=self_model_data.get("minimal", {}).get("coherence", 0.5)
                ),
                narrative=NarrativeSelfState(
                    active=self_model_data.get("narrative", {}).get("active", False)
                ),
            ),
        )

        logger.info(f"Retrieved state for session {session_id}")
        return response

    except ValueError as e:
        logger.warning(f"Session {session_id} not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
        )
    except Exception:
        logger.error(f"Failed to get state for session {session_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system state",
        )


@router.get(
    "/{session_id}/ignition-history",
    response_model=IgnitionHistoryResponse,
    summary="Get ignition event history",
    description="Retrieve historical ignition events with optional filtering and pagination",
    dependencies=[Depends(require_permission(Permission.DATA_READ))],
)
async def get_ignition_history(  # noqa: C901
    session_id: str,
    request: Request,
    start_time: Optional[float] = Query(None, description="Filter events after this time (ms)"),
    end_time: Optional[float] = Query(None, description="Filter events before this time (ms)"),
    limit: Optional[int] = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of events to return (warning: values > 500 may be slow)",
    ),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
) -> IgnitionHistoryResponse:
    """
    Get ignition event history.

    Returns a list of ignition events that occurred during the simulation,
    with optional time-based filtering and pagination support.

    Args:
        session_id: Unique session identifier
        request: HTTP request for authentication check
        start_time: Optional start time filter (milliseconds)
        end_time: Optional end time filter (milliseconds)
        limit: Maximum number of events to return (1-1000)
        cursor: Pagination cursor for fetching next page
        manager: Session manager dependency

    Returns:
        IgnitionHistoryResponse with events and pagination info

    Raises:
        HTTPException: If session not found or history cannot be retrieved
    """
    try:
        # Enforce maximum limit to prevent excessive memory usage
        if limit and limit > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit exceeds maximum allowed value of 500. Use smaller limits or time filters to reduce data size.",
            )

        # Get session
        sim_session = await manager.get_session(session_id)

        # Check ownership
        if sim_session.user_id != current_user.user_id and not has_any_role(
            current_user.roles, [Role.ADMIN]
        ):
            raise HTTPException(status_code=403, detail="Not authorized to access this session")

        # Get complete state to access history
        state = await sim_session.get_state()
        history = state.get("history", {})

        # Extract ignition events from history
        times = history.get("time", [])
        ignitions = history.get("ignitions", [])
        ignition_history = history.get("ignition", [])

        # Build event list
        events = []
        for i, (time_val, ignition_val) in enumerate(zip(times, ignitions)):
            if ignition_val:  # Only include actual ignition events
                # Apply time filters
                if start_time is not None and time_val < start_time:
                    continue
                if end_time is not None and time_val > end_time:
                    continue

                # Use historical ignition data for this event
                ignition_data = ignition_history[i] if i < len(ignition_history) else {}
                total_signal = ignition_data.get("total_signal", 0.0)
                threshold = ignition_data.get("threshold", 2.0)

                # Estimate duration based on signal decay (simplified calculation)
                duration_ms = min(500.0, max(100.0, total_signal * 100))

                # Use historical signal and threshold values
                events.append(
                    IgnitionEvent(
                        time_ms=time_val,
                        duration_ms=duration_ms,
                        trigger_signal=total_signal,
                        threshold=threshold,
                    )
                )

        # Apply pagination
        limit_val = limit or 100  # Default to 100 if None
        start_idx = 0
        if cursor:
            try:
                cursor_data = json.loads(base64.urlsafe_b64decode(cursor).decode())
                start_idx = cursor_data.get("offset", 0)
            except Exception as e:
                logger.warning(f"Invalid cursor: {e}")
                start_idx = 0

        end_idx = start_idx + limit_val
        paginated_events = events[start_idx:end_idx]
        has_more = end_idx < len(events)

        # Generate next cursor
        next_cursor = None
        if has_more:
            cursor_data = {"offset": end_idx}
            next_cursor = base64.urlsafe_b64encode(json.dumps(cursor_data).encode()).decode()

        response = IgnitionHistoryResponse(
            events=paginated_events,
            pagination=(
                PaginationInfo(next_cursor=next_cursor, has_more=has_more)
                if paginated_events
                else None
            ),
        )

        logger.info(f"Retrieved {len(paginated_events)} ignition events for session {session_id}")
        return response

    except ValueError as e:
        logger.warning(f"Session {session_id} not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
        )
    except Exception:
        logger.error(f"Failed to get ignition history for session {session_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ignition history",
        )


@router.get(
    "/{session_id}/interoception",
    response_model=BodyState,
    summary="Get interoceptive body state",
    description="Retrieve current interoceptive state including physiological parameters",
    dependencies=[Depends(require_permission(Permission.DATA_READ))],
)
async def get_interoceptive_state(
    session_id: str,
    request: Request,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
) -> BodyState:
    """
    Get interoceptive body state.

    Returns current physiological state including:
    - Heart rate
    - Cortisol levels
    - Body temperature

    Args:
        session_id: Unique session identifier
        request: HTTP request for authentication check
        manager: Session manager dependency

    Returns:
        BodyState with current interoceptive parameters

    Raises:
        HTTPException: If session not found or state cannot be retrieved
    """
    try:
        # Get session
        sim_session = await manager.get_session(session_id)

        # Check ownership
        if sim_session.user_id != current_user.user_id and not has_any_role(
            current_user.roles, [Role.ADMIN]
        ):
            raise HTTPException(status_code=403, detail="Not authorized to access this session")

        # Get complete state
        state = await sim_session.get_state()
        body_data = state.get("body", {})

        response = BodyState(
            heart_rate=body_data.get("heart_rate", 70.0),
            cortisol=body_data.get("cortisol", 0.1),
            temperature=body_data.get("temperature", 37.0),
        )

        logger.info(f"Retrieved interoceptive state for session {session_id}")
        return response

    except ValueError as e:
        logger.warning(f"Session {session_id} not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
        )
    except Exception:
        logger.error(f"Failed to get interoceptive state for session {session_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get interoceptive state",
        )


@router.get(
    "/{session_id}/prediction-errors",
    response_model=PredictionErrorsResponse,
    summary="Get prediction errors",
    description="Retrieve hierarchical prediction errors from all levels of the predictive processing hierarchy",
    dependencies=[Depends(require_permission(Permission.DATA_READ))],
)
async def get_prediction_errors(
    session_id: str,
    request: Request,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
) -> PredictionErrorsResponse:
    """
    Get prediction errors.

    Returns hierarchical prediction errors showing the discrepancy between
    predictions and actual observations at each level of the processing hierarchy.

    Args:
        session_id: Unique session identifier
        request: HTTP request for authentication check
        manager: Session manager dependency

    Returns:
        Dict with prediction error information

    Raises:
        HTTPException: If session not found or errors cannot be retrieved
    """
    try:
        # Get session
        sim_session = await manager.get_session(session_id)

        # Check ownership
        if sim_session.user_id != current_user.user_id and not has_any_role(
            current_user.roles, [Role.ADMIN]
        ):
            raise HTTPException(status_code=403, detail="Not authorized to access this session")

        # Get complete state
        state = await sim_session.get_state()
        prediction_data = state.get("prediction", {})

        # Extract prediction errors
        response = PredictionErrorsResponse(
            session_id=session_id,
            time_ms=state.get("time", 0.0),
            prediction_errors=prediction_data.get("errors", {}),
            exteroceptive_stats=prediction_data.get("exteroceptive_stats", {}),
            interoceptive_stats=prediction_data.get("interoceptive_stats", {}),
        )

        logger.info(f"Retrieved prediction errors for session {session_id}")
        return response

    except ValueError as e:
        logger.warning(f"Session {session_id} not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
        )
    except Exception:
        logger.error(f"Failed to get prediction errors for session {session_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get prediction errors",
        )


@router.get(
    "/{session_id}/somatic-markers",
    response_model=SomaticMarkersResponse,
    summary="Get somatic markers",
    description="Retrieve stored somatic markers (context-action-outcome associations)",
    dependencies=[Depends(require_permission(Permission.DATA_READ))],
)
async def get_somatic_markers(
    session_id: str,
    request: Request,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
) -> SomaticMarkersResponse:
    """
    Get somatic markers.

    Returns stored context-action-outcome associations with gain values,
    representing learned emotional/bodily responses to situations.

    Args:
        session_id: Unique session identifier
        request: HTTP request for authentication check
        manager: Session manager dependency

    Returns:
        Dict with somatic marker information

    Raises:
        HTTPException: If session not found or markers cannot be retrieved
    """
    try:
        # Get session
        sim_session = await manager.get_session(session_id)

        # Check ownership
        if sim_session.user_id != current_user.user_id and not has_any_role(
            current_user.roles, [Role.ADMIN]
        ):
            raise HTTPException(status_code=403, detail="Not authorized to access this session")

        # Get complete state
        state = await sim_session.get_state()

        # Extract somatic marker data from interoception subsystem
        interoception_data = state.get("interoception", {})
        somatic_data = interoception_data.get("somatic_markers", {})

        response = SomaticMarkersResponse(
            session_id=session_id,
            time_ms=state.get("time", 0.0),
            num_markers=somatic_data.get("num_markers", 0),
            total_retrievals=somatic_data.get("total_retrievals", 0),
            successful_retrievals=somatic_data.get("successful_retrievals", 0),
            retrieval_rate=somatic_data.get("retrieval_rate", 0.0),
            markers=somatic_data.get("markers", []),
        )

        logger.info(f"Retrieved somatic markers for session {session_id}")
        return response

    except ValueError as e:
        logger.warning(f"Session {session_id} not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
        )
    except Exception:
        logger.error(f"Failed to get somatic markers for session {session_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get somatic markers",
        )


@router.get(
    "/{session_id}/summary-statistics",
    response_model=SummaryStatistics,
    summary="Get summary statistics",
    description="Retrieve computed summary statistics for simulation session",
    dependencies=[Depends(require_permission(Permission.DATA_READ))],
)
async def get_summary_statistics(
    session_id: str,
    request: Request,
    manager: SessionManager = Depends(get_session_manager),
    current_user: TokenPayload = Depends(get_current_user),
) -> SummaryStatistics:
    """
    Get summary statistics.

    Returns computed metrics including:
    - Duration and step count
    - Ignition event statistics
    - Energy consumption statistics
    - Allostatic regulation statistics

    Args:
        session_id: Unique session identifier
        request: HTTP request for authentication check
        manager: Session manager dependency

    Returns:
        SummaryStatistics with computed metrics

    Raises:
        HTTPException: If session not found or computation fails
    """
    try:
        # Get session
        sim_session = await manager.get_session(session_id)

        # Check ownership
        if sim_session.user_id != current_user.user_id and not has_any_role(
            current_user.roles, [Role.ADMIN]
        ):
            raise HTTPException(status_code=403, detail="Not authorized to access this session")

        # Get complete state to access history
        state = await sim_session.get_state()
        history = state.get("history", {})

        # Extract time series data
        times = history.get("time", [])
        ignitions = history.get("ignitions", [])
        free_energy = history.get("free_energy", [])
        allostatic_load = history.get("allostatic_load", [])

        # Basic statistics
        duration_ms = times[-1] if times else 0.0
        num_steps = len(times)

        # Ignition statistics
        ignition_count = sum(1 for ig in ignitions if ig)
        ignition_rate = ignition_count / num_steps if num_steps > 0 else 0.0

        ignition_stats = {
            "total_ignitions": ignition_count,
            "ignition_rate": ignition_rate,
            "average_ignition_interval_ms": (
                duration_ms / ignition_count if ignition_count > 0 else 0.0
            ),
        }

        # Energy statistics
        avg_free_energy = sum(free_energy) / len(free_energy) if free_energy else 0.0
        min_free_energy = min(free_energy) if free_energy else 0.0
        max_free_energy = max(free_energy) if free_energy else 0.0

        energy_stats = {
            "average_free_energy": avg_free_energy,
            "min_free_energy": min_free_energy,
            "max_free_energy": max_free_energy,
            "energy_variance": (
                sum((x - avg_free_energy) ** 2 for x in free_energy) / len(free_energy)
                if free_energy
                else 0.0
            ),
        }

        # Allostasis statistics
        avg_allostatic_load = (
            sum(allostatic_load) / len(allostatic_load) if allostatic_load else 0.0
        )
        min_allostatic_load = min(allostatic_load) if allostatic_load else 0.0
        max_allostatic_load = max(allostatic_load) if allostatic_load else 0.0

        allostasis_stats = {
            "average_allostatic_load": avg_allostatic_load,
            "min_allostatic_load": min_allostatic_load,
            "max_allostatic_load": max_allostatic_load,
            "final_allostatic_load": allostatic_load[-1] if allostatic_load else 0.0,
        }

        response = SummaryStatistics(
            session_id=session_id,
            duration_ms=duration_ms,
            num_steps=num_steps,
            ignition_stats=ignition_stats,
            energy_stats=energy_stats,
            allostasis_stats=allostasis_stats,
        )

        logger.info(f"Generated summary statistics for session {session_id}")
        return response

    except ValueError as e:
        logger.warning(f"Summary statistics generation failed for session {session_id}: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    except Exception:
        logger.error(
            f"Failed to generate summary statistics for session {session_id}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary statistics",
        )
