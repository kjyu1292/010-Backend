"""----------------------------"""
import pytest
from uuid import uuid4

from app.auth.service import (
    get_password_hash
    , verify_password
    , create_access_token
    , verify_access_token
    , _hash_token
)


"""----------------------------"""
def test_password_hash_roundtrip():
    hashed = get_password_hash("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)

def test_password_hash_rejects_wrong_password():
    hashed = get_password_hash("correct-horse-battery-staple")
    assert not verify_password("wrong-password", hashed)

def test_password_never_stored_in_plaintext():
    hashed = get_password_hash("mypassword123")
    assert hashed != "mypassword123"
    assert hashed.startswith("$2b$")


"""----------------------------"""
def test_access_token_roundtrip():
    user_id = uuid4()
    token = create_access_token("user@example.com", user_id)
    token_data = verify_access_token(token)
    assert token_data.user_id == user_id

def test_access_token_rejects_garbage():
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        verify_access_token("not.a.valid.jwt")


"""----------------------------"""
def test_token_hash_is_deterministic():
    token = "some-opaque-refresh-token"
    assert _hash_token(token) == _hash_token(token)

def test_token_hash_differs_per_input():
    assert _hash_token("token-a") != _hash_token("token-b")