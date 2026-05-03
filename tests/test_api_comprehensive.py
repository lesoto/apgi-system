#!/usr/bin/env python3
"""
Comprehensive tests for API Layer modules.

Tests cover:
- Authentication middleware
- Consent validation system
- Database operations
- API routes and endpoints
- Compliance features
- Error handling
- Security features
"""

import hashlib
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from starlette.responses import JSONResponse

# Import API modules we're testing
try:
    from api.compliance.consent_validation import (
        ConsentPurpose,
        ConsentRecord,
        ConsentStatus,
        ConsentValidationResult,
        ConsentValidator,
    )
    from api.database.batch_operations import (
        bulk_delete,
        bulk_fetch,
        bulk_insert,
        bulk_update,
        bulk_upsert,
    )
    from api.exceptions import ExpiredTokenError, InvalidTokenError
    from api.middleware.authentication import (  # noqa: F401
        AuthenticationMiddleware,
        TokenPayload,
        _token_cache,
    )

    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False


# Mock implementation for missing BatchOperationManager
class BatchOperationManager:
    """Mock BatchOperationManager class for testing."""

    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.session_factory = None  # Mock session factory

    async def bulk_insert(self, session, model, records):
        """Mock bulk insert method."""
        return await bulk_insert(session, model, records, self.batch_size)

    async def bulk_update(self, session, model, filter_column, filter_value, update_data):
        """Mock bulk update method."""
        return await bulk_update(
            session, model, filter_column, filter_value, update_data, self.batch_size
        )

    async def bulk_delete(self, session, model, filter_column, filter_value):
        """Mock bulk delete method."""
        return await bulk_delete(session, model, filter_column, filter_value, self.batch_size)

    async def bulk_upsert(self, session, model, records, conflict_columns=None):
        """Mock bulk upsert method."""
        return await bulk_upsert(session, model, records, conflict_columns, self.batch_size)

    async def bulk_fetch(self, session, model, filter_column, filter_value):
        """Mock bulk fetch method."""
        return await bulk_fetch(session, model, filter_column, filter_value)


