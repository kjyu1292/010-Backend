"""----------------------------"""
import os
import uuid
import pytest
import httpx

import app.environment

"""----------------------------"""
BASE_URL = os.getenv("E2E_BASE_URL")
if BASE_URL is None:
    raise RuntimeError(
            f"BASE_URL is not set in {env_file.name}"
    )


"""----------------------------"""
@pytest.fixture
def unique_user():
    tag = uuid.uuid4().hex[:8]
    return {
        "email": f"e2e_{tag}@example.com"
        , "password": "correct-horse-battery-staple"
        , "display_name": f"E2E User {tag}"
        , "platform": "ios"
    }


"""----------------------------"""
@pytest.mark.asyncio
async def test_full_auth_lifecycle(unique_user):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:

        # Register
        r = await client.post("/v1/auth/register", json=unique_user)
        assert r.status_code == 201

        # Login
        r = await client.post(
            "/v1/auth/login"
            , data={"username": unique_user["email"], "password": unique_user["password"]}
        )
        assert r.status_code == 200
        tokens = r.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Access protected route
        r = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code == 200
        assert r.json()["email"] == unique_user["email"]

        # Refresh -> get a new pair, old refresh token is now dead
        r = await client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert r.status_code == 200
        new_tokens = r.json()
        assert new_tokens["refresh_token"] != refresh_token

        # Reusing the OLD refresh token must now fail (rotation + reuse detection)
        r = await client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert r.status_code == 401

        # Logout with the current (new) refresh token
        r = await client.post("/v1/auth/logout", json={"refresh_token": new_tokens["refresh_token"]})
        assert r.status_code == 204

        # That refresh token is now dead too
        r = await client.post("/v1/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]})
        assert r.status_code == 401


"""----------------------------"""
@pytest.mark.asyncio
async def test_register_rate_limit_kicks_in():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        statuses = []
        for _ in range(10):
            tag = uuid.uuid4().hex[:8]
            payload = {
                "email": f"ratelimit_{tag}@example.com"
                , "password": "correct-horse-battery-staple"
                , "display_name": f"Rate Limit Test {tag}"
                , "platform": "ios"
            }
            r = await client.post("/v1/auth/register", json=payload)
            statuses.append(r.status_code)

        assert 429 in statuses, "Expected the rate limiter to trigger a 429 within 10 rapid requests"
