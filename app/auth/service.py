"""----------------------------"""
import os
import hashlib
import secrets
from uuid import UUID
from typing import Annotated
from datetime import timedelta, datetime, timezone

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import select
from redis.asyncio import Redis

import app.environment
from app.logging import get_logger
from app.auth.model import TokenData, RegisterUserRequest
from app.database.core import userDBSession
from app.entities.user import User


"""----------------------------"""
SECRET = os.getenv("SECRET")
ENCRYPTION_ALGORITHM = os.getenv("ENCRYPTION_ALGORITHM")
ACCESS_TOKEN_LIFETIME_SECONDS = int(os.getenv("ACCESS_TOKEN_LIFETIME_SECONDS", "1800"))       # 30 min
REFRESH_TOKEN_LIFETIME_SECONDS = int(os.getenv("REFRESH_TOKEN_LIFETIME_SECONDS", "1209600"))  # 14 days

if ((not SECRET)
    | (not ENCRYPTION_ALGORITHM)
    | (not ACCESS_TOKEN_LIFETIME_SECONDS)
    | (not REFRESH_TOKEN_LIFETIME_SECONDS)):
    raise RuntimeError(f"""
            SECRET, ENCRYPTION_ALGORITHM, ACCESS_TOKEN_LIFETIME_SECONDS,
            and REFRESH_TOKEN_LIFETIME_SECONDS must be set in the environment
    """)


"""----------------------------"""
oauth2_bearer = OAuth2PasswordBearer(tokenUrl = "auth/login")
bcrypt_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

logger = get_logger("__name__")


"""----------------------------"""
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return bcrypt_context.hash(password)

def _hash_token(token: str) -> str:
    """Refresh tokens are opaque; only their hash is ever persisted, in Redis."""
    return hashlib.sha256(token.encode()).hexdigest()


"""----------------------------"""
async def authenticate_user(
    email: str
    , password: str
    , session: userDBSession
) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Failed authenticate for user {email}")
        return None
    if not user.is_active:
        logger.warning(f"Failed authenticate for inactive user {email}")
        return None
    return user

async def register_user(
    payload: RegisterUserRequest
    , session: userDBSession
) -> User:
    existing = await session.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        logger.info(f"Registration rejected, duplicated email {payload.email}")
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email = payload.email
        , hashed_password = get_password_hash(payload.password)
        , display_name = payload.display_name
        , platform = payload.platform
        , status = 0
        , is_active = True
        , is_superuser = False
        , is_verified = False
        , created_at = datetime.now(timezone.utc)
        , last_login_at = datetime.now(timezone.utc)
    )
    try:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    except Exception as e:
        await session.rollback()
        logger.info(f"Registration rejected: {e}")
        raise 
    return user


"""----------------------------"""
def create_access_token(email: str, user_id: UUID) -> str:
    encode = {
        "sub": email
        , "id": str(user_id)
        , "exp": datetime.now(timezone.utc) + timedelta(seconds = ACCESS_TOKEN_LIFETIME_SECONDS)
    }
    return jwt.encode(encode, SECRET, algorithm = ENCRYPTION_ALGORITHM)

def verify_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET, algorithms = [ENCRYPTION_ALGORITHM])
    except PyJWTError:
        logger.info(f"Invalid or expired token")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user_id = payload.get("id")
    if user_id is None:
        logger.info(f"Invalid token payload")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")
    return TokenData(user_id = UUID(user_id))


"""----------------------------"""
async def issue_refresh_token(
    redis: Redis
    , user_id: UUID
    , device_id: str
) -> str:
    """Generates an opaque refresh token, stores only its hash in Redis (key = hash),
    with TTL matching the token's lifetime -> no manual cleanup needed."""
    raw_token = secrets.token_urlsafe(48)
    key = f"refresh:{_hash_token(raw_token)}"
    await redis.set(key, f"{user_id}:{device_id}", ex = REFRESH_TOKEN_LIFETIME_SECONDS)
    return raw_token

async def rotate_refresh_token(
    redis: Redis
    , presented_token: str
) -> tuple[str, UUID, str]:
    """Validates presented refresh token against Redis, deletes it (single use),
    and issues a new one. If the token was already rotated/expired, the lookup
    misses and this raises -> forces re-login (implicit reuse detection)."""
    key = f"refresh:{_hash_token(presented_token)}"
    stored = await redis.get(key)

    if stored is None:
        logger.warning(f"Refresh token reuse or expiry detected for hash prefix {presented_token[:8]}...")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token invalid or reused, please log in again")

    await redis.delete(key)
    user_id_str, device_id = stored.split(":", 1)
    user_id = UUID(user_id_str)
    new_token = await issue_refresh_token(redis, user_id, device_id)
    return new_token, user_id, device_id

async def revoke_refresh_token(redis: Redis, raw_token: str) -> None:
    await redis.delete(f"refresh:{_hash_token(raw_token)}")


"""----------------------------"""
async def get_current_user(
    token: Annotated[str, Depends(oauth2_bearer)]
    , session: userDBSession
) -> User:
    token_data = verify_access_token(token)
    result = await session.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        logger.info("User not found")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
