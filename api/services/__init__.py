"""
API Services

Business logic layer for the APGI REST API.
"""

from api.services.session_manager import SessionManager, SimulationSession, SessionLifecycleState
from api.services.health_check import HealthCheckService
from api.services.auth_manager import AuthManager, TokenPayload
from api.services.authorization import (
    Role,
    Permission,
    get_current_user,
    require_permission,
    require_role,
    require_any_role,
    check_resource_ownership,
)

__all__ = [
    "SessionManager",
    "SimulationSession",
    "SessionLifecycleState",
    "HealthCheckService",
    "AuthManager",
    "TokenPayload",
    "Role",
    "Permission",
    "get_current_user",
    "require_permission",
    "require_role",
    "require_any_role",
    "check_resource_ownership",
]
