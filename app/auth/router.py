"""----------------------------"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import select

from app.database.core import userDBSession
from app.database.redis import RedisSession

from app.limiter import limiter
from app.entities.user import User

from app.auth import service
from app.auth.model import RegisterUserRequest, TokenPair, RefreshRequest

"""----------------------------"""
router = APIRouter(prefix = "/auth", tags = ["auth"])


"""----------------------------"""
@router.post("/register", status_code = status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request
    , payload: RegisterUserRequest
    , session: userDBSession
):
    await service.register_user(payload, session)
    return {"detail": "Registration successful"}


@router.post("/login", response_model = TokenPair)
@limiter.limit("10/minute")
async def login(
    request: Request
    , form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
    , session: userDBSession
    , redis: RedisSession
    , device_id: str = "default"  # TODO: wire to app/entities Device table once client sends real device info
):
    user = await service.authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")

    access_token = service.create_access_token(user.email, user.id)
    refresh_token = await service.issue_refresh_token(redis, user.id, device_id)
    return TokenPair(access_token = access_token, refresh_token = refresh_token)


@router.post("/refresh", response_model = TokenPair)
@limiter.limit("30/minute")
async def refresh(
    request: Request
    , payload: RefreshRequest
    , session: userDBSession
    , redis: RedisSession
):
    new_refresh_token, user_id, _device_id = await service.rotate_refresh_token(redis, payload.refresh_token)

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    access_token = service.create_access_token(user.email, user.id)
    return TokenPair(access_token = access_token, refresh_token = new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest
    , redis: RedisSession
):
    await service.revoke_refresh_token(redis, payload.refresh_token)


@router.get("/me")
async def me(current_user: service.CurrentUser):
    return {
        "id": str(current_user.id)
        , "email": current_user.email
        , "display_name": current_user.display_name
    }
