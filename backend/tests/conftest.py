"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import redis.asyncio as aioredis

from app.models import Base
from app.config import settings


# Test database URL (uses a separate test database)
# Use same user as main database, just different database name
TEST_DATABASE_URL = settings.database_url.replace("/gametime", "/gametime_test")
TEST_REDIS_URL = settings.redis_url.replace("/0", "/1")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for the test session.

    Yields:
        asyncio.AbstractEventLoop: Event loop
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """
    Create a test database engine.

    Yields:
        AsyncEngine: SQLAlchemy async engine
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for testing.

    Args:
        test_engine: Test database engine

    Yields:
        AsyncSession: Database session
    """
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture
async def redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Create a Redis client for testing.

    Yields:
        aioredis.Redis: Redis client
    """
    client = await aioredis.from_url(
        TEST_REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )

    yield client

    # Clean up test data
    await client.flushdb()
    await client.close()


@pytest.fixture
def mock_settings(monkeypatch):
    """
    Mock application settings for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    monkeypatch.setattr(settings, "testing", True)
    monkeypatch.setattr(settings, "debug", True)
    monkeypatch.setattr(settings, "enable_rate_limiting", False)
    return settings