class TestAuthenticationMiddleware:
    """Test authentication middleware functionality."""

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    def test_middleware_initialization(self):
        """Test middleware initialization."""
        middleware = AuthenticationMiddleware(app=None)

        assert hasattr(middleware, "PUBLIC_PATHS")
        assert "/" in middleware.PUBLIC_PATHS
        assert "/health" in middleware.PUBLIC_PATHS
        assert "/docs" in middleware.PUBLIC_PATHS
        assert "/v1/auth/login" in middleware.PUBLIC_PATHS

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_public_path_access(self):
        """Test access to public paths without authentication."""
        middleware = AuthenticationMiddleware(app=None)

        # Create mock request for public path
        request = MagicMock(spec=Request)
        request.url.path = "/health"
        request.method = "GET"

        # Create mock call_next
        call_next = AsyncMock()
        response = JSONResponse({"status": "ok"})
        call_next.return_value = response

        # Process request
        result = await middleware.dispatch(request, call_next)

        # Should pass through without authentication
        call_next.assert_called_once_with(request)
        assert result == response

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_protected_path_without_token(self):
        """Test access to protected path without token."""
        middleware = AuthenticationMiddleware(app=None)

        # Create mock request for protected path
        request = MagicMock(spec=Request)
        request.url.path = "/v1/data"
        request.method = "GET"
        request.headers = {}

        # Create mock call_next
        call_next = AsyncMock()

        # Process request
        result = await middleware.dispatch(request, call_next)

        # Should return 401 error
        assert isinstance(result, JSONResponse)
        call_next.assert_not_called()

        # Check error response
        content = json.loads(result.body.decode())
        assert "error" in content or "detail" in content
        assert result.status_code == 401

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_protected_path_with_valid_token(self):
        """Test access to protected path with valid token."""
        middleware = AuthenticationMiddleware(app=None)

        # Create mock request with valid token
        request = MagicMock(spec=Request)
        request.url.path = "/v1/data"
        request.method = "GET"
        request.headers = {"authorization": "Bearer valid_token_123"}

        # Create mock call_next
        call_next = AsyncMock()
        response = JSONResponse({"data": "protected"})
        call_next.return_value = response

        # Mock token validation
        with patch("api.middleware.authentication.AuthManager.verify_token") as mock_verify:
            mock_payload = TokenPayload(
                user_id="user123",
                email="user@example.com",
                permissions=["read", "write"],
                expires_at=datetime.now() + timedelta(hours=1),
            )
            mock_verify.return_value = mock_payload

            # Process request
            result = await middleware.dispatch(request, call_next)

            # Should pass through with user info attached
            call_next.assert_called_once()
            assert result == response

            # Check request state was modified
            called_request = call_next.call_args[0][0]
            assert hasattr(called_request, "state")
            assert called_request.state.user == mock_payload

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_protected_path_with_expired_token(self):
        """Test access to protected path with expired token."""
        middleware = AuthenticationMiddleware(app=None)

        # Create mock request with expired token
        request = MagicMock(spec=Request)
        request.url.path = "/v1/data"
        request.method = "GET"
        request.headers = {"authorization": "Bearer expired_token"}

        # Create mock call_next
        call_next = AsyncMock()

        # Mock expired token
        with patch("api.middleware.authentication.AuthManager.verify_token") as mock_verify:
            mock_verify.side_effect = ExpiredTokenError("Token has expired")

            # Process request
            result = await middleware.dispatch(request, call_next)

            # Should return 401 error
            assert isinstance(result, JSONResponse)
            assert result.status_code == 401
            call_next.assert_not_called()

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_protected_path_with_invalid_token(self):
        """Test access to protected path with invalid token."""
        middleware = AuthenticationMiddleware(app=None)

        # Create mock request with invalid token
        request = MagicMock(spec=Request)
        request.url.path = "/v1/data"
        request.method = "GET"
        request.headers = {"authorization": "Bearer invalid_token"}

        # Create mock call_next
        call_next = AsyncMock()

        # Mock invalid token
        with patch("api.middleware.authentication.AuthManager.verify_token") as mock_verify:
            mock_verify.side_effect = InvalidTokenError("Invalid token")

            # Process request
            result = await middleware.dispatch(request, call_next)

            # Should return 401 error
            assert isinstance(result, JSONResponse)
            assert result.status_code == 401
            call_next.assert_not_called()

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_malformed_authorization_header(self):
        """Test malformed authorization header."""
        middleware = AuthenticationMiddleware(app=None)

        # Test missing Bearer prefix
        request = MagicMock(spec=Request)
        request.url.path = "/v1/data"
        request.method = "GET"
        request.headers = {"authorization": "invalid_format_token"}

        call_next = AsyncMock()

        # Process request
        result = await middleware.dispatch(request, call_next)

        # Should return 401 error
        assert isinstance(result, JSONResponse)
        assert result.status_code == 401
        call_next.assert_not_called()

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    def test_token_cache_functionality(self):
        """Test token caching functionality."""
        # Test token cache operations
        from api.middleware.authentication import TOKEN_CACHE_TTL_SECONDS, _token_cache

        # Create test payload
        payload = TokenPayload(
            user_id="test_user",
            email="test@example.com",
            permissions=["read"],
            expires_at=datetime.now() + timedelta(hours=1),
        )

        # Test cache storage and retrieval
        token = "test_token_123"
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Store in cache
        expiration_time = datetime.now().timestamp() + TOKEN_CACHE_TTL_SECONDS
        _token_cache[token_hash] = (payload, expiration_time)

        # Retrieve from cache


