"""----------------------------"""
import os
from typing import Annotated
from collections.abc import AsyncGenerator

from fastapi import Depends
from redis.asyncio import Redis, from_url

import app.environment


"""----------------------------"""
REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL is None:
    raise RuntimeError(
            f"REDIS_URL is not set in {env_file.name}"
    )
redis_pool = from_url(REDIS_URL, decode_responses = True)


"""----------------------------"""
async def get_redis() -> AsyncGenerator[Redis, None]:
    yield redis_pool


RedisSession = Annotated[Redis, Depends(get_redis)]
