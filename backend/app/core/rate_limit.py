"""Rate limiting utilities using Redis."""

from typing import Optional
from datetime import timedelta
import redis.asyncio as aioredis

from app.config import settings
from app.core.exceptions import RateLimitExceededError
from app.core.security import hash_ip_address


class RateLimiter:
    """Redis-based rate limiter."""

    def __init__(self, redis_client: aioredis.Redis) -> None:
        """
        Initialize rate limiter.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool:
        """
        Check if rate limit is exceeded.

        Args:
            key: Rate limit key (e.g., "room_creation:hashed_ip")
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            bool: True if within limit, False if exceeded

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        if not settings.enable_rate_limiting:
            return True

        # Get current count
        current = await self.redis.get(key)

        if current is None:
            # First request in window
            await self.redis.setex(key, window_seconds, 1)
            return True

        current_count = int(current)

        if current_count >= limit:
            # Get TTL for retry-after header
            ttl = await self.redis.ttl(key)
            raise RateLimitExceededError(retry_after=max(ttl, 1))

        # Increment counter
        await self.redis.incr(key)
        return True

    async def check_room_creation_limit(self, ip_address: str) -> bool:
        """
        Check room creation rate limit for an IP address.

        Args:
            ip_address: Client IP address

        Returns:
            bool: True if within limit

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        hashed_ip = hash_ip_address(ip_address)
        key = f"rate_limit:room_creation:{hashed_ip}"

        return await self.check_rate_limit(
            key=key,
            limit=settings.rate_limit_room_creation,
            window_seconds=3600,  # 1 hour
        )

    async def check_api_request_limit(self, ip_address: str) -> bool:
        """
        Check API request rate limit for an IP address.

        Args:
            ip_address: Client IP address

        Returns:
            bool: True if within limit

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        hashed_ip = hash_ip_address(ip_address)
        key = f"rate_limit:api_requests:{hashed_ip}"

        return await self.check_rate_limit(
            key=key,
            limit=settings.rate_limit_api_requests,
            window_seconds=60,  # 1 minute
        )

    async def check_websocket_message_limit(self, session_id: str) -> bool:
        """
        Check WebSocket message rate limit for a session.

        Args:
            session_id: WebSocket session ID

        Returns:
            bool: True if within limit

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        key = f"rate_limit:ws_messages:{session_id}"

        return await self.check_rate_limit(
            key=key,
            limit=settings.rate_limit_ws_messages,
            window_seconds=60,  # 1 minute
        )

    async def reset_rate_limit(self, key: str) -> None:
        """
        Reset rate limit for a specific key.

        Args:
            key: Rate limit key to reset
        """
        await self.redis.delete(key)

    async def get_remaining(
        self,
        key: str,
        limit: int,
    ) -> int:
        """
        Get remaining requests for a rate limit key.

        Args:
            key: Rate limit key
            limit: Maximum allowed requests

        Returns:
            int: Number of remaining requests
        """
        current = await self.redis.get(key)

        if current is None:
            return limit

        return max(0, limit - int(current))


async def get_rate_limiter(redis_client: aioredis.Redis) -> RateLimiter:
    """
    Dependency for getting rate limiter instance.

    Args:
        redis_client: Redis client

    Returns:
        RateLimiter: Rate limiter instance
    """
    return RateLimiter(redis_client)