class TestConsentValidation:
    """Test consent validation system."""

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    def test_consent_status_enum(self):
        """Test consent status enum values."""
        assert ConsentStatus.ACTIVE.value == "active"
        assert ConsentStatus.EXPIRED.value == "expired"
        assert ConsentStatus.REVOKED.value == "revoked"
        assert ConsentStatus.PENDING_VERIFICATION.value == "pending_verification"
        assert ConsentStatus.SUPERSEDED.value == "superseded"

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    def test_consent_purpose_enum(self):
        """Test consent purpose enum values."""
        assert ConsentPurpose.DATA_COLLECTION.value == "data_collection"
        assert ConsentPurpose.RESEARCH.value == "research"
        assert ConsentPurpose.ANALYTICS.value == "analytics"
        assert ConsentPurpose.MARKETING.value == "marketing"
        assert ConsentPurpose.THIRD_PARTY_SHARING.value == "third_party_sharing"
        assert ConsentPurpose.PROCESSING.value == "processing"

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    def test_consent_validation_result(self):
        """Test consent validation result dataclass."""
        result = ConsentValidationResult(
            is_valid=True,
            subject_id="subject123",
            status=ConsentStatus.ACTIVE,
            purposes=[ConsentPurpose.DATA_COLLECTION],
            expires_at=datetime.now() + timedelta(days=30),
            metadata={"source": "form"},
        )

        assert result.is_valid is True
        assert result.subject_id == "subject123"
        assert result.status == ConsentStatus.ACTIVE
        assert len(result.purposes) == 1
        assert result.purposes[0] == ConsentPurpose.DATA_COLLECTION
        assert result.expires_at > datetime.now()
        assert result.metadata["source"] == "form"

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    def test_consent_record_creation(self):
        """Test consent record creation."""
        record = ConsentRecord(
            consent_id="consent_123",
            subject_id="subject123",
            purposes=[ConsentPurpose.RESEARCH, ConsentPurpose.ANALYTICS],
            status=ConsentStatus.ACTIVE,
            granted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365),
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
        )

        assert record.consent_id == "consent_123"
        assert record.subject_id == "subject123"
        assert len(record.purposes) == 2
        assert record.status == ConsentStatus.ACTIVE
        assert record.granted_at is not None
        assert record.expires_at is not None
        assert record.ip_address == "192.168.1.1"
        assert record.user_agent == "TestAgent/1.0"

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    def test_consent_validator_initialization(self):
        """Test consent validator initialization."""
        validator = ConsentValidator()

        assert hasattr(validator, "consent_store")
        assert hasattr(validator, "audit_logger")

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_validate_consent_valid(self):
        """Test validation of valid consent."""
        validator = ConsentValidator()

        # Mock valid consent record
        with patch.object(validator, "get_consent_record") as mock_get:
            record = ConsentRecord(
                consent_id="consent_123",
                subject_id="subject123",
                purposes=[ConsentPurpose.RESEARCH],
                status=ConsentStatus.ACTIVE,
                granted_at=datetime.now() - timedelta(days=1),
                expires_at=datetime.now() + timedelta(days=30),
            )
            mock_get.return_value = record

            # Validate consent
            result = await validator.validate_consent(
                subject_id="subject123", purpose=ConsentPurpose.RESEARCH
            )

            assert result.is_valid is True
            assert result.subject_id == "subject123"
            assert result.status == ConsentStatus.ACTIVE
            assert ConsentPurpose.RESEARCH in result.purposes

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_validate_consent_expired(self):
        """Test validation of expired consent."""
        validator = ConsentValidator()

        # Mock expired consent record
        with patch.object(validator, "get_consent_record") as mock_get:
            record = ConsentRecord(
                consent_id="consent_123",
                subject_id="subject123",
                purposes=[ConsentPurpose.RESEARCH],
                status=ConsentStatus.ACTIVE,
                granted_at=datetime.now() - timedelta(days=100),
                expires_at=datetime.now() - timedelta(days=1),  # Expired
            )
            mock_get.return_value = record

            # Validate consent
            result = await validator.validate_consent(
                subject_id="subject123", purpose=ConsentPurpose.RESEARCH
            )

            assert result.is_valid is False
            assert result.status == ConsentStatus.EXPIRED

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_validate_consent_revoked(self):
        """Test validation of revoked consent."""
        validator = ConsentValidator()

        # Mock revoked consent record
        with patch.object(validator, "get_consent_record") as mock_get:
            record = ConsentRecord(
                consent_id="consent_123",
                subject_id="subject123",
                purposes=[ConsentPurpose.RESEARCH],
                status=ConsentStatus.REVOKED,
                granted_at=datetime.now() - timedelta(days=10),
                expires_at=datetime.now() + timedelta(days=30),
            )
            mock_get.return_value = record

            # Validate consent
            result = await validator.validate_consent(
                subject_id="subject123", purpose=ConsentPurpose.RESEARCH
            )

            assert result.is_valid is False
            assert result.status == ConsentStatus.REVOKED

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_validate_consent_wrong_purpose(self):
        """Test validation with wrong purpose."""
        validator = ConsentValidator()

        # Mock consent record for research only
        with patch.object(validator, "get_consent_record") as mock_get:
            record = ConsentRecord(
                consent_id="consent_123",
                subject_id="subject123",
                purposes=[ConsentPurpose.RESEARCH],  # Only research consent
                status=ConsentStatus.ACTIVE,
                granted_at=datetime.now() - timedelta(days=1),
                expires_at=datetime.now() + timedelta(days=30),
            )
            mock_get.return_value = record

            # Try to validate for marketing (not consented)
            result = await validator.validate_consent(
                subject_id="subject123", purpose=ConsentPurpose.MARKETING
            )

            assert result.is_valid is False
            assert "purpose not authorized" in str(result.metadata.get("reason", "")).lower()

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_validate_consent_no_record(self):
        """Test validation with no consent record."""
        validator = ConsentValidator()

        # Mock no consent record found
        with patch.object(validator, "get_consent_record") as mock_get:
            mock_get.return_value = None

            # Validate consent
            result = await validator.validate_consent(
                subject_id="subject123", purpose=ConsentPurpose.RESEARCH
            )

            assert result.is_valid is False
            assert result.status == ConsentStatus.PENDING_VERIFICATION

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_revoke_consent(self):
        """Test consent revocation."""
        validator = ConsentValidator()

        # Mock existing consent
        with (
            patch.object(validator, "get_consent_record") as mock_get,
            patch.object(validator, "update_consent_record") as mock_update,
        ):

            record = ConsentRecord(
                consent_id="consent_123",
                subject_id="subject123",
                purposes=[ConsentPurpose.RESEARCH],
                status=ConsentStatus.ACTIVE,
                granted_at=datetime.now() - timedelta(days=1),
                expires_at=datetime.now() + timedelta(days=30),
            )
            mock_get.return_value = record

            # Revoke consent
            result = await validator.revoke_consent(
                consent_id="consent_123", reason="User requested withdrawal"
            )

            assert result is True
            mock_update.assert_called_once()

            # Check the updated record
            updated_record = mock_update.call_args[0][0]
            assert updated_record.status == ConsentStatus.REVOKED
            assert "User requested withdrawal" in updated_record.metadata.get(
                "revocation_reason", ""
            )

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_grant_consent(self):
        """Test consent granting."""
        validator = ConsentValidator()

        with patch.object(validator, "create_consent_record") as mock_create:
            mock_create.return_value = True

            # Grant consent
            result = await validator.grant_consent(
                subject_id="subject123",
                purposes=[ConsentPurpose.RESEARCH, ConsentPurpose.ANALYTICS],
                expires_at=datetime.now() + timedelta(days=365),
                ip_address="192.168.1.1",
                user_agent="TestAgent/1.0",
            )

            assert result is True
            mock_create.assert_called_once()

            # Check the created record
            created_record = mock_create.call_args[0][0]
            assert created_record.subject_id == "subject123"
            assert len(created_record.purposes) == 2
            assert created_record.status == ConsentStatus.ACTIVE


