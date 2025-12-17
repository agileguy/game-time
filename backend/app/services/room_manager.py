"""Room management service."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import RoomFullError, RoomNotFoundError, ValidationError
from app.core.security import generate_room_code, validate_player_name, validate_room_code
from app.models import Player, Room


class RoomManager:
    """Service for managing game rooms."""

    def __init__(self, db: AsyncSession):
        """
        Initialize room manager.

        Args:
            db: Database session
        """
        self.db = db

    async def create_room(
        self,
        host_name: str,
        host_session_id: str,
        max_players: int = 12,
        is_public: bool = True,
    ) -> tuple[Room, Player]:
        """
        Create a new room with a host player.

        Args:
            host_name: Name of the host player
            host_session_id: Session ID of the host
            max_players: Maximum number of players (2-12)
            is_public: Whether room is public

        Returns:
            tuple[Room, Player]: Created room and host player

        Raises:
            ValidationError: If validation fails
        """
        # Validate inputs
        if not validate_player_name(host_name):
            raise ValidationError("Invalid player name")

        if not (2 <= max_players <= 12):
            raise ValidationError("Max players must be between 2 and 12")

        # Generate unique room code
        code = await self._generate_unique_code()

        # Create room
        room = Room(
            code=code,
            status="lobby",
            max_players=max_players,
            is_public=is_public,
            last_activity=datetime.utcnow(),
        )
        self.db.add(room)
        await self.db.flush()

        # Create host player
        host = Player(
            room_id=room.id,
            name=host_name,
            session_id=host_session_id,
            is_host=True,
            connected=True,
        )
        self.db.add(host)
        await self.db.flush()

        # Update room with host ID
        room.host_player_id = host.id
        await self.db.flush()

        return room, host

    async def get_room_by_code(self, code: str) -> Optional[Room]:
        """
        Get room by code.

        Args:
            code: Room code

        Returns:
            Optional[Room]: Room if found, None otherwise
        """
        if not validate_room_code(code):
            return None

        result = await self.db.execute(
            select(Room)
            .where(Room.code == code.upper())
            .options(selectinload(Room.players))
        )
        return result.scalar_one_or_none()

    async def get_room_by_id(self, room_id: int) -> Optional[Room]:
        """
        Get room by ID.

        Args:
            room_id: Room ID

        Returns:
            Optional[Room]: Room if found, None otherwise
        """
        result = await self.db.execute(
            select(Room).where(Room.id == room_id).options(selectinload(Room.players))
        )
        return result.scalar_one_or_none()

    async def join_room(
        self,
        code: str,
        player_name: str,
        session_id: str,
    ) -> tuple[Room, Player]:
        """
        Join an existing room.

        Args:
            code: Room code
            player_name: Player name
            session_id: Player session ID

        Returns:
            tuple[Room, Player]: Room and new player

        Raises:
            RoomNotFoundError: If room doesn't exist
            RoomFullError: If room is full
            ValidationError: If validation fails
        """
        # Validate inputs
        if not validate_room_code(code):
            raise ValidationError("Invalid room code")

        if not validate_player_name(player_name):
            raise ValidationError("Invalid player name")

        # Expire all to ensure fresh data from database
        # This prevents stale player counts when checking if room is full
        self.db.expire_all()

        # Get room
        room = await self.get_room_by_code(code)
        if not room:
            raise RoomNotFoundError(code)

        # Check if room is in lobby
        if room.status != "lobby":
            raise ValidationError("Cannot join room that is not in lobby")

        # Check if room is full
        active_players = [p for p in room.players if p.connected]
        if len(active_players) >= room.max_players:
            raise RoomFullError(code, room.max_players)

        # Create player
        player = Player(
            room_id=room.id,
            name=player_name,
            session_id=session_id,
            is_host=False,
            connected=True,
        )
        self.db.add(player)

        # Update room activity
        room.last_activity = datetime.utcnow()

        await self.db.flush()

        return room, player

    async def leave_room(self, player_id: int) -> Optional[Room]:
        """
        Player leaves a room.

        Args:
            player_id: Player ID

        Returns:
            Optional[Room]: Room the player left, None if player not found
        """
        result = await self.db.execute(
            select(Player)
            .where(Player.id == player_id)
            .options(selectinload(Player.room))
        )
        player = result.scalar_one_or_none()

        if not player:
            return None

        if not player.room:
            return None

        # Store room_id before expiring
        room_id = player.room.id

        # Expire all to ensure fresh data from database
        self.db.expire_all()

        # Load room with all players for host transfer
        room_result = await self.db.execute(
            select(Room)
            .where(Room.id == room_id)
            .options(selectinload(Room.players))
        )
        room = room_result.scalar_one_or_none()

        # Find the player within room.players and mark as disconnected
        # This ensures we're working with the same object instance
        for p in room.players:
            if p.id == player.id:
                p.connected = False
                player = p  # Use this instance
                break

        await self.db.flush()

        # If player was host, transfer to another player
        if player.is_host and room:
            await self._transfer_host(room)

        # Update room activity
        if room:
            room.last_activity = datetime.utcnow()
            await self.db.flush()

        return room

    async def kick_player(self, room_id: int, player_id: int, kicker_id: int) -> bool:
        """
        Kick a player from a room (host only).

        Args:
            room_id: Room ID
            player_id: Player to kick
            kicker_id: Player doing the kicking (must be host)

        Returns:
            bool: True if kicked successfully

        Raises:
            ValidationError: If kicker is not host
        """
        # Get kicker
        result = await self.db.execute(select(Player).where(Player.id == kicker_id))
        kicker = result.scalar_one_or_none()

        if not kicker or not kicker.is_host:
            raise ValidationError("Only host can kick players")

        # Get player to kick
        result = await self.db.execute(
            select(Player).where(Player.id == player_id, Player.room_id == room_id)
        )
        player = result.scalar_one_or_none()

        if not player:
            return False

        # Can't kick yourself
        if player.id == kicker.id:
            raise ValidationError("Cannot kick yourself")

        # Mark as disconnected
        player.connected = False
        await self.db.flush()

        return True

    async def update_room_status(self, room_id: int, status: str) -> Optional[Room]:
        """
        Update room status.

        Args:
            room_id: Room ID
            status: New status (lobby, playing, finished)

        Returns:
            Optional[Room]: Updated room
        """
        room = await self.get_room_by_id(room_id)
        if not room:
            return None

        room.status = status
        room.last_activity = datetime.utcnow()
        await self.db.flush()

        return room

    async def cleanup_stale_rooms(self, timeout_hours: int = 1) -> int:
        """
        Clean up rooms that have been inactive.

        Args:
            timeout_hours: Hours of inactivity before cleanup

        Returns:
            int: Number of rooms cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=timeout_hours)

        # Get stale rooms
        result = await self.db.execute(
            select(Room).where(Room.last_activity < cutoff_time)
        )
        stale_rooms = result.scalars().all()

        # Delete stale rooms (cascade will delete players)
        count = 0
        for room in stale_rooms:
            await self.db.delete(room)
            count += 1

        await self.db.flush()

        return count

    async def get_active_players_count(self, room_id: int) -> int:
        """
        Get count of active (connected) players in a room.

        Args:
            room_id: Room ID

        Returns:
            int: Number of active players
        """
        result = await self.db.execute(
            select(Player).where(
                Player.room_id == room_id, Player.connected == True  # noqa: E712
            )
        )
        return len(result.scalars().all())

    async def _generate_unique_code(self, max_attempts: int = 10) -> str:
        """
        Generate a unique room code.

        Args:
            max_attempts: Maximum attempts to generate unique code

        Returns:
            str: Unique room code

        Raises:
            RuntimeError: If unable to generate unique code
        """
        for _ in range(max_attempts):
            code = generate_room_code()

            # Check if code exists
            result = await self.db.execute(select(Room).where(Room.code == code))
            if result.scalar_one_or_none() is None:
                return code

        raise RuntimeError("Unable to generate unique room code")

    async def _transfer_host(self, room: Room) -> None:
        """
        Transfer host to another connected player.

        Args:
            room: Room to transfer host in
        """
        # Find another connected player
        for player in room.players:
            if player.connected and not player.is_host:
                player.is_host = True
                room.host_player_id = player.id
                await self.db.flush()
                return

        # No other players, host remains but disconnected
