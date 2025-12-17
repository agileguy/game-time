"""Integration tests for Player Manager Service."""

import pytest

from app.models import Player, Room
from app.services import PlayerManager, RoomManager


@pytest.mark.integration
class TestPlayerManagerIntegration:
    """Integration tests for PlayerManager."""

    async def test_create_session(self, db_session, redis_client):
        """Test creating a player session."""
        player_manager = PlayerManager(db_session, redis_client)

        session_id = await player_manager.create_session()

        assert session_id is not None
        assert len(session_id) == 64
        assert session_id.isalnum()

        # Verify session stored in Redis
        is_valid = await player_manager.validate_session(session_id)
        assert is_valid is True

    async def test_validate_session_invalid(self, db_session, redis_client):
        """Test validating invalid session."""
        player_manager = PlayerManager(db_session, redis_client)

        is_valid = await player_manager.validate_session("invalid_session")
        assert is_valid is False

    async def test_get_player_by_session(self, db_session, redis_client):
        """Test getting player by session ID."""
        room_manager = RoomManager(db_session)
        player_manager = PlayerManager(db_session, redis_client)

        # Create room with player
        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        # Get player by session
        player = await player_manager.get_player_by_session("a" * 64)
        assert player is not None
        assert player.id == host.id
        assert player.name == "Alice"

    async def test_get_player_by_session_not_found(self, db_session, redis_client):
        """Test getting non-existent player by session."""
        player_manager = PlayerManager(db_session, redis_client)

        player = await player_manager.get_player_by_session("x" * 64)
        assert player is None

    async def test_update_player_connection(self, db_session, redis_client):
        """Test updating player connection status."""
        room_manager = RoomManager(db_session)
        player_manager = PlayerManager(db_session, redis_client)

        # Create player
        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        # Disconnect
        updated = await player_manager.update_player_connection(host.id, False)
        assert updated is not None
        assert updated.connected is False

        # Reconnect
        updated = await player_manager.update_player_connection(host.id, True)
        assert updated is not None
        assert updated.connected is True

    async def test_update_last_seen(self, db_session, redis_client):
        """Test updating player last seen timestamp."""
        from datetime import datetime, timedelta

        room_manager = RoomManager(db_session)
        player_manager = PlayerManager(db_session, redis_client)

        # Create player
        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        original_last_seen = host.last_seen

        # Wait a moment
        import asyncio
        await asyncio.sleep(0.1)

        # Update last seen
        updated = await player_manager.update_last_seen(host.id)
        assert updated is not None
        assert updated.last_seen > original_last_seen

    async def test_store_and_get_connection(self, db_session, redis_client):
        """Test storing and retrieving WebSocket connection info."""
        player_manager = PlayerManager(db_session, redis_client)

        session_id = "test_session_" + ("x" * 50)
        connection_id = "conn_123"
        room_code = "ABCD"

        # Store connection
        await player_manager.store_connection(session_id, connection_id, room_code)

        # Retrieve connection
        stored_conn = await player_manager.get_connection_id(session_id)
        assert stored_conn == connection_id

        # Retrieve room
        stored_room = await player_manager.get_player_room(session_id)
        assert stored_room == room_code

    async def test_remove_connection(self, db_session, redis_client):
        """Test removing WebSocket connection info."""
        player_manager = PlayerManager(db_session, redis_client)

        session_id = "test_session_" + ("y" * 50)
        connection_id = "conn_456"
        room_code = "EFGH"

        # Store then remove
        await player_manager.store_connection(session_id, connection_id, room_code)
        await player_manager.remove_connection(session_id)

        # Verify removed
        stored_conn = await player_manager.get_connection_id(session_id)
        assert stored_conn is None

        stored_room = await player_manager.get_player_room(session_id)
        assert stored_room is None

    async def test_is_player_connected(self, db_session, redis_client):
        """Test checking if player is connected."""
        room_manager = RoomManager(db_session)
        player_manager = PlayerManager(db_session, redis_client)

        # Create player
        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        # Store connection
        await player_manager.store_connection("a" * 64, "conn_789", room.code)

        # Check connected
        is_connected = await player_manager.is_player_connected(host.id)
        assert is_connected is True

        # Remove connection
        await player_manager.remove_connection("a" * 64)

        # Check not connected
        is_connected = await player_manager.is_player_connected(host.id)
        assert is_connected is False

    async def test_get_room_players(self, db_session, redis_client):
        """Test getting all players in a room."""
        room_manager = RoomManager(db_session)
        player_manager = PlayerManager(db_session, redis_client)

        # Create room with multiple players
        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        _, player1 = await room_manager.join_room(
            code=room.code,
            player_name="Bob",
            session_id="b" * 64,
        )
        await db_session.commit()

        _, player2 = await room_manager.join_room(
            code=room.code,
            player_name="Charlie",
            session_id="c" * 64,
        )
        await db_session.commit()

        # Get all players
        players = await player_manager.get_room_players(room.id)
        assert len(players) == 3

        # Disconnect one
        player1.connected = False
        await db_session.commit()

        # Get only connected
        connected_players = await player_manager.get_room_players(room.id, connected_only=True)
        assert len(connected_players) == 2
        player_ids = [p.id for p in connected_players]
        assert player1.id not in player_ids

    async def test_session_workflow(self, db_session, redis_client):
        """Test complete session workflow."""
        room_manager = RoomManager(db_session)
        player_manager = PlayerManager(db_session, redis_client)

        # 1. Create session
        session_id = await player_manager.create_session()
        assert await player_manager.validate_session(session_id)

        # 2. Create player with session
        room, player = await room_manager.create_room(
            host_name="Alice",
            host_session_id=session_id,
        )
        await db_session.commit()

        # 3. Store connection
        await player_manager.store_connection(session_id, "conn_test", room.code)

        # 4. Get player by session
        found_player = await player_manager.get_player_by_session(session_id)
        assert found_player.id == player.id

        # 5. Check connection
        conn_id = await player_manager.get_connection_id(session_id)
        assert conn_id == "conn_test"

        # 6. Update activity
        await player_manager.update_last_seen(player.id)

        # 7. Disconnect
        await player_manager.update_player_connection(player.id, False)
        await player_manager.remove_connection(session_id)

        # Verify disconnected
        is_connected = await player_manager.is_player_connected(player.id)
        assert is_connected is False
