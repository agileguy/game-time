"""Player management service."""

from datetime import datetime
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import PlayerNotFoundError
from app.core.security import generate_session_id, get_session_expiry
from app.models import Player


class PlayerManager:
    """Service for managing players and sessions."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        """
        Initialize player manager.

        Args:
            db: Database session
            redis: Redis client
        """
        self.db = db
        self.redis = redis

    async def create_session(self) -> str:
        """
        Create a new player session.

        Returns:
            str: Session ID
        """
        session_id = generate_session_id()
        expiry = get_session_expiry()

        # Store session in Redis
        await self.redis.setex(
            f"session:{session_id}",
            int((expiry - datetime.utcnow()).total_seconds()),
            "active",
        )

        return session_id

    async def validate_session(self, session_id: str) -> bool:
        """
        Check if a session is valid.

        Args:
            session_id: Session ID to validate

        Returns:
            bool: True if session is valid
        """
        session_data = await self.redis.get(f"session:{session_id}")
        return session_data is not None

    async def get_player_by_session(self, session_id: str) -> Optional[Player]:
        """
        Get player by session ID.

        Args:
            session_id: Session ID

        Returns:
            Optional[Player]: Player if found
        """
        result = await self.db.execute(
            select(Player).where(Player.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """
        Get player by ID.

        Args:
            player_id: Player ID

        Returns:
            Optional[Player]: Player if found
        """
        result = await self.db.execute(select(Player).where(Player.id == player_id))
        return result.scalar_one_or_none()

    async def update_player_connection(
        self, player_id: int, connected: bool
    ) -> Optional[Player]:
        """
        Update player connection status.

        Args:
            player_id: Player ID
            connected: Connection status

        Returns:
            Optional[Player]: Updated player
        """
        player = await self.get_player_by_id(player_id)
        if not player:
            return None

        player.connected = connected
        player.last_seen = datetime.utcnow()
        await self.db.flush()

        return player

    async def update_last_seen(self, player_id: int) -> Optional[Player]:
        """
        Update player's last seen timestamp.

        Args:
            player_id: Player ID

        Returns:
            Optional[Player]: Updated player
        """
        player = await self.get_player_by_id(player_id)
        if not player:
            return None

        player.last_seen = datetime.utcnow()
        await self.db.flush()

        return player

    async def store_connection(
        self, session_id: str, connection_id: str, room_code: str
    ) -> None:
        """
        Store WebSocket connection info in Redis.

        Args:
            session_id: Player session ID
            connection_id: WebSocket connection ID
            room_code: Room code player is in
        """
        # Store connection mapping
        await self.redis.setex(
            f"connection:{session_id}",
            settings.session_expire_hours * 3600,
            connection_id,
        )

        # Store room association
        await self.redis.setex(
            f"player_room:{session_id}",
            settings.session_expire_hours * 3600,
            room_code,
        )

    async def get_connection_id(self, session_id: str) -> Optional[str]:
        """
        Get WebSocket connection ID for a session.

        Args:
            session_id: Session ID

        Returns:
            Optional[str]: Connection ID if found
        """
        connection_id = await self.redis.get(f"connection:{session_id}")
        return connection_id

    async def get_player_room(self, session_id: str) -> Optional[str]:
        """
        Get room code for a player's session.

        Args:
            session_id: Session ID

        Returns:
            Optional[str]: Room code if found
        """
        room_code = await self.redis.get(f"player_room:{session_id}")
        return room_code

    async def remove_connection(self, session_id: str) -> None:
        """
        Remove WebSocket connection info.

        Args:
            session_id: Session ID
        """
        await self.redis.delete(f"connection:{session_id}")
        await self.redis.delete(f"player_room:{session_id}")

    async def is_player_connected(self, player_id: int) -> bool:
        """
        Check if player has an active WebSocket connection.

        Args:
            player_id: Player ID

        Returns:
            bool: True if connected
        """
        player = await self.get_player_by_id(player_id)
        if not player:
            return False

        connection_id = await self.get_connection_id(player.session_id)
        return connection_id is not None and player.connected

    async def get_room_players(self, room_id: int, connected_only: bool = False) -> list[Player]:
        """
        Get all players in a room.

        Args:
            room_id: Room ID
            connected_only: Only return connected players

        Returns:
            list[Player]: List of players
        """
        query = select(Player).where(Player.room_id == room_id)

        if connected_only:
            query = query.where(Player.connected == True)  # noqa: E712

        result = await self.db.execute(query)
        return list(result.scalars().all())
