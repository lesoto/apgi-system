"""
User Management Routes

API endpoints for user management including registration,
password reset, and user administration.
"""

from datetime import datetime
from typing import Any, List, cast

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from api.database.connection import get_db
from api.exceptions import UserNotFoundError
from api.models.schemas import (
    ErrorResponse,
    UserCreateRequest,
    UserCreateResponse,
    UserResponse,
    UserUpdateRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    UserStatsResponse,
)
from api.services.authorization import (
    Permission,
    require_permission,
    get_current_user,
    TokenPayload,
    Role,
    has_any_role,
)
from api.services.user_management import get_user_management_service

router = APIRouter(
    prefix="/v1/users",
    tags=["User Management"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)


@router.post(
    "/register",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with auto-generated password if not provided",
    dependencies=[Depends(require_permission(Permission.USER_CREATE))],
)
async def register_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
) -> UserCreateResponse:
    """
    Register a new user.

    Args:
        request: User creation request
        db: Database session

    Returns:
        UserCreateResponse with user details and password

    Raises:
        HTTPException: If username already exists
    """
    user_service = get_user_management_service(db)

    try:
        user, password = user_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            roles=request.roles or ["researcher"],
        )

        return UserCreateResponse(
            user_id=cast(str, user.user_id),
            username=cast(str, user.username),
            email=cast(str, user.email),
            roles=cast(list[str], user.roles),
            password=password,  # Only returned once during creation
            created_at=cast(datetime, user.created_at),
            message="User created successfully",
        )

    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user data")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


