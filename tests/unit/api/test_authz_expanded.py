from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from api.middleware.authentication import AuthenticationMiddleware
from api.services.auth_manager import TokenPayload


@pytest.fixture
def authz_app():
    app = FastAPI()
    app.add_middleware(AuthenticationMiddleware)

    @app.get("/admin")
    async def admin_route(request: Request):
        user = getattr(request.state, "user", None)
        if not user or "admin" not in user.roles:
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Admin access required")
        return {"message": "admin access granted"}

    @app.get("/user")
    async def user_route(request: Request):
        user = getattr(request.state, "user", None)
        if not user:
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Not authenticated")
        return {"message": f"hello {user.username}"}

    return app


@pytest.fixture
def client(authz_app):
    return TestClient(authz_app)


@pytest.mark.asyncio
async def test_role_based_access(client, monkeypatch):
    # Mock token verification to return a user with 'user' role
    payload = TokenPayload(
        user_id="user1",
        username="testuser",
        roles=["user"],
        exp=datetime.utcnow() + timedelta(hours=1),
    )

    async def mock_verify_token(self, token):
        return payload

    monkeypatch.setattr(
        "api.middleware.authentication.AuthenticationMiddleware._verify_token", mock_verify_token
    )

    # Test user route
    response = client.get("/user", headers={"Authorization": "Bearer some-token"})
    assert response.status_code == 200
    assert response.json()["message"] == "hello testuser"

    # Test admin route (should fail)
    response = client.get("/admin", headers={"Authorization": "Bearer some-token"})
    assert response.status_code == 403

    # Update payload to have admin role
    payload.roles = ["admin"]
    response = client.get("/admin", headers={"Authorization": "Bearer some-token"})
    # Wait, the middleware caches by token hash!
    # If we use the same token, it will hit the cache.
    # In the first call, it cached roles=['user'].
    # So even if we change the payload object, the cached one is returned.

    # Actually, the mock returns the object 'payload' which we modified.
    # But wait, AuthenticationMiddleware._token_cache stores the object.
    # Since we modified the object in place, it might work, but let's be careful.

    # To bypass cache, use a different token
    response = client.get("/admin", headers={"Authorization": "Bearer other-token"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_token_revocation_bypass(client, monkeypatch):
    """
    Test that a revoked token is still accepted if it's in the middleware cache.
    This test demonstrates the race condition/bypass risk.
    """
    from api.middleware.authentication import _token_cache

    _token_cache.clear()

    payload = TokenPayload(
        user_id="user1",
        username="testuser",
        roles=["user"],
        exp=datetime.utcnow() + timedelta(hours=1),
    )

    # Mock AuthManager to simulate blacklist
    is_blacklisted = False

    async def mock_is_token_blacklisted(self, token):
        return is_blacklisted

    monkeypatch.setattr(
        "api.services.auth_manager.AuthManager.is_token_blacklisted", mock_is_token_blacklisted
    )

    # Mock verify_token to return our payload
    def mock_verify_token_real(self, token, expected_type="access"):
        return payload

    monkeypatch.setattr(
        "api.services.auth_manager.AuthManager.verify_token", mock_verify_token_real
    )

    token = "test-token"

    # 1. First request - populates cache
    response = client.get("/user", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # 2. Revoke the token
    is_blacklisted = True

    # 3. Second request - should fail if check is robust, but currently fails (succeeds) due to cache hit
    response = client.get("/user", headers={"Authorization": f"Bearer {token}"})

    # If this fails, it means the bypass exists.
    # The task is to FIX it, so I should expect it to fail (status 401) after my fix.
    # For now, let's see it fail (succeed 200).
    assert response.status_code == 401, "Token should be rejected after revocation even if in cache"
