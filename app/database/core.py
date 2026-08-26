"""----------------------------"""
import os
from typing import Annotated
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession
    , create_async_engine
    , async_sessionmaker
)

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase

import app.environment
from app.database import Base
from app.entities.user import User


"""----------------------------"""
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise RuntimeError(
            f"DATABASE_URL is not set in {env_file.name}"
    )


"""----------------------------"""
engine = create_async_engine(DATABASE_URL)
asyncSessionLocal = async_sessionmaker(
        bind = engine
        , class_ = AsyncSession
        , expire_on_commit = False
)


"""----------------------------"""
#async def create_db_and_table():
#    async with engine.begin() as conn:
#        await conn.run_sync(Base.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with asyncSessionLocal() as session:
        yield session

userDBSession = Annotated[AsyncSession, Depends(get_async_session)]
async def get_user_db(session: userDBSession):
    yield SQLAlchemyUserDatabase(session, User)

#atDBSession = Annotated[AsyncSession, Depends(get_async_session)]
#async def get_access_token_db(session: atDBSession):
#    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)
