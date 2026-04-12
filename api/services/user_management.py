"""
User Management Service

Provides comprehensive user management functionality including:
- Automated user provisioning
- User registration and management
- Password reset functionality
- Role-based access control
"""

import secrets
import string
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database.models import User
from api.exceptions import UserNotFoundError
from api.services.auth_manager import AuthManager


class UserManagementService:
    """
    Comprehensive user management service.

    Handles user creation, provisioning, password management,
    and role-based access control.
    """

    def __init__(self, db: Session):
        """
        Initialize user management service.

        Args:
            db: Database session
        """
        self.db = db
        self.auth_manager = AuthManager(db)

    def generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a secure random password.

        Args:
            length: Password length (default 16)

        Returns:
            Secure random password string
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        return password

    def generate_username(self, prefix: str = "user", suffix_length: int = 8) -> str:
        """
        Generate a unique username.

        Args:
            prefix: Username prefix
            suffix_length: Length of random suffix

        Returns:
            Unique username
        """
        suffix = "".join(
            secrets.choice(string.ascii_lowercase + string.digits) for _ in range(suffix_length)
        )
        username = f"{prefix}_{suffix}"

        # Ensure uniqueness
        counter = 1
        original_username = username
        while self._username_exists(username):
            username = f"{original_username}_{counter}"
            counter += 1

        return username

    def _username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        stmt = select(User).where(User.username == username)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def create_user(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        roles: Optional[List[str]] = None,
        is_default: bool = False,
    ) -> Tuple[User, str]:
        """
        Create a new user with optional auto-generated credentials.

        Args:
            username: Username (auto-generated if None)
            email: Email address
            password: Password (auto-generated if None)
            roles: List of roles (default: ['user'])
            is_default: Whether this is a default system user

        Returns:
            Tuple of (User object, plain_text_password)

        Raises:
            ValueError: If username already exists
        """
        # Generate username if not provided
        if not username:
            prefix = "default" if is_default else "user"
            username = self.generate_username(prefix)

        # Check if username exists
        if self._username_exists(username):
            raise ValueError(f"Username '{username}' already exists")

        # Generate password if not provided
        if not password:
            password = self.generate_secure_password()

        # Set default roles
        if not roles:
            roles = ["admin"] if is_default else ["user"]

        # Hash password
        password_hash = self.auth_manager.hash_password(password)

        # Create user
        user = User(
            username=username,
            email=email or f"{username}@apgi.local",
            password_hash=password_hash,
            roles=roles,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Save to database
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user, password

    def create_default_user(self) -> Tuple[User, str]:
        """
        Create a default system user for initial setup.

        Returns:
            Tuple of (User object, plain_text_password)
        """
        # Check if default user already exists
        stmt = select(User).where(User.username.like("default_%"))
        result = self.db.execute(stmt)
        existing = result.scalars().all()

        if existing:
            # Return existing default user
            user = existing[0]
            return user, "Password already set - check server logs"

        # Create new default user
        user, password = self.create_user(
            username=None,  # Auto-generate
            email="admin@apgi.local",
            password=None,  # Auto-generate
            roles=["admin"],
            is_default=True,
        )

        return user, password

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User identifier

        Returns:
            User object or None if not found
        """
        stmt = select(User).where(User.user_id == user_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User object or None if not found
        """
        stmt = select(User).where(User.username == username)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def update_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        roles: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
    ) -> User:
        """
        Update user information.

        Args:
            user_id: User identifier
            email: New email address
            roles: New roles list
            is_active: New active status

        Returns:
            Updated User object

        Raises:
            UserNotFoundError: If user not found
        """
        user = self.get_user(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Update fields
        if email is not None:
            user.email = email  # type: ignore[assignment]
        if roles is not None:
            user.roles = roles  # type: ignore[assignment]
        if is_active is not None:
            user.is_active = is_active  # type: ignore[assignment]

        user.updated_at = datetime.utcnow()  # type: ignore[assignment]
        self.db.commit()
        self.db.refresh(user)

        return user

    def reset_password(self, user_id: str, new_password: Optional[str] = None) -> str:
        """
        Reset user password.

        Args:
            user_id: User identifier
            new_password: New password (auto-generated if None)

        Returns:
            New plain text password

        Raises:
            UserNotFoundError: If user not found
        """
        user = self.get_user(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Generate new password if not provided
        if not new_password:
            new_password = self.generate_secure_password()

        # Hash and update password
        user.password_hash = self.auth_manager.hash_password(new_password)  # type: ignore[assignment]
        user.updated_at = datetime.utcnow()  # type: ignore[assignment]

        self.db.commit()

        return new_password

    def list_users(self, active_only: bool = True) -> List[User]:
        """
        List all users.

        Args:
            active_only: Only return active users

        Returns:
            List of User objects
        """
        stmt = select(User)
        if active_only:
            stmt = stmt.where(User.is_active.is_(True))

        stmt = stmt.order_by(User.created_at.desc())
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: User identifier

        Returns:
            True if user was deleted, False if not found
        """
        user = self.get_user(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()

        return True

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        return self.auth_manager.authenticate_user(username, password)

    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics.

        Returns:
            Dictionary with user statistics
        """
        total_users = len(self.list_users(active_only=False))
        active_users = len(self.list_users(active_only=True))

        # Count by role
        stmt = select(User)
        result = self.db.execute(stmt)
        all_users = result.scalars().all()

        role_counts: dict[str, int] = {}
        for user in all_users:
            for role in user.roles:  # type: ignore[attr-defined]
                role_counts[role] = role_counts.get(role, 0) + 1

        # Sort role_counts for consistent ordering (alphabetical by role name)
        sorted_role_counts = dict(sorted(role_counts.items()))

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "role_counts": sorted_role_counts,
        }


def get_user_management_service(db: Session) -> UserManagementService:
    """
    Get user management service instance.

    Args:
        db: Database session

    Returns:
        UserManagementService instance
    """
    return UserManagementService(db)
