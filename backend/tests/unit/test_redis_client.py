"""Unit tests for Redis client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.redis_client import RedisClient, get_redis, redis_client


class TestRedisClient:
    """Tests for RedisClient class."""

    def test_init(self):
        """Test Redis client initialization."""
        client = RedisClient()
        assert client._redis is None

    async def test_connect(self):
        """Test connecting to Redis."""
        client = RedisClient()

        with patch("app.redis_client.aioredis.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            # from_url is async, so mock needs to return awaitable
            mock_from_url.return_value = mock_redis

            # Make the mock awaitable
            async def async_return():
                return mock_redis

            mock_from_url.return_value = async_return()

            await client.connect()

            assert client._redis == mock_redis
            mock_from_url.assert_called_once()
            call_args = mock_from_url.call_args
            # Check that it was called with redis_url as first arg
            assert "redis://localhost:6379" in call_args[0][0]
            # Check encoding and decode_responses kwargs
            assert call_args[1]["encoding"] == "utf-8"
            assert call_args[1]["decode_responses"] is True

    async def test_disconnect_when_connected(self):
        """Test disconnecting from Redis when connected."""
        client = RedisClient()
        mock_redis = AsyncMock()
        client._redis = mock_redis

        await client.disconnect()

        mock_redis.close.assert_called_once()

    async def test_disconnect_when_not_connected(self):
        """Test disconnecting when not connected (should not raise error)."""
        client = RedisClient()
        client._redis = None

        # Should not raise any error
        await client.disconnect()

    def test_client_property_when_connected(self):
        """Test getting client when connected."""
        client = RedisClient()
        mock_redis = MagicMock()
        client._redis = mock_redis

        result = client.client

        assert result == mock_redis

    def test_client_property_when_not_connected(self):
        """Test getting client when not connected raises error."""
        client = RedisClient()
        client._redis = None

        with pytest.raises(RuntimeError) as exc_info:
            _ = client.client

        assert "Redis not connected" in str(exc_info.value)
        assert "Call connect() first" in str(exc_info.value)

    async def test_connect_disconnect_flow(self):
        """Test full connect/disconnect flow."""
        client = RedisClient()

        with patch("app.redis_client.aioredis.from_url") as mock_from_url:
            mock_redis = AsyncMock()

            # Make the mock awaitable
            async def async_return():
                return mock_redis

            mock_from_url.return_value = async_return()

            # Connect
            await client.connect()
            assert client._redis is not None

            # Can get client
            redis = client.client
            assert redis == mock_redis

            # Disconnect
            await client.disconnect()
            mock_redis.close.assert_called_once()


class TestGetRedis:
    """Tests for get_redis dependency function."""

    async def test_get_redis_when_connected(self):
        """Test get_redis returns client when connected."""
        # Mock the global redis_client
        mock_redis = MagicMock()
        with patch.object(redis_client, "_redis", mock_redis):
            result = await get_redis()
            assert result == mock_redis

    async def test_get_redis_when_not_connected(self):
        """Test get_redis raises error when not connected."""
        # Ensure _redis is None
        with patch.object(redis_client, "_redis", None):
            with pytest.raises(RuntimeError) as exc_info:
                await get_redis()

            assert "Redis not connected" in str(exc_info.value)


class TestGlobalRedisClient:
    """Tests for global redis_client instance."""

    def test_global_redis_client_exists(self):
        """Test that global redis_client is instantiated."""
        from app.redis_client import redis_client as global_client

        assert global_client is not None
        assert isinstance(global_client, RedisClient)

    def test_global_redis_client_is_singleton(self):
        """Test that redis_client is a singleton."""
        from app.redis_client import redis_client as client1
        from app.redis_client import redis_client as client2

        # Both imports should refer to the same instance
        assert client1 is client2
