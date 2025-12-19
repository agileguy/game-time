"""Game manager service for handling game lifecycle and state."""

from datetime import datetime
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import GameStateError, RoomNotFoundError
from app.core.logging import get_logger
from app.games.base import BaseGame
from app.models.game_session import GameSession
from app.models.room import Room
from app.models.score import Score

logger = get_logger()


class GameRegistry:
    """Registry for available game types."""

    _games: dict[str, type[BaseGame]] = {}

    @classmethod
    def register(cls, game_class: type[BaseGame]) -> None:
        """
        Register a game type.

        Args:
            game_class: Game class to register
        """
        game_type = game_class.game_type()
        cls._games[game_type] = game_class
        logger.info(f"Registered game type: {game_type}")

    @classmethod
    def get(cls, game_type: str) -> type[BaseGame] | None:
        """
        Get a registered game class.

        Args:
            game_type: Game type identifier

        Returns:
            Type[BaseGame] | None: Game class or None if not found
        """
        return cls._games.get(game_type)

    @classmethod
    def list_games(cls) -> list[dict[str, Any]]:
        """
        List all registered games.

        Returns:
            list: List of game info dicts
        """
        return [
            {
                "type": game_class.game_type(),
                "name": game_class.display_name(),
                "min_players": game_class.min_players(),
                "max_players": game_class.max_players(),
            }
            for game_class in cls._games.values()
        ]


