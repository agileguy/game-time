"""Integration tests for HTTP API routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.redis_client import get_redis


@pytest.mark.integration
class TestHealthRoutes:
    """Integration tests for health check endpoints."""

    async def test_basic_health_check(self, client: AsyncClient):
        """Test basic health endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "game-time"

    async def test_database_health_check(self, client: AsyncClient):
        """Test database health endpoint."""
        response = await client.get("/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    async def test_redis_health_check(self, client: AsyncClient):
        """Test Redis health endpoint."""
        response = await client.get("/health/redis")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["redis"] == "connected"

    async def test_full_health_check(self, client: AsyncClient):
        """Test full health endpoint."""
        response = await client.get("/health/full")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["redis"] == "connected"
        assert data["errors"] is None


@pytest.mark.integration
class TestRoomRoutes:
    """Integration tests for room endpoints."""

    async def test_create_room_success(self, client: AsyncClient):
        """Test successful room creation."""
        response = await client.post(
            "/api/rooms",
            json={
                "host_name": "Alice",
                "max_players": 8,
                "is_public": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "room_code" in data
        assert len(data["room_code"]) == 4
        assert data["player_name"] == "Alice"
        assert data["is_host"] is True
        assert "session_id" in data
        assert "player_id" in data

    async def test_create_room_invalid_name(self, client: AsyncClient):
        """Test room creation with invalid name."""
        response = await client.post(
            "/api/rooms",
            json={
                "host_name": "",  # Empty name
                "max_players": 8,
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_create_room_invalid_max_players(self, client: AsyncClient):
        """Test room creation with invalid max players."""
        response = await client.post(
            "/api/rooms",
            json={
                "host_name": "Alice",
                "max_players": 20,  # Too many
            },
        )

        assert response.status_code == 422

    async def test_join_room_success(self, client: AsyncClient):
        """Test successfully joining a room."""
        # Create room first
        create_response = await client.post(
            "/api/rooms",
            json={"host_name": "Alice"},
        )
        room_code = create_response.json()["room_code"]

        # Join room
        join_response = await client.post(
            f"/api/rooms/{room_code}/join",
            json={"player_name": "Bob"},
        )

        assert join_response.status_code == 200
        data = join_response.json()
        assert data["room_code"] == room_code
        assert data["player_name"] == "Bob"
        assert data["is_host"] is False
        assert "session_id" in data

    async def test_join_room_not_found(self, client: AsyncClient):
        """Test joining non-existent room."""
        response = await client.post(
            "/api/rooms/XXXX/join",
            json={"player_name": "Bob"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_join_room_full(self, client: AsyncClient):
        """Test joining a full room."""
        # Create room with max 2 players
        create_response = await client.post(
            "/api/rooms",
            json={
                "host_name": "Alice",
                "max_players": 2,
            },
        )
        room_code = create_response.json()["room_code"]

        # Join room (fills it)
        await client.post(
            f"/api/rooms/{room_code}/join",
            json={"player_name": "Bob"},
        )

        # Try to join full room
        response = await client.post(
            f"/api/rooms/{room_code}/join",
            json={"player_name": "Charlie"},
        )

        assert response.status_code == 409
        assert "full" in response.json()["detail"].lower()

    async def test_get_room_details(self, client: AsyncClient):
        """Test getting room details."""
        # Create room
        create_response = await client.post(
            "/api/rooms",
            json={"host_name": "Alice", "max_players": 8},
        )
        room_code = create_response.json()["room_code"]

        # Get room details
        response = await client.get(f"/api/rooms/{room_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["room_code"] == room_code
        assert data["status"] == "lobby"
        assert data["max_players"] == 8
        assert data["active_players"] == 0  # No WebSocket connections yet
        assert data["is_public"] is True

    async def test_get_room_not_found(self, client: AsyncClient):
        """Test getting non-existent room."""
        response = await client.get("/api/rooms/XXXX")

        assert response.status_code == 404

    async def test_multiple_players_join(self, client: AsyncClient):
        """Test multiple players joining a room."""
        # Create room
        create_response = await client.post(
            "/api/rooms",
            json={"host_name": "Alice", "max_players": 5},
        )
        room_code = create_response.json()["room_code"]

        # Join with multiple players
        players = ["Bob", "Charlie", "David"]
        for name in players:
            response = await client.post(
                f"/api/rooms/{room_code}/join",
                json={"player_name": name},
            )
            assert response.status_code == 200

        # Check room details
        response = await client.get(f"/api/rooms/{room_code}")
        data = response.json()
        assert data["active_players"] == 0  # No WebSocket connections yet


@pytest.fixture
async def client(db_session, redis_client):
    """Create async test client with dependency overrides."""

    # Override dependencies to use test fixtures
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up overrides
    app.dependency_overrides.clear()
