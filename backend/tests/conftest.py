"""Pytest configuration and shared fixtures."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Set testing mode environment variable BEFORE importing settings
os.environ["TESTING"] = "true"

from app.config import Settings, settings
from app.models import Base

# Reinitialize settings to pick up the TESTING environment variable
if not settings.testing:
    # Force reload of settings with TESTING=true
    import app.config

    app.config.settings = Settings(testing=True)

# Test database URL (uses a separate test database)
# Use same user as main database, just different database name
# Be careful to only replace the database name, not the username
TEST_DATABASE_URL = settings.database_url.replace(
    "localhost:5432/gametime", "localhost:5432/gametime_test"
)
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
        yield session

        # Clean up all data after each test
        await session.rollback()
        async with session.begin():
            # Delete all data from tables in reverse order of dependencies
            await session.execute(text("DELETE FROM players"))
            await session.execute(text("DELETE FROM rooms"))
            await session.commit()


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
