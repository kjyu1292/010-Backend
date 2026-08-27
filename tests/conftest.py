"""----------------------------"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from redis.asyncio import Redis

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.app import app
from app.database import Base
from app.database.redis import get_redis
from app.database.core import get_async_session


"""----------------------------"""
# Integration/e2e tests use testcontainers to spin up REAL Postgres + Redis
# per test session -- no mocking of the database layer itself.

@pytest_asyncio.fixture(scope = "session")
async def postgres_container():
    from testcontainers.community.postgres import PostgresContainer
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

@pytest_asyncio.fixture(scope = "session")
async def redis_container():
    from testcontainers.community.redis import RedisContainer
    with RedisContainer("redis:7-alpine") as rc:
        yield rc


"""----------------------------"""
@pytest_asyncio.fixture
async def test_engine(postgres_container):
    url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def test_session_maker(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit = False)

@pytest_asyncio.fixture
async def test_redis(redis_container):
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    redis_url = f"redis://{host}:{port}/0"
    client = Redis.from_url(redis_url, decode_responses = True)
    await client.flushdb()
    yield client
    await client.aclose()


"""----------------------------"""
@pytest_asyncio.fixture
async def client(test_session_maker, test_redis):
    async def override_get_session():
        async with test_session_maker() as session:
            yield session

    async def override_get_redis():
        yield test_redis

    app.dependency_overrides[get_async_session] = override_get_session
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app = app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