@router.post(
    "/create-default",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create default system user",
    description="Create a default admin user for initial system setup",
    dependencies=[Depends(require_permission(Permission.USER_CREATE))],
)
async def create_default_user(
    db: Session = Depends(get_db),
) -> UserCreateResponse:
    """
    Create a default system user.

    Args:
        db: Database session
        user_service: User management service

    Returns:
        UserCreateResponse with default user details
    """
    user_service = get_user_management_service(db)

    try:
        user, password = user_service.create_default_user()

        return UserCreateResponse(
            user_id=cast(str, user.user_id),
            username=cast(str, user.username),
            email=cast(str, user.email),
            roles=cast(list[str], user.roles),
            password=password,
            created_at=cast(datetime, user.created_at),
            message="Default user created successfully",
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create default user",
        )


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List all users",
    description="Retrieve list of all users (requires admin privileges)",
    dependencies=[Depends(require_permission(Permission.USER_READ))],
)
async def list_users(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> List[UserResponse]:
    """
    List all users.

    Args:
        active_only: Only return active users
        db: Database session
        current_user: Authenticated user

    Returns:
        List of UserResponse objects

    Raises:
        HTTPException: If unauthorized
    """
    # Check if user can list inactive users
    is_admin = has_any_role(current_user.roles, [Role.ADMIN])
    if not active_only and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list inactive users",
        )

    user_service = get_user_management_service(db)
    users = user_service.list_users(active_only=active_only)

    return [
        UserResponse(
            user_id=cast(str, user.user_id),
            username=cast(str, user.username),
            email=cast(str, user.email),
            roles=cast(list[str], user.roles),
            is_active=cast(bool, user.is_active),
            created_at=cast(datetime, cast(Any, user.created_at)),
            updated_at=cast(datetime, cast(Any, user.updated_at)),
            last_login=cast(datetime | None, cast(Any, user.last_login)),
        )
        for user in users
    ]


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve profile of currently authenticated user",
    dependencies=[Depends(require_permission(Permission.USER_READ))],
)
async def get_current_user_profile(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Get current user profile.

    Args:
        current_user: Authenticated user token payload
        db: Database session
        user_service: User management service

    Returns:
        UserResponse object
    """
    user_service = get_user_management_service(db)
    user = user_service.get_user(current_user.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(
        user_id=cast(str, user.user_id),
        username=cast(str, user.username),
        email=cast(str, user.email),
        roles=cast(list[str], user.roles),
        is_active=cast(bool, user.is_active),
        created_at=cast(datetime, cast(Any, user.created_at)),
        updated_at=cast(datetime, cast(Any, user.updated_at)),
        last_login=cast(datetime | None, cast(Any, user.last_login)),
    )


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update profile of currently authenticated user",
    dependencies=[Depends(require_permission(Permission.USER_UPDATE))],
)
async def update_current_user_profile(
    request: UserUpdateRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Update current user profile.

    Users can update their own email. Only admins can change roles and active status.

    Args:
        request: User update request
        current_user: Authenticated user token payload
        db: Database session

    Returns:
        Updated UserResponse object

    Raises:
        HTTPException: If user not found or unauthorized
    """
    user_service = get_user_management_service(db)

    # Users can only update themselves
    user_id = current_user.user_id

    # Check permissions - users can update their own email, but only admins can change roles/active status
    is_admin = has_any_role(current_user.roles, [Role.ADMIN])

    try:
        user = user_service.update_user(
            user_id=user_id,
            email=request.email,
            roles=request.roles if is_admin else None,  # Only admins can change roles
            is_active=(
                request.is_active if is_admin else None
            ),  # Only admins can change active status
        )

        return UserResponse(
            user_id=cast(str, user.user_id),
            username=cast(str, user.username),
            email=cast(str, user.email),
            roles=cast(list[str], user.roles),
            is_active=cast(bool, user.is_active),
            created_at=cast(datetime, cast(Any, user.created_at)),
            updated_at=cast(datetime, cast(Any, user.updated_at)),
            last_login=cast(datetime | None, cast(Any, user.last_login)),
        )

    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.get(
    "/stats",
    response_model=UserStatsResponse,
    summary="Get user statistics",
    description="Retrieve user statistics (requires admin privileges)",
    dependencies=[Depends(require_permission(Permission.USER_READ))],
)
async def get_user_stats(
    db: Session = Depends(get_db),
) -> UserStatsResponse:
    """
    Get user statistics.

    Args:
        db: Database session
        user_service: User management service

    Returns:
        UserStatsResponse object
    """
    user_service = get_user_management_service(db)
    stats = user_service.get_user_stats()

    return UserStatsResponse(
        total_users=stats["total_users"],
        active_users=stats["active_users"],
        inactive_users=stats["inactive_users"],
        role_counts=cast(dict[str, int], stats["role_counts"]),
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve specific user information (requires admin privileges)",
    dependencies=[Depends(require_permission(Permission.USER_READ))],
)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Get user by ID.

    Args:
        user_id: User identifier
        db: Database session
        user_service: User management service

    Returns:
        UserResponse object

    Raises:
        HTTPException: If user not found
    """
    user_service = get_user_management_service(db)
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(
        user_id=cast(str, user.user_id),
        username=cast(str, user.username),
        email=cast(str, user.email),
        roles=cast(list[str], user.roles),
        is_active=cast(bool, user.is_active),
        created_at=cast(datetime, cast(Any, user.created_at)),
        updated_at=cast(datetime, cast(Any, user.updated_at)),
        last_login=cast(datetime | None, cast(Any, user.last_login)),
    )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user information (requires admin privileges or own user)",
)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> UserResponse:
    """
    Update user information.

    Args:
        user_id: User identifier
        request: User update request
        db: Database session
        user_service: User management service
        current_user: Authenticated user

    Returns:
        Updated UserResponse object

    Raises:
        HTTPException: If user not found or unauthorized
    """
    user_service = get_user_management_service(db)
    # Check permissions (admin can update any user, users can only update themselves)
    is_admin = has_any_role(current_user.roles, [Role.ADMIN])
    is_own_user = current_user.user_id == user_id

    if not (is_admin or is_own_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user"
        )

    try:
        user = user_service.update_user(
            user_id=user_id,
            email=request.email,
            roles=request.roles if is_admin else None,  # Only admins can change roles
            is_active=(
                request.is_active if is_admin else None
            ),  # Only admins can change active status
        )

        return UserResponse(
            user_id=cast(str, user.user_id),
            username=cast(str, user.username),
            email=cast(str, user.email),
            roles=cast(list[str], user.roles),
            is_active=cast(bool, user.is_active),
            created_at=cast(datetime, cast(Any, user.created_at)),
            updated_at=cast(datetime, cast(Any, user.updated_at)),
            last_login=cast(datetime | None, cast(Any, user.last_login)),
        )

    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.post(
    "/{user_id}/reset-password",
    response_model=PasswordResetResponse,
    summary="Reset user password",
    description="Reset user password (requires admin privileges or own user)",
)
async def reset_user_password(
    user_id: str,
    request: PasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> PasswordResetResponse:
    """
    Reset user password.

    Args:
        user_id: User identifier
        request: Password reset request
        db: Database session
        user_service: User management service
        current_user: Authenticated user

    Returns:
        PasswordResetResponse with new password

    Raises:
        HTTPException: If user not found or unauthorized
    """
    user_service = get_user_management_service(db)
    # Check permissions
    is_admin = has_any_role(current_user.roles, [Role.ADMIN])
    is_own_user = current_user.user_id == user_id

    if not (is_admin or is_own_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reset this user's password",
        )

    try:
        new_password = user_service.reset_password(  # noqa: F841
            user_id=user_id, new_password=request.new_password
        )

        return PasswordResetResponse(user_id=user_id, message="Password reset successfully")

    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete user account (requires admin privileges)",
    dependencies=[Depends(require_permission(Permission.USER_DELETE))],
)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete user.

    Args:
        user_id: User identifier
        db: Database session
        user_service: User management service

    Raises:
        HTTPException: If user not found
    """
    user_service = get_user_management_service(db)
    try:
        deleted = user_service.delete_user(user_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )
