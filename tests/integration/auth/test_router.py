"""----------------------------"""
import pytest


"""----------------------------"""
VALID_PAYLOAD = {
    "email": "player1@example.com"
    , "password": "correct-horse-battery-staple"
    , "display_name": "Player One"
    , "platform": "ios"
}


"""----------------------------"""
@pytest.mark.asyncio
async def test_register_creates_user(client):
    response = await client.post("/v1/auth/register", json=VALID_PAYLOAD)
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    await client.post("/v1/auth/register", json=VALID_PAYLOAD)
    response = await client.post("/v1/auth/register", json=VALID_PAYLOAD)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_register_rejects_short_password(client):
    payload = {**VALID_PAYLOAD, "password": "short"}
    response = await client.post("/v1/auth/register", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_register_rejects_oversized_password(client):
    payload = {**VALID_PAYLOAD, "password": "x" * 100}
    response = await client.post("/v1/auth/register", json=payload)
    assert response.status_code == 422


"""----------------------------"""
@pytest.mark.asyncio
async def test_login_returns_token_pair(client):
    await client.post("/v1/auth/register", json=VALID_PAYLOAD)
    response = await client.post(
        "/v1/auth/login"
        , data={"username": VALID_PAYLOAD["email"], "password": VALID_PAYLOAD["password"]}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body

@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    await client.post("/v1/auth/register", json=VALID_PAYLOAD)
    response = await client.post(
        "/v1/auth/login"
        , data={"username": VALID_PAYLOAD["email"], "password": "wrong-password"}
    )
    assert response.status_code == 401


"""----------------------------"""
@pytest.mark.asyncio
async def test_me_requires_auth(client):
    response = await client.get("/v1/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_me_returns_user_with_valid_token(client):
    await client.post("/v1/auth/register", json=VALID_PAYLOAD)
    login = await client.post(
        "/v1/auth/login"
        , data={"username": VALID_PAYLOAD["email"], "password": VALID_PAYLOAD["password"]}
    )
    token = login.json()["access_token"]
    response = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == VALID_PAYLOAD["email"]
