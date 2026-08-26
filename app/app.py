"""----------------------------"""
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from contextlib import asynccontextmanager

from app.database.core import create_db_and_table
from app.auth.router import router, limiter

"""----------------------------"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_table()
    yield

app = FastAPI(lifespan = lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(router, prefix = "/v1")

"""----------------------------"""
@app.get("/health", tags = ["health"])
async def health():
    return {"status": "ok"}
