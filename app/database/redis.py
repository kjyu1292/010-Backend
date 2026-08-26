"""----------------------------"""
import os
from typing import Annotated
from collections.abc import AsyncGenerator

from fastapi import Depends
from redis.asyncio import Redis, from_url

from dotenv import load_dotenv
load_dotenv()


"""----------------------------"""
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_pool = from_url(REDIS_URL, decode_responses = True)


"""----------------------------"""
async def get_redis() -> AsyncGenerator[Redis, None]:
    yield redis_pool


RedisSession = Annotated[Redis, Depends(get_redis)]
