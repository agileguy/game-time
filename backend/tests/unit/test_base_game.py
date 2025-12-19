"""Unit tests for base game classes."""

from datetime import datetime

import pytest

from app.games.base import BaseGame, GamePhase, GameState


class TestGamePhase:
    """Test GamePhase enum."""

    def test_game_phases_exist(self):
        """Test all game phases are defined."""
        assert GamePhase.WAITING == "waiting"
        assert GamePhase.SETUP == "setup"
        assert GamePhase.PLAYING == "playing"
        assert GamePhase.ROUND_END == "round_end"
        assert GamePhase.FINISHED == "finished"


class TestGameState:
    """Test GameState dataclass."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        state = GameState(game_type="test_game")

        assert state.game_type == "test_game"
        assert state.phase == GamePhase.WAITING
        assert state.current_round == 0
        assert state.total_rounds == 1
        assert state.round_data == {}
        assert state.player_data == {}
        assert state.scores == {}
        assert state.started_at is None
        assert state.finished_at is None
        assert state.winner_id is None

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        started_at = datetime.utcnow()
        state = GameState(
            game_type="custom_game",
            phase=GamePhase.PLAYING,
            current_round=2,
            total_rounds=5,
            round_data={"key": "value"},
            player_data={"p1": {"score": 100}},
            scores={"p1": 100},
            started_at=started_at,
        )

        assert state.game_type == "custom_game"
        assert state.phase == GamePhase.PLAYING
        assert state.current_round == 2
        assert state.total_rounds == 5
        assert state.round_data == {"key": "value"}
        assert state.player_data == {"p1": {"score": 100}}
        assert state.scores == {"p1": 100}
        assert state.started_at == started_at

    def test_to_dict(self):
        """Test converting state to dictionary."""
        state = GameState(game_type="test")
        state.scores = {"p1": 50, "p2": 75}

        state_dict = state.to_dict()

        assert state_dict["game_type"] == "test"
        assert state_dict["phase"] == "waiting"
        assert state_dict["current_round"] == 0
        assert state_dict["scores"] == {"p1": 50, "p2": 75}
        assert state_dict["started_at"] is None
        assert state_dict["finished_at"] is None

    def test_to_dict_with_timestamps(self):
        """Test to_dict with timestamp conversion."""
        started_at = datetime.utcnow()
        finished_at = datetime.utcnow()

        state = GameState(
            game_type="test",
            started_at=started_at,
            finished_at=finished_at,
        )

        state_dict = state.to_dict()

        assert state_dict["started_at"] == started_at.isoformat()
        assert state_dict["finished_at"] == finished_at.isoformat()

    def test_from_dict(self):
        """Test creating state from dictionary."""
        data = {
            "game_type": "test",
            "phase": "playing",
            "current_round": 3,
            "total_rounds": 5,
            "round_data": {"round": 3},
            "player_data": {"p1": {"ready": True}},
            "scores": {"p1": 100},
            "started_at": None,
            "finished_at": None,
            "winner_id": None,
        }

        state = GameState.from_dict(data)

        assert state.game_type == "test"
        assert state.phase == GamePhase.PLAYING
        assert state.current_round == 3
        assert state.total_rounds == 5
        assert state.round_data == {"round": 3}
        assert state.player_data == {"p1": {"ready": True}}
        assert state.scores == {"p1": 100}

    def test_from_dict_with_timestamps(self):
        """Test from_dict with timestamp parsing."""
        started_str = datetime.utcnow().isoformat()
        finished_str = datetime.utcnow().isoformat()

        data = {
            "game_type": "test",
            "started_at": started_str,
            "finished_at": finished_str,
        }

        state = GameState.from_dict(data)

        assert state.started_at is not None
        assert state.finished_at is not None
        assert state.started_at.isoformat() == started_str
        assert state.finished_at.isoformat() == finished_str


class MockGame(BaseGame):
    """Mock game implementation for testing."""

    @classmethod
    def game_type(cls) -> str:
        return "mock_game"

    @classmethod
    def display_name(cls) -> str:
        return "Mock Game"

    @classmethod
    def min_players(cls) -> int:
        return 2

    @classmethod
    def max_players(cls) -> int:
        return 8

    async def start(self):
        self.state.phase = GamePhase.PLAYING
        return {"started": True}

    async def handle_player_action(self, player_id, action, data):
        return {"action": action, "player_id": player_id}

    async def get_state_for_player(self, player_id):
        return {"player_id": player_id, "phase": self.state.phase.value}

    async def get_state_for_display(self):
        return {"phase": self.state.phase.value}

    async def get_results(self):
        return {"winner_id": self.state.winner_id, "scores": self.state.scores}


class TestBaseGame:
    """Test BaseGame abstract class functionality."""

    def test_init(self):
        """Test base game initialization."""
        room_code = "ROOM123"
        player_ids = ["p1", "p2", "p3"]

        game = MockGame(room_code=room_code, player_ids=player_ids)

        assert game.room_code == room_code
        assert game.player_ids == player_ids
        assert game.state.game_type == "mock_game"
        assert game.state.phase == GamePhase.WAITING

    @pytest.mark.asyncio
    async def test_start(self):
        """Test starting a game."""
        game = MockGame(room_code="TEST", player_ids=["p1", "p2"])
        result = await game.start()

        assert result["started"] is True
        assert game.state.phase == GamePhase.PLAYING

    @pytest.mark.asyncio
    async def test_handle_player_action(self):
        """Test handling player actions."""
        game = MockGame(room_code="TEST", player_ids=["p1"])
        result = await game.handle_player_action("p1", "test_action", {})

        assert result["action"] == "test_action"
        assert result["player_id"] == "p1"

    @pytest.mark.asyncio
    async def test_get_state_for_player(self):
        """Test getting state for specific player."""
        game = MockGame(room_code="TEST", player_ids=["p1"])
        state = await game.get_state_for_player("p1")

        assert state["player_id"] == "p1"
        assert "phase" in state

    @pytest.mark.asyncio
    async def test_get_state_for_display(self):
        """Test getting state for display."""
        game = MockGame(room_code="TEST", player_ids=["p1"])
        state = await game.get_state_for_display()

        assert "phase" in state

    @pytest.mark.asyncio
    async def test_get_results(self):
        """Test getting game results."""
        game = MockGame(room_code="TEST", player_ids=["p1", "p2"])
        game.state.scores = {"p1": 100, "p2": 50}
        game.state.winner_id = "p1"

        results = await game.get_results()

        assert results["winner_id"] == "p1"
        assert results["scores"] == {"p1": 100, "p2": 50}

    def test_is_finished_false(self):
        """Test is_finished when game not finished."""
        game = MockGame(room_code="TEST", player_ids=["p1"])
        assert not game.is_finished()

    def test_is_finished_true(self):
        """Test is_finished when game finished."""
        game = MockGame(room_code="TEST", player_ids=["p1"])
        game.state.phase = GamePhase.FINISHED
        assert game.is_finished()

    def test_get_current_scores(self):
        """Test getting current scores."""
        game = MockGame(room_code="TEST", player_ids=["p1", "p2"])
        game.state.scores = {"p1": 75, "p2": 100}

        scores = game.get_current_scores()

        assert scores == {"p1": 75, "p2": 100}
        # Verify it's a copy
        scores["p1"] = 999
        assert game.state.scores["p1"] == 75

    def test_calculate_winner_clear(self):
        """Test calculating winner with clear winner."""
        game = MockGame(room_code="TEST", player_ids=["p1", "p2", "p3"])
        game.state.scores = {"p1": 100, "p2": 75, "p3": 50}

        winner = game._calculate_winner()

        assert winner == "p1"

    def test_calculate_winner_tie(self):
        """Test calculating winner with tie."""
        game = MockGame(room_code="TEST", player_ids=["p1", "p2"])
        game.state.scores = {"p1": 100, "p2": 100}

        winner = game._calculate_winner()

        assert winner is None

    def test_calculate_winner_empty(self):
        """Test calculating winner with no scores."""
        game = MockGame(room_code="TEST", player_ids=["p1"])
        game.state.scores = {}

        winner = game._calculate_winner()

        assert winner is None

    @pytest.mark.asyncio
    async def test_handle_player_disconnect(self):
        """Test default disconnect handler."""
        game = MockGame(room_code="TEST", player_ids=["p1", "p2"])
        result = await game.handle_player_disconnect("p1")

        assert result == {}

    @pytest.mark.asyncio
    async def test_handle_player_reconnect(self):
        """Test reconnect handler."""
        game = MockGame(room_code="TEST", player_ids=["p1"])
        result = await game.handle_player_reconnect("p1")

        assert "player_id" in result
        assert result["player_id"] == "p1"