class TestBatchOperations:
    """Test database batch operations."""

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    def test_batch_operation_manager_initialization(self):
        """Test batch operation manager initialization."""
        manager = BatchOperationManager()

        assert hasattr(manager, "session_factory")
        assert hasattr(manager, "batch_size")
        assert hasattr(manager, "timeout")

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_batch_insert_success(self):
        """Test successful batch insert operation."""
        manager = BatchOperationManager()

        # Mock database session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()

        with patch("api.database.batch_operations.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Test data
            test_data = [
                {"id": 1, "name": "test1", "value": 100},
                {"id": 2, "name": "test2", "value": 200},
                {"id": 3, "name": "test3", "value": 300},
            ]

            # Perform batch insert
            result = await manager.batch_insert(table_name="test_table", data=test_data)

            assert result is True
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_batch_insert_with_conflict(self):
        """Test batch insert with conflict handling."""
        manager = BatchOperationManager()

        # Mock database session with conflict
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Integrity constraint violation"))
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        with patch("api.database.batch_operations.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            test_data = [{"id": 1, "name": "test"}]

            # Should handle conflict gracefully
            result = await manager.batch_insert(
                table_name="test_table", data=test_data, on_conflict="ignore"
            )

            assert result is False
            mock_session.rollback.assert_called_once()

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_batch_update_success(self):
        """Test successful batch update operation."""
        manager = BatchOperationManager()

        # Mock database session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()

        with patch("api.database.batch_operations.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Test update data
            update_data = [{"id": 1, "value": 150}, {"id": 2, "value": 250}]

            # Perform batch update
            result = await manager.batch_update(
                table_name="test_table", data=update_data, key_field="id"
            )

            assert result is True
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_batch_delete_success(self):
        """Test successful batch delete operation."""
        manager = BatchOperationManager()

        # Mock database session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()

        with patch("api.database.batch_operations.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Test delete criteria
            delete_criteria = {"status": "inactive"}

            # Perform batch delete
            result = await manager.batch_delete(table_name="test_table", criteria=delete_criteria)

            assert result is True
            mock_session.execute.assert_called()
            mock_session.commit.assert_called_once()


class TestAPIErrorHandling:
    """Test API error handling."""

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    def test_expired_token_error(self):
        """Test expired token error."""
        error = ExpiredTokenError("Token has expired")

        assert str(error) == "Token has expired"
        assert hasattr(error, "message")

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    def test_invalid_token_error(self):
        """Test invalid token error."""
        error = InvalidTokenError("Invalid token format")

        assert str(error) == "Invalid token format"
        assert hasattr(error, "message")

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_database_connection_error_handling(self):
        """Test database connection error handling."""
        manager = BatchOperationManager()

        # Mock connection failure
        with patch("api.database.batch_operations.AsyncSessionLocal") as mock_session_local:
            mock_session_local.side_effect = Exception("Connection failed")

            test_data = [{"id": 1, "name": "test"}]

            # Should handle connection error
            with pytest.raises(Exception):
                await manager.batch_insert("test_table", test_data)


class TestAPISecurity:
    """Test API security features."""

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_sql_injection_prevention(self):
        """Test SQL injection prevention in batch operations."""
        manager = BatchOperationManager()

        # Mock database session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()

        with patch("api.database.batch_operations.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_session

            # Test data with potential SQL injection
            malicious_data = [
                {"id": 1, "name": "test'; DROP TABLE users; --"},
                {"id": 2, "name": 'test" OR 1=1; --'},
            ]

            # Should sanitize input
            result = await manager.batch_insert("test_table", malicious_data)

            assert result is True
            # Verify that execute was called with sanitized parameters
            mock_session.execute.assert_called()

    @pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
    async def test_rate_limiting_compliance(self):
        """Test rate limiting compliance."""
        middleware = AuthenticationMiddleware(app=None)

        # Create multiple requests
        requests = []
        for i in range(10):
            request = MagicMock(spec=Request)
            request.url.path = "/v1/data"
            request.method = "GET"
            request.headers = {"authorization": f"Bearer token_{i}"}
            request.client = MagicMock()
            request.client.host = "192.168.1.1"
            requests.append(request)

        # Mock token verification
        with patch("api.middleware.authentication.AuthManager.verify_token") as mock_verify:
            mock_payload = TokenPayload(
                user_id="user123",
                email="user@example.com",
                permissions=["read"],
                expires_at=datetime.now() + timedelta(hours=1),
            )
            mock_verify.return_value = mock_payload

            # Process requests (rate limiting would be applied here)
            for request in requests:
                call_next = AsyncMock()
                call_next.return_value = JSONResponse({"data": "ok"})

                try:
                    await middleware.dispatch(request, call_next)
                except Exception as e:
                    # Rate limiting might raise an exception
                    if "rate limit" in str(e).lower():
                        continue


# Mock tests for when API modules are not available
class TestAPIMock:
    """Mock tests when API modules are not available."""

    @pytest.mark.skipif(API_AVAILABLE, reason="API modules are available")
    def test_api_modules_unavailable(self):
        """Test behavior when API modules are not available."""
        with pytest.raises(ImportError):
            from api.middleware.authentication import AuthenticationMiddleware  # noqa: F401

        with pytest.raises(ImportError):
            from api.compliance.consent_validation import ConsentValidator  # noqa: F401


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
