"""Integration tests for Room Manager Service."""

import pytest
from sqlalchemy import select

from app.core.exceptions import RoomFullError, RoomNotFoundError, ValidationError
from app.models import Player, Room
from app.services import RoomManager


@pytest.mark.integration
class TestRoomManagerIntegration:
    """Integration tests for RoomManager."""

    async def test_create_room_success(self, db_session):
        """Test successful room creation with host player."""
        room_manager = RoomManager(db_session)

        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
            max_players=8,
            is_public=True,
        )

        # Verify room created
        assert room.id is not None
        assert len(room.code) == 4
        assert room.status == "lobby"
        assert room.max_players == 8
        assert room.is_public is True
        assert room.host_player_id == host.id

        # Verify host created
        assert host.id is not None
        assert host.name == "Alice"
        assert host.is_host is True
        assert host.connected is True
        assert host.room_id == room.id

    async def test_create_room_generates_unique_codes(self, db_session):
        """Test that room codes are unique."""
        room_manager = RoomManager(db_session)

        # Create multiple rooms
        codes = set()
        for i in range(5):
            room, _ = await room_manager.create_room(
                host_name=f"Host{i}",
                host_session_id=("0" * 63) + str(i),
            )
            codes.add(room.code)

        # All codes should be unique
        assert len(codes) == 5

    async def test_create_room_invalid_name(self, db_session):
        """Test room creation with invalid host name."""
        room_manager = RoomManager(db_session)

        with pytest.raises(ValidationError):
            await room_manager.create_room(
                host_name="",  # Empty name
                host_session_id="a" * 64,
            )

    async def test_create_room_invalid_max_players(self, db_session):
        """Test room creation with invalid max players."""
        room_manager = RoomManager(db_session)

        with pytest.raises(ValidationError):
            await room_manager.create_room(
                host_name="Alice",
                host_session_id="a" * 64,
                max_players=1,  # Too few
            )

        with pytest.raises(ValidationError):
            await room_manager.create_room(
                host_name="Alice",
                host_session_id="b" * 64,
                max_players=20,  # Too many
            )

    async def test_get_room_by_code(self, db_session):
        """Test retrieving room by code."""
        room_manager = RoomManager(db_session)

        # Create room
        room, _ = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        # Get room by code
        found_room = await room_manager.get_room_by_code(room.code)
        assert found_room is not None
        assert found_room.id == room.id
        assert found_room.code == room.code

    async def test_get_room_by_code_not_found(self, db_session):
        """Test getting non-existent room."""
        room_manager = RoomManager(db_session)

        room = await room_manager.get_room_by_code("XXXX")
        assert room is None

    async def test_join_room_success(self, db_session):
        """Test successfully joining a room."""
        room_manager = RoomManager(db_session)

        # Create room
        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        # Join room
        joined_room, player = await room_manager.join_room(
            code=room.code,
            player_name="Bob",
            session_id="b" * 64,
        )

        # Verify join
        assert joined_room.id == room.id
        assert player.name == "Bob"
        assert player.is_host is False
        assert player.connected is True
        assert player.room_id == room.id

        # Verify room has 2 players
        await db_session.refresh(room, ["players"])
        assert len(room.players) == 2

    async def test_join_room_not_found(self, db_session):
        """Test joining non-existent room."""
        room_manager = RoomManager(db_session)

        with pytest.raises(RoomNotFoundError):
            await room_manager.join_room(
                code="XXXX",
                player_name="Bob",
                session_id="b" * 64,
            )

    async def test_join_room_full(self, db_session):
        """Test joining a full room."""
        room_manager = RoomManager(db_session)

        # Create room with max 2 players
        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
            max_players=2,
        )
        await db_session.commit()

        # Join room (fills it)
        await room_manager.join_room(
            code=room.code,
            player_name="Bob",
            session_id="b" * 64,
        )
        await db_session.commit()

        # Try to join full room
        with pytest.raises(RoomFullError):
            await room_manager.join_room(
                code=room.code,
                player_name="Charlie",
                session_id="c" * 64,
            )

    async def test_join_room_invalid_status(self, db_session):
        """Test joining room that's not in lobby."""
        room_manager = RoomManager(db_session)

        # Create room
        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        room.status = "playing"
        await db_session.commit()

        # Try to join playing room
        with pytest.raises(ValidationError, match="not in lobby"):
            await room_manager.join_room(
                code=room.code,
                player_name="Bob",
                session_id="b" * 64,
            )

    async def test_leave_room(self, db_session):
        """Test player leaving room."""
        room_manager = RoomManager(db_session)

        # Create and join room
        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        _, player = await room_manager.join_room(
            code=room.code,
            player_name="Bob",
            session_id="b" * 64,
        )
        await db_session.commit()

        # Player leaves
        left_room = await room_manager.leave_room(player.id)

        assert left_room is not None
        assert left_room.id == room.id

        # Verify player marked as disconnected
        await db_session.refresh(player)
        assert player.connected is False

    async def test_leave_room_host_transfer(self, db_session):
        """Test host transfer when host leaves."""
        room_manager = RoomManager(db_session)

        # Create room and add player
        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        _, player = await room_manager.join_room(
            code=room.code,
            player_name="Bob",
            session_id="b" * 64,
        )
        await db_session.commit()

        # Host leaves
        await room_manager.leave_room(host.id)
        await db_session.commit()

        # Verify host transferred
        await db_session.refresh(room)
        await db_session.refresh(player)
        assert room.host_player_id == player.id
        assert player.is_host is True

    async def test_kick_player(self, db_session):
        """Test host kicking a player."""
        room_manager = RoomManager(db_session)

        # Create room and add player
        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        _, player = await room_manager.join_room(
            code=room.code,
            player_name="Bob",
            session_id="b" * 64,
        )
        await db_session.commit()

        # Host kicks player
        result = await room_manager.kick_player(
            room_id=room.id,
            player_id=player.id,
            kicker_id=host.id,
        )

        assert result is True

        # Verify player disconnected
        await db_session.refresh(player)
        assert player.connected is False

    async def test_kick_player_not_host(self, db_session):
        """Test non-host cannot kick players."""
        room_manager = RoomManager(db_session)

        # Create room and add 2 players
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

        # Non-host tries to kick
        with pytest.raises(ValidationError, match="Only host"):
            await room_manager.kick_player(
                room_id=room.id,
                player_id=player2.id,
                kicker_id=player1.id,
            )

    async def test_kick_self(self, db_session):
        """Test cannot kick yourself."""
        room_manager = RoomManager(db_session)

        room, host = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        with pytest.raises(ValidationError, match="Cannot kick yourself"):
            await room_manager.kick_player(
                room_id=room.id,
                player_id=host.id,
                kicker_id=host.id,
            )

    async def test_update_room_status(self, db_session):
        """Test updating room status."""
        room_manager = RoomManager(db_session)

        room, _ = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        # Update to playing
        updated_room = await room_manager.update_room_status(room.id, "playing")
        assert updated_room.status == "playing"

        # Verify in DB
        await db_session.refresh(room)
        assert room.status == "playing"

    async def test_cleanup_stale_rooms(self, db_session):
        """Test cleanup of stale rooms."""
        from datetime import datetime, timedelta

        room_manager = RoomManager(db_session)

        # Create room
        room, _ = await room_manager.create_room(
            host_name="Alice",
            host_session_id="a" * 64,
        )
        await db_session.commit()

        # Make it stale (old last_activity)
        room.last_activity = datetime.utcnow() - timedelta(hours=2)
        await db_session.commit()

        # Cleanup
        count = await room_manager.cleanup_stale_rooms(timeout_hours=1)
        await db_session.commit()

        assert count == 1

        # Verify room deleted
        result = await db_session.execute(select(Room).where(Room.id == room.id))
        assert result.scalar_one_or_none() is None

    async def test_get_active_players_count(self, db_session):
        """Test counting active players."""
        room_manager = RoomManager(db_session)

        # Create room with players
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

        # All connected
        count = await room_manager.get_active_players_count(room.id)
        assert count == 3

        # Disconnect one
        player1.connected = False
        await db_session.commit()

        count = await room_manager.get_active_players_count(room.id)
        assert count == 2
