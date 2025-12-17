"""Unit tests for rate limiting."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import RateLimitExceededError
from app.core.rate_limit import RateLimiter, get_rate_limiter


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.incr = AsyncMock()
    redis.delete = AsyncMock()
    redis.ttl = AsyncMock(return_value=60)
    return redis


@pytest.fixture
def rate_limiter(mock_redis):
    """Create a rate limiter with mock Redis."""
    return RateLimiter(mock_redis)


class TestRateLimiter:
    """Tests for RateLimiter class."""

    async def test_init(self, mock_redis):
        """Test rate limiter initialization."""
        limiter = RateLimiter(mock_redis)
        assert limiter.redis == mock_redis

    async def test_check_rate_limit_first_request(self, rate_limiter, mock_redis):
        """Test rate limit check for first request in window."""
        mock_redis.get.return_value = None

        result = await rate_limiter.check_rate_limit(
            key="test:key",
            limit=10,
            window_seconds=60,
        )

        assert result is True
        mock_redis.get.assert_called_once_with("test:key")
        mock_redis.setex.assert_called_once_with("test:key", 60, 1)

    async def test_check_rate_limit_within_limit(self, rate_limiter, mock_redis):
        """Test rate limit check when within limit."""
        mock_redis.get.return_value = "5"

        result = await rate_limiter.check_rate_limit(
            key="test:key",
            limit=10,
            window_seconds=60,
        )

        assert result is True
        mock_redis.get.assert_called_once_with("test:key")
        mock_redis.incr.assert_called_once_with("test:key")

    async def test_check_rate_limit_exceeded(self, rate_limiter, mock_redis):
        """Test rate limit check when limit exceeded."""
        mock_redis.get.return_value = "10"
        mock_redis.ttl.return_value = 45

        with pytest.raises(RateLimitExceededError) as exc_info:
            await rate_limiter.check_rate_limit(
                key="test:key",
                limit=10,
                window_seconds=60,
            )

        assert exc_info.value.details["retry_after"] == 45
        mock_redis.get.assert_called_once_with("test:key")
        mock_redis.ttl.assert_called_once_with("test:key")
        mock_redis.incr.assert_not_called()

    async def test_check_rate_limit_disabled(
        self, rate_limiter, mock_redis, mock_settings
    ):
        """Test rate limit check when rate limiting is disabled."""
        result = await rate_limiter.check_rate_limit(
            key="test:key",
            limit=10,
            window_seconds=60,
        )

        assert result is True
        mock_redis.get.assert_not_called()

    async def test_check_rate_limit_ttl_fallback(self, rate_limiter, mock_redis):
        """Test that TTL fallback to 1 if TTL returns 0 or negative."""
        mock_redis.get.return_value = "10"
        mock_redis.ttl.return_value = -1  # Key doesn't exist or no TTL

        with pytest.raises(RateLimitExceededError) as exc_info:
            await rate_limiter.check_rate_limit(
                key="test:key",
                limit=10,
                window_seconds=60,
            )

        # Should use max(ttl, 1) so retry_after is at least 1
        assert exc_info.value.details["retry_after"] == 1

    async def test_check_room_creation_limit(self, rate_limiter, mock_redis):
        """Test room creation rate limit check."""
        mock_redis.get.return_value = None

        result = await rate_limiter.check_room_creation_limit("192.168.1.1")

        assert result is True
        # Should use hashed IP in key
        call_args = mock_redis.setex.call_args
        assert call_args is not None
        key = call_args[0][0]
        assert key.startswith("rate_limit:room_creation:")
        assert call_args[0][1] == 3600  # 1 hour window

    async def test_check_room_creation_limit_exceeded(
        self, rate_limiter, mock_redis, mock_settings
    ):
        """Test room creation rate limit when exceeded."""
        # Enable rate limiting
        mock_settings.enable_rate_limiting = True
        mock_redis.get.return_value = "5"  # At limit
        mock_redis.ttl.return_value = 1800  # 30 minutes remaining

        with pytest.raises(RateLimitExceededError) as exc_info:
            await rate_limiter.check_room_creation_limit("192.168.1.1")

        assert exc_info.value.details["retry_after"] == 1800

    async def test_check_api_request_limit(self, rate_limiter, mock_redis):
        """Test API request rate limit check."""
        mock_redis.get.return_value = None

        result = await rate_limiter.check_api_request_limit("192.168.1.1")

        assert result is True
        call_args = mock_redis.setex.call_args
        assert call_args is not None
        key = call_args[0][0]
        assert key.startswith("rate_limit:api_requests:")
        assert call_args[0][1] == 60  # 1 minute window

    async def test_check_api_request_limit_exceeded(
        self, rate_limiter, mock_redis, mock_settings
    ):
        """Test API request rate limit when exceeded."""
        mock_settings.enable_rate_limiting = True
        mock_redis.get.return_value = "100"  # At limit
        mock_redis.ttl.return_value = 30

        with pytest.raises(RateLimitExceededError) as exc_info:
            await rate_limiter.check_api_request_limit("192.168.1.1")

        assert exc_info.value.details["retry_after"] == 30

    async def test_check_websocket_message_limit(self, rate_limiter, mock_redis):
        """Test WebSocket message rate limit check."""
        mock_redis.get.return_value = None
        session_id = "test-session-123"

        result = await rate_limiter.check_websocket_message_limit(session_id)

        assert result is True
        call_args = mock_redis.setex.call_args
        assert call_args is not None
        key = call_args[0][0]
        assert key == f"rate_limit:ws_messages:{session_id}"
        assert call_args[0][1] == 60  # 1 minute window

    async def test_check_websocket_message_limit_exceeded(
        self, rate_limiter, mock_redis, mock_settings
    ):
        """Test WebSocket message rate limit when exceeded."""
        mock_settings.enable_rate_limiting = True
        mock_redis.get.return_value = "60"  # At limit
        mock_redis.ttl.return_value = 15

        with pytest.raises(RateLimitExceededError) as exc_info:
            await rate_limiter.check_websocket_message_limit("test-session")

        assert exc_info.value.details["retry_after"] == 15

    async def test_reset_rate_limit(self, rate_limiter, mock_redis):
        """Test resetting a rate limit key."""
        await rate_limiter.reset_rate_limit("test:key")

        mock_redis.delete.assert_called_once_with("test:key")

    async def test_get_remaining_no_requests(self, rate_limiter, mock_redis):
        """Test getting remaining requests when no requests made."""
        mock_redis.get.return_value = None

        remaining = await rate_limiter.get_remaining("test:key", limit=10)

        assert remaining == 10
        mock_redis.get.assert_called_once_with("test:key")

    async def test_get_remaining_some_requests(self, rate_limiter, mock_redis):
        """Test getting remaining requests when some requests made."""
        mock_redis.get.return_value = "3"

        remaining = await rate_limiter.get_remaining("test:key", limit=10)

        assert remaining == 7
        mock_redis.get.assert_called_once_with("test:key")

    async def test_get_remaining_at_limit(self, rate_limiter, mock_redis):
        """Test getting remaining requests when at limit."""
        mock_redis.get.return_value = "10"

        remaining = await rate_limiter.get_remaining("test:key", limit=10)

        assert remaining == 0

    async def test_get_remaining_over_limit(self, rate_limiter, mock_redis):
        """Test getting remaining requests when over limit."""
        mock_redis.get.return_value = "15"

        remaining = await rate_limiter.get_remaining("test:key", limit=10)

        # Should return 0, not negative
        assert remaining == 0

    async def test_get_rate_limiter_dependency(self, mock_redis):
        """Test get_rate_limiter dependency function."""
        limiter = await get_rate_limiter(mock_redis)

        assert isinstance(limiter, RateLimiter)
        assert limiter.redis == mock_redis


class TestRateLimiterIntegration:
    """Integration tests for rate limiter with realistic scenarios."""

    async def test_multiple_requests_within_limit(self, rate_limiter, mock_redis):
        """Test multiple sequential requests within limit."""
        # First request
        mock_redis.get.return_value = None
        await rate_limiter.check_rate_limit("test:key", limit=3, window_seconds=60)

        # Second request
        mock_redis.get.return_value = "1"
        await rate_limiter.check_rate_limit("test:key", limit=3, window_seconds=60)

        # Third request
        mock_redis.get.return_value = "2"
        result = await rate_limiter.check_rate_limit(
            "test:key", limit=3, window_seconds=60
        )

        assert result is True
        assert mock_redis.incr.call_count == 2  # Called for 2nd and 3rd requests

    async def test_burst_then_wait(self, rate_limiter, mock_redis, mock_settings):
        """Test burst of requests followed by rate limit exceeded."""
        mock_settings.enable_rate_limiting = True

        # First 5 requests succeed
        for i in range(5):
            if i == 0:
                mock_redis.get.return_value = None
            else:
                mock_redis.get.return_value = str(i)

            await rate_limiter.check_rate_limit("test:key", limit=5, window_seconds=60)

        # 6th request should fail
        mock_redis.get.return_value = "5"
        mock_redis.ttl.return_value = 55

        with pytest.raises(RateLimitExceededError) as exc_info:
            await rate_limiter.check_rate_limit("test:key", limit=5, window_seconds=60)

        assert exc_info.value.details["retry_after"] == 55