class GameManager:
    """
    Game manager service.

    Handles game instances, lifecycle, and state persistence.
    """

    def __init__(self, redis: aioredis.Redis):
        """
        Initialize game manager.

        Args:
            redis: Redis client for state caching
        """
        self.redis = redis
        self._active_games: dict[str, BaseGame] = {}
        self._games_needing_broadcast: set[str] = set()

    async def create_game(
        self,
        db: AsyncSession,
        room_code: str,
        game_type: str,
    ) -> BaseGame:
        """
        Create a new game instance.

        Args:
            db: Database session
            room_code: Room code
            game_type: Type of game to create

        Returns:
            BaseGame: Created game instance

        Raises:
            RoomNotFoundError: If room doesn't exist
            GameStateError: If game type is invalid or game already active
        """
        # Expire all cached objects to ensure fresh data from database
        # This is critical for transaction isolation - we need to see all committed player joins
        db.expire_all()

        # Get the room with players
        room_result = await db.execute(
            select(Room).filter(Room.code == room_code).options(selectinload(Room.players))
        )
        room = room_result.scalar_one_or_none()

        if not room:
            raise RoomNotFoundError(room_code)

        # Check if game already active
        if room_code in self._active_games:
            raise GameStateError(
                f"Game already active in room {room_code}",
                current_state="active",
            )

        # Get game class
        game_class = GameRegistry.get(game_type)
        if not game_class:
            raise GameStateError(
                f"Invalid game type: {game_type}",
                current_state="invalid",
            )

        # Validate player count
        player_count = len(room.players)
        logger.info(f"Room {room_code} has {player_count} players: {[p.name for p in room.players]}")
        if player_count < game_class.min_players():
            raise GameStateError(
                f"Not enough players. Need at least {game_class.min_players()}",
                current_state=f"{player_count}_players",
            )

        if player_count > game_class.max_players():
            raise GameStateError(
                f"Too many players. Maximum is {game_class.max_players()}",
                current_state=f"{player_count}_players",
            )

        # Get player session IDs
        player_ids = [player.session_id for player in room.players]

        # Create game instance
        game = game_class(room_code=room_code, player_ids=player_ids)
        self._active_games[room_code] = game

        # Create database game session
        game_session = GameSession(
            room_id=room.id,
            game_type=game_type,
            state=game.state.to_dict(),
            started_at=datetime.utcnow(),
        )
        db.add(game_session)

        # Flush to get the game_session.id before creating scores
        await db.flush()

        # Create score records for each player
        for player in room.players:
            score = Score(
                game_session_id=game_session.id,
                player_id=player.id,
                score=0,
            )
            db.add(score)

        await db.commit()

        # Cache game state in Redis
        await self._cache_game_state(room_code, game)

        logger.info(
            f"Created {game_type} game",
            room_code=room_code,
            player_count=player_count,
        )

        return game

    async def get_game(self, room_code: str) -> BaseGame | None:
        """
        Get active game for a room.

        Args:
            room_code: Room code

        Returns:
            BaseGame | None: Game instance or None
        """
        return self._active_games.get(room_code)

    async def start_game(self, room_code: str) -> dict[str, Any]:
        """
        Start a game.

        Args:
            room_code: Room code

        Returns:
            dict: Initial game state

        Raises:
            GameStateError: If no game is active
        """
        game = self._active_games.get(room_code)
        if not game:
            raise GameStateError(
                f"No active game in room {room_code}",
                current_state="no_game",
            )

        # Start the game
        initial_state = await game.start()

        # Update cache
        await self._cache_game_state(room_code, game)

        logger.info("Started game", room_code=room_code, game_type=game.game_type())

        return initial_state

    async def handle_player_action(
        self,
        room_code: str,
        player_id: str,
        action: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle a player action in a game.

        Args:
            room_code: Room code
            player_id: Player session ID
            action: Action type
            data: Action data

        Returns:
            dict: Response data

        Raises:
            GameStateError: If no game is active
        """
        game = self._active_games.get(room_code)
        if not game:
            raise GameStateError(
                f"No active game in room {room_code}",
                current_state="no_game",
            )

        # Handle the action
        response = await game.handle_player_action(player_id, action, data)

        # Update cache
        await self._cache_game_state(room_code, game)

        return response

    async def get_state_for_player(
        self, room_code: str, player_id: str
    ) -> dict[str, Any]:
        """
        Get game state for a specific player.

        Args:
            room_code: Room code
            player_id: Player session ID

        Returns:
            dict: Player-specific game state

        Raises:
            GameStateError: If no game is active
        """
        game = self._active_games.get(room_code)
        if not game:
            raise GameStateError(
                f"No active game in room {room_code}",
                current_state="no_game",
            )

        return await game.get_state_for_player(player_id)

    async def get_state_for_display(self, room_code: str) -> dict[str, Any]:
        """
        Get game state for the display screen.

        Args:
            room_code: Room code

        Returns:
            dict: Display-specific game state

        Raises:
            GameStateError: If no game is active
        """
        game = self._active_games.get(room_code)
        if not game:
            raise GameStateError(
                f"No active game in room {room_code}",
                current_state="no_game",
            )

        return await game.get_state_for_display()

    async def finish_game(
        self,
        db: AsyncSession,
        room_code: str,
    ) -> dict[str, Any]:
        """
        Finish a game and save results.

        Args:
            db: Database session
            room_code: Room code

        Returns:
            dict: Final game results

        Raises:
            GameStateError: If no game is active
        """
        game = self._active_games.get(room_code)
        if not game:
            raise GameStateError(
                f"No active game in room {room_code}",
                current_state="no_game",
            )

        # Get results
        results = await game.get_results()

        # Update database
        room_result = await db.execute(
            select(Room).filter(Room.code == room_code)
        )
        room = room_result.scalar_one_or_none()

        if room:
            # Get the most recent game session
            session_result = await db.execute(
                select(GameSession)
                .filter(GameSession.room_id == room.id)
                .order_by(GameSession.started_at.desc())
                .limit(1)
            )
            game_session = session_result.scalar_one_or_none()

            if game_session:
                # Update game session
                game_session.finished_at = datetime.utcnow()
                game_session.state = game.state.to_dict()
                game_session.winner_id = results.get("winner_id")

                # Update scores
                for player in room.players:
                    score_result = await db.execute(
                        select(Score).filter(
                            Score.game_session_id == game_session.id,
                            Score.player_id == player.id,
                        )
                    )
                    score = score_result.scalar_one_or_none()

                    if score and player.session_id in game.state.scores:
                        score.score = game.state.scores[player.session_id]

                await db.commit()

        # Remove from active games
        del self._active_games[room_code]

        # Clear cache
        await self.redis.delete(f"game:{room_code}")

        logger.info(
            "Finished game",
            room_code=room_code,
            game_type=game.game_type(),
            winner_id=results.get("winner_id"),
        )

        return results

    async def _cache_game_state(self, room_code: str, game: BaseGame) -> None:
        """
        Cache game state in Redis.

        Args:
            room_code: Room code
            game: Game instance
        """
        state_dict = game.state.to_dict()
        await self.redis.setex(
            f"game:{room_code}",
            3600,  # 1 hour TTL
            str(state_dict),
        )


# Global game manager instance (will be initialized with Redis in main.py)
game_manager: GameManager | None = None


def get_game_manager() -> GameManager:
    """
    Get the global game manager instance.

    Returns:
        GameManager: Game manager instance

    Raises:
        RuntimeError: If game manager not initialized
    """
    if game_manager is None:
        raise RuntimeError("Game manager not initialized")
    return game_manager
