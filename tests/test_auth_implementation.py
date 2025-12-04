"""
Basic tests for authentication implementation.

Tests the core authentication functionality to ensure it works correctly.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from api.services.auth_manager import AuthManager, TokenPayload
from api.services.authorization import (
    Role,
    Permission,
    get_permissions_for_roles,
    has_permission,
    check_permission,
)
from api.database.models import User, RefreshToken
from api.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    ExpiredTokenError,
    AuthorizationError,
)


class TestAuthManager:
    """Test AuthManager functionality."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"

        # Hash password
        hashed = AuthManager.hash_password(password)

        # Verify correct password
        assert AuthManager.verify_password(password, hashed)

        # Verify incorrect password fails
        assert not AuthManager.verify_password("wrong_password", hashed)

    def test_create_access_token(self, db: Session):
        """Test access token creation."""
        auth_manager = AuthManager(db)

        # Create token
        token = auth_manager.create_access_token(
            user_id="test_user_123", username="testuser", roles=["researcher"]
        )

        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        payload = auth_manager.verify_token(token, expected_type="access")
        assert payload.user_id == "test_user_123"
        assert payload.username == "testuser"
        assert payload.roles == ["researcher"]
        assert payload.token_type == "access"

    def test_create_refresh_token(self, db: Session):
        """Test refresh token creation."""
        auth_manager = AuthManager(db)

        # Create token
        token = auth_manager.create_refresh_token(
            user_id="test_user_123", username="testuser", roles=["researcher"]
        )

        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        payload = auth_manager.verify_token(token, expected_type="refresh")
        assert payload.user_id == "test_user_123"
        assert payload.username == "testuser"
        assert payload.roles == ["researcher"]
        assert payload.token_type == "refresh"

    def test_verify_token_wrong_type(self, db: Session):
        """Test that verifying token with wrong type fails."""
        auth_manager = AuthManager(db)

        # Create access token
        access_token = auth_manager.create_access_token(
            user_id="test_user_123", username="testuser", roles=["researcher"]
        )

        # Try to verify as refresh token (should fail)
        with pytest.raises(InvalidTokenError):
            auth_manager.verify_token(access_token, expected_type="refresh")

    def test_verify_invalid_token(self, db: Session):
        """Test that invalid tokens are rejected."""
        auth_manager = AuthManager(db)

        # Try to verify invalid token
        with pytest.raises(InvalidTokenError):
            auth_manager.verify_token("invalid_token_string", expected_type="access")


class TestAuthorization:
    """Test authorization functionality."""

    def test_role_permissions(self):
        """Test that roles have correct permissions."""
        # Admin should have all permissions
        admin_perms = get_permissions_for_roles(["admin"])
        assert Permission.SESSION_CREATE in admin_perms
        assert Permission.SYSTEM_ADMIN in admin_perms
        assert Permission.USER_MANAGE in admin_perms

        # Researcher should have session and task permissions
        researcher_perms = get_permissions_for_roles(["researcher"])
        assert Permission.SESSION_CREATE in researcher_perms
        assert Permission.TASK_CREATE in researcher_perms
        assert Permission.SYSTEM_ADMIN not in researcher_perms

        # Viewer should only have read permissions
        viewer_perms = get_permissions_for_roles(["viewer"])
        assert Permission.SESSION_READ in viewer_perms
        assert Permission.SESSION_CREATE not in viewer_perms
        assert Permission.TASK_CREATE not in viewer_perms

    def test_has_permission(self):
        """Test permission checking."""
        # Admin has all permissions
        assert has_permission(["admin"], Permission.SESSION_CREATE)
        assert has_permission(["admin"], Permission.SYSTEM_ADMIN)

        # Researcher has session permissions
        assert has_permission(["researcher"], Permission.SESSION_CREATE)
        assert not has_permission(["researcher"], Permission.SYSTEM_ADMIN)

        # Viewer only has read permissions
        assert has_permission(["viewer"], Permission.SESSION_READ)
        assert not has_permission(["viewer"], Permission.SESSION_CREATE)

    def test_check_permission_raises(self):
        """Test that check_permission raises AuthorizationError when lacking permission."""
        # Viewer trying to create session should fail
        with pytest.raises(AuthorizationError) as exc_info:
            check_permission(
                user_roles=["viewer"],
                required_permission=Permission.SESSION_CREATE,
                resource="session",
                action="create",
            )

        assert exc_info.value.status_code == 403
        assert "session" in exc_info.value.message.lower()


class TestTokenPayload:
    """Test TokenPayload class."""

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        exp_time = datetime.utcnow() + timedelta(hours=1)

        # Create payload
        payload = TokenPayload(
            user_id="test_123",
            username="testuser",
            roles=["researcher", "viewer"],
            exp=exp_time,
            token_type="access",
        )

        # Convert to dict
        payload_dict = payload.to_dict()
        assert payload_dict["user_id"] == "test_123"
        assert payload_dict["username"] == "testuser"
        assert payload_dict["roles"] == ["researcher", "viewer"]
        assert payload_dict["token_type"] == "access"

        # Convert back from dict
        restored = TokenPayload.from_dict(payload_dict)
        assert restored.user_id == payload.user_id
        assert restored.username == payload.username
        assert restored.roles == payload.roles
        assert restored.token_type == payload.token_type


def test_authentication_integration(db: Session):
    """Integration test for authentication flow."""
    auth_manager = AuthManager(db)

    # Create a test user
    user = User(
        user_id="test_user_123",
        username="testuser",
        email="test@example.com",
        password_hash=AuthManager.hash_password("test_password"),
        roles=["researcher"],
    )
    db.add(user)
    db.commit()

    # Authenticate user
    authenticated_user = auth_manager.authenticate_user("testuser", "test_password")
    assert authenticated_user is not None
    assert authenticated_user.username == "testuser"

    # Create tokens
    tokens = auth_manager.create_tokens_for_user(authenticated_user)
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # Verify access token
    access_payload = auth_manager.verify_token(tokens["access_token"], expected_type="access")
    assert access_payload.user_id == "test_user_123"
    assert access_payload.username == "testuser"

    # Verify refresh token
    refresh_payload = auth_manager.verify_token(tokens["refresh_token"], expected_type="refresh")
    assert refresh_payload.user_id == "test_user_123"

    # Refresh access token
    new_tokens = auth_manager.refresh_access_token(tokens["refresh_token"])
    assert "access_token" in new_tokens

    # Verify new access token works
    new_payload = auth_manager.verify_token(new_tokens["access_token"], expected_type="access")
    assert new_payload.user_id == "test_user_123"

    # Logout (revoke refresh token)
    revoked = auth_manager.revoke_refresh_token(tokens["refresh_token"])
    assert revoked

    # Try to use revoked refresh token (should fail)
    with pytest.raises(AuthenticationError):
        auth_manager.refresh_access_token(tokens["refresh_token"])

    # Clean up
    db.delete(user)
    db.commit()
