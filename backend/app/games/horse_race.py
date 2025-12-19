"""Horse race game implementation."""

import asyncio
import random
from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.games.base import BaseGame, GamePhase

logger = get_logger()


class HorseRace(BaseGame):
    """
    Horse race betting game.

    Players bet on which horse will win the race, then watch the race unfold.
    """

    # Game constants
    NUM_HORSES = 4
    TRACK_LENGTH = 100
    BETTING_DURATION = 15  # seconds
    RACE_UPDATES_PER_SECOND = 10
    WIN_POINTS = 100
    PLACE_POINTS = 50  # 2nd place

    HORSE_NAMES = ["Thunder", "Lightning", "Storm", "Blaze"]
    HORSE_COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A"]

    @classmethod
    def game_type(cls) -> str:
        """Return game type identifier."""
        return "horse_race"

    @classmethod
    def display_name(cls) -> str:
        """Return human-readable name."""
        return "Horse Race"

    @classmethod
    def min_players(cls) -> int:
        """Minimum players required."""
        return 2

    @classmethod
    def max_players(cls) -> int:
        """Maximum players allowed."""
        return 12

    async def start(self) -> dict[str, Any]:
        """
        Start the game with betting phase.

        Returns:
            dict: Initial game state
        """
        self.state.phase = GamePhase.SETUP
        self.state.started_at = datetime.utcnow()

        # Initialize horse data
        self.state.round_data = {
            "horses": [
                {
                    "id": i,
                    "name": self.HORSE_NAMES[i],
                    "color": self.HORSE_COLORS[i],
                    "position": 0,
                }
                for i in range(self.NUM_HORSES)
            ],
            "betting_end_time": None,
            "race_start_time": None,
            "race_end_time": None,
            "winner": None,
        }

        # Initialize player bets
        for player_id in self.player_ids:
            self.state.player_data[player_id] = {
                "bet": None,  # Horse ID player bet on
                "bet_placed": False,
            }

        # Initialize scores to 0
        for player_id in self.player_ids:
            self.state.scores[player_id] = 0

        logger.info(
            "Started horse race betting phase",
            room_code=self.room_code,
            betting_duration=self.BETTING_DURATION,
        )

        return {
            "phase": self.state.phase.value,
            "horses": self.state.round_data["horses"],
            "betting_duration": self.BETTING_DURATION,
        }

    async def handle_player_action(
        self, player_id: str, action: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle player actions (betting).

        Args:
            player_id: Player session ID
            action: Action type
            data: Action data

        Returns:
            dict: Response data
        """
        if action == "place_bet":
            return await self._handle_place_bet(player_id, data)
        elif action == "start_race":
            # Only host can start race (if all bets placed or time expired)
            return await self._start_race()
        else:
            return {"error": f"Unknown action: {action}"}

    async def _handle_place_bet(
        self, player_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle a player placing a bet."""
        if self.state.phase != GamePhase.SETUP:
            return {"error": "Betting phase is over"}

        horse_id = data.get("horse_id")
        if horse_id is None or horse_id < 0 or horse_id >= self.NUM_HORSES:
            return {"error": "Invalid horse ID"}

        # Record the bet
        self.state.player_data[player_id]["bet"] = horse_id
        self.state.player_data[player_id]["bet_placed"] = True

        logger.info(
            "Player placed bet",
            room_code=self.room_code,
            player_id=player_id,
            horse_id=horse_id,
        )

        return {
            "success": True,
            "bet": horse_id,
            "horse_name": self.HORSE_NAMES[horse_id],
        }

    async def _start_race(self) -> dict[str, Any]:
        """Start the race simulation."""
        if self.state.phase != GamePhase.SETUP:
            return {"error": "Race already started"}

        self.state.phase = GamePhase.PLAYING
        self.state.round_data["race_start_time"] = datetime.utcnow().isoformat()

        logger.info("Starting horse race", room_code=self.room_code)

        # Run the race simulation
        await self._simulate_race()

        return {"success": True, "phase": "playing"}

    async def _simulate_race(self) -> None:
        """Simulate the race with realistic movement."""
        horses = self.state.round_data["horses"]
        finished_horses: list[int] = []

        # Race until all horses finish
        while len(finished_horses) < self.NUM_HORSES:
            # Update each horse position
            for i, horse in enumerate(horses):
                if i in finished_horses:
                    continue

                # Random movement (2-8 units per update)
                movement = random.uniform(2.0, 8.0)
                horse["position"] = min(
                    self.TRACK_LENGTH, horse["position"] + movement
                )

                # Check if horse finished
                if horse["position"] >= self.TRACK_LENGTH:
                    finished_horses.append(i)
                    logger.info(
                        "Horse finished",
                        room_code=self.room_code,
                        horse_id=i,
                        horse_name=horse["name"],
                        position_in_race=len(finished_horses),
                    )

            # Small delay between updates
            await asyncio.sleep(1.0 / self.RACE_UPDATES_PER_SECOND)

        # Record winner
        self.state.round_data["winner"] = finished_horses[0]
        self.state.round_data["second_place"] = (
            finished_horses[1] if len(finished_horses) > 1 else None
        )
        self.state.round_data["race_end_time"] = datetime.utcnow().isoformat()

        # Calculate scores
        await self._calculate_scores(finished_horses)

        # Move to finished phase
        self.state.phase = GamePhase.FINISHED
        self.state.finished_at = datetime.utcnow()
        self.state.winner_id = self._calculate_winner()

        logger.info(
            "Horse race finished",
            room_code=self.room_code,
            winner_horse=finished_horses[0],
            winner_player=self.state.winner_id,
        )

    async def _calculate_scores(self, finished_horses: list[int]) -> None:
        """
        Calculate scores based on bets.

        Args:
            finished_horses: List of horse IDs in finishing order
        """
        winner_horse = finished_horses[0]
        second_place_horse = finished_horses[1] if len(finished_horses) > 1 else None

        for player_id in self.player_ids:
            player_bet = self.state.player_data[player_id].get("bet")

            if player_bet is None:
                # No bet placed
                self.state.scores[player_id] = 0
            elif player_bet == winner_horse:
                # Bet on winner
                self.state.scores[player_id] = self.WIN_POINTS
            elif player_bet == second_place_horse:
                # Bet on second place
                self.state.scores[player_id] = self.PLACE_POINTS
            else:
                # Lost bet
                self.state.scores[player_id] = 0

    async def get_state_for_player(self, player_id: str) -> dict[str, Any]:
        """
        Get game state for a specific player.

        Args:
            player_id: Player session ID

        Returns:
            dict: Player-specific state
        """
        player_data = self.state.player_data.get(player_id, {})

        state = {
            "phase": self.state.phase.value,
            "your_bet": player_data.get("bet"),
            "your_score": self.state.scores.get(player_id, 0),
            "horses": self.state.round_data.get("horses", []),
        }

        if self.state.phase == GamePhase.FINISHED:
            state["winner"] = self.state.round_data.get("winner")
            state["all_scores"] = self.state.scores

        return state

    async def get_state_for_display(self) -> dict[str, Any]:
        """
        Get game state for display screen.

        Returns:
            dict: Display state
        """
        state = {
            "phase": self.state.phase.value,
            "horses": self.state.round_data.get("horses", []),
            "betting_duration": self.BETTING_DURATION,
        }

        if self.state.phase == GamePhase.PLAYING:
            state["race_started"] = True

        if self.state.phase == GamePhase.FINISHED:
            state["winner"] = self.state.round_data.get("winner")
            state["second_place"] = self.state.round_data.get("second_place")
            state["final_positions"] = [
                {"horse_id": i, "position": horse["position"]}
                for i, horse in enumerate(self.state.round_data["horses"])
            ]

        return state

    async def get_results(self) -> dict[str, Any]:
        """
        Get final game results.

        Returns:
            dict: Results with scores and winner
        """
        winner_horse = self.state.round_data.get("winner")

        results = {
            "game_type": self.game_type(),
            "winner_id": self.state.winner_id,
            "winner_horse": winner_horse,
            "winner_horse_name": (
                self.HORSE_NAMES[winner_horse] if winner_horse is not None else None
            ),
            "scores": self.state.scores,
            "player_bets": {
                player_id: data.get("bet")
                for player_id, data in self.state.player_data.items()
            },
        }

        return results
