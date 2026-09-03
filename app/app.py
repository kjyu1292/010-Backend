"""----------------------------"""
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from prometheus_fastapi_instrumentator import Instrumentator

from contextlib import asynccontextmanager

from app.limiter import limiter
from app.database.core import engine
from app.auth.router import router as auth_router
from app.players.router import router as players_router


"""----------------------------"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

app = FastAPI(lifespan = lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router, prefix = "/v1")
app.include_router(players_router, prefix = "/v1")

"""----------------------------"""
@app.get("/health", tags = ["health"])
async def health():
    return {"status": "ok"}


"""----------------------------"""
Instrumentator().instrument(app = app).expose(app = app)
