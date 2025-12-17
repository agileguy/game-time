"""Redis client configuration and connection management."""

import redis.asyncio as aioredis

from app.config import settings


class RedisClient:
    """Redis client wrapper for managing connections."""

    def __init__(self) -> None:
        """Initialize Redis client."""
        self._redis: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        self._redis = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_max_connections,
        )

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()

    @property
    def client(self) -> aioredis.Redis:
        """
        Get Redis client instance.

        Returns:
            aioredis.Redis: Redis client

        Raises:
            RuntimeError: If Redis not connected
        """
        if self._redis is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._redis


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> aioredis.Redis:
    """
    Dependency for getting Redis client.

    Returns:
        aioredis.Redis: Redis client
    """
    return redis_client.client
