"""Base game class and interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.core.logging import get_logger

logger = get_logger()


class GamePhase(str, Enum):
    """Game phase enumeration."""

    WAITING = "waiting"  # Waiting for players/game start
    SETUP = "setup"  # Game setup phase (e.g., betting, question display)
    PLAYING = "playing"  # Active gameplay
    ROUND_END = "round_end"  # End of a round
    FINISHED = "finished"  # Game completed


@dataclass
class GameState:
    """
    Game state container.

    Holds all the state for a game instance.
    """

    game_type: str
    phase: GamePhase = GamePhase.WAITING
    current_round: int = 0
    total_rounds: int = 1
    round_data: dict[str, Any] = field(default_factory=dict)
    player_data: dict[str, Any] = field(default_factory=dict)
    scores: dict[str, int] = field(default_factory=dict)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    winner_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "game_type": self.game_type,
            "phase": self.phase.value,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "round_data": self.round_data,
            "player_data": self.player_data,
            "scores": self.scores,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": (self.finished_at.isoformat() if self.finished_at else None),
            "winner_id": self.winner_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        """Create state from dictionary."""
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])

        finished_at = None
        if data.get("finished_at"):
            finished_at = datetime.fromisoformat(data["finished_at"])

        return cls(
            game_type=data["game_type"],
            phase=GamePhase(data.get("phase", "waiting")),
            current_round=data.get("current_round", 0),
            total_rounds=data.get("total_rounds", 1),
            round_data=data.get("round_data", {}),
            player_data=data.get("player_data", {}),
            scores=data.get("scores", {}),
            started_at=started_at,
            finished_at=finished_at,
            winner_id=data.get("winner_id"),
        )


class BaseGame(ABC):
    """
    Abstract base class for all games.

    Defines the game lifecycle and required methods.
    """

    def __init__(self, room_code: str, player_ids: list[str]):
        """
        Initialize game.

        Args:
            room_code: Room code for this game
            player_ids: List of player session IDs
        """
        self.room_code = room_code
        self.player_ids = player_ids
        self.state = GameState(game_type=self.game_type())
        logger.info(
            f"Initialized {self.game_type()} game",
            room_code=room_code,
            player_count=len(player_ids),
        )

    @classmethod
    @abstractmethod
    def game_type(cls) -> str:
        """Return the game type identifier."""
        pass

    @classmethod
    @abstractmethod
    def display_name(cls) -> str:
        """Return the human-readable game name."""
        pass

    @classmethod
    @abstractmethod
    def min_players(cls) -> int:
        """Return minimum number of players required."""
        pass

    @classmethod
    @abstractmethod
    def max_players(cls) -> int:
        """Return maximum number of players allowed."""
        pass

    @abstractmethod
    async def start(self) -> dict[str, Any]:
        """
        Start the game.

        Returns:
            dict: Initial game state to broadcast to players
        """
        pass

    @abstractmethod
    async def handle_player_action(
        self, player_id: str, action: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle a player action.

        Args:
            player_id: Session ID of the player
            action: Action type
            data: Action data

        Returns:
            dict: Response data to send back
        """
        pass

    @abstractmethod
    async def get_state_for_player(self, player_id: str) -> dict[str, Any]:
        """
        Get game state for a specific player.

        Args:
            player_id: Session ID of the player

        Returns:
            dict: Player-specific game state
        """
        pass

    @abstractmethod
    async def get_state_for_display(self) -> dict[str, Any]:
        """
        Get game state for the display screen.

        Returns:
            dict: Display-specific game state
        """
        pass

    @abstractmethod
    async def get_results(self) -> dict[str, Any]:
        """
        Get final game results.

        Returns:
            dict: Final results with scores and winner
        """
        pass

    async def handle_player_disconnect(self, player_id: str) -> dict[str, Any]:
        """
        Handle player disconnection.

        Default implementation does nothing. Override for game-specific logic.

        Args:
            player_id: Session ID of disconnected player

        Returns:
            dict: State update to broadcast
        """
        logger.info(
            f"Player disconnected from {self.game_type()} game",
            room_code=self.room_code,
            player_id=player_id,
        )
        return {}

    async def handle_player_reconnect(self, player_id: str) -> dict[str, Any]:
        """
        Handle player reconnection.

        Args:
            player_id: Session ID of reconnected player

        Returns:
            dict: Current game state for the player
        """
        logger.info(
            f"Player reconnected to {self.game_type()} game",
            room_code=self.room_code,
            player_id=player_id,
        )
        return await self.get_state_for_player(player_id)

    def is_finished(self) -> bool:
        """Check if game is finished."""
        return self.state.phase == GamePhase.FINISHED

    def get_current_scores(self) -> dict[str, int]:
        """
        Get current scores for all players.

        Returns:
            dict: Mapping of player_id to score
        """
        return self.state.scores.copy()

    def _calculate_winner(self) -> str | None:
        """
        Calculate the winner based on scores.

        Returns:
            str | None: Winner's player_id or None if tie
        """
        if not self.state.scores:
            return None

        max_score = max(self.state.scores.values())
        winners = [
            player_id for player_id, score in self.state.scores.items() if score == max_score
        ]

        # Return None if there's a tie
        if len(winners) > 1:
            return None

        return winners[0]
