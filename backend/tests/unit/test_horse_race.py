"""Unit tests for horse race game."""

import pytest

from app.games.base import GamePhase
from app.games.horse_race import HorseRace


class TestHorseRaceGameInfo:
    """Test horse race game information methods."""

    def test_game_type(self):
        """Test game type identifier."""
        assert HorseRace.game_type() == "horse_race"

    def test_display_name(self):
        """Test display name."""
        assert HorseRace.display_name() == "Horse Race"

    def test_min_players(self):
        """Test minimum players."""
        assert HorseRace.min_players() == 2
        assert HorseRace.min_players() > 0

    def test_max_players(self):
        """Test maximum players."""
        assert HorseRace.max_players() == 12
        assert HorseRace.max_players() >= HorseRace.min_players()


class TestHorseRaceInitialization:
    """Test horse race initialization."""

    def test_init(self):
        """Test game initialization."""
        room_code = "TEST123"
        player_ids = ["player1", "player2", "player3"]

        game = HorseRace(room_code=room_code, player_ids=player_ids)

        assert game.room_code == room_code
        assert game.player_ids == player_ids
        assert game.state.game_type == "horse_race"
        assert game.state.phase == GamePhase.WAITING
        assert not game.is_finished()

    def test_init_with_min_players(self):
        """Test initialization with minimum players."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        assert len(game.player_ids) == 2

    def test_init_with_max_players(self):
        """Test initialization with maximum players."""
        player_ids = [f"player{i}" for i in range(12)]
        game = HorseRace(room_code="TEST", player_ids=player_ids)
        assert len(game.player_ids) == 12


class TestHorseRaceStart:
    """Test horse race start phase."""

    @pytest.mark.asyncio
    async def test_start_initializes_game(self):
        """Test that start initializes the game properly."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        result = await game.start()

        # Should move to setup (betting) phase
        assert game.state.phase == GamePhase.SETUP
        assert game.state.started_at is not None

        # Should return initial state
        assert "phase" in result
        assert result["phase"] == "setup"
        assert "horses" in result
        assert len(result["horses"]) == HorseRace.NUM_HORSES
        assert "betting_duration" in result

    @pytest.mark.asyncio
    async def test_start_initializes_horses(self):
        """Test that horses are initialized correctly."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        await game.start()

        horses = game.state.round_data["horses"]
        assert len(horses) == HorseRace.NUM_HORSES

        for i, horse in enumerate(horses):
            assert horse["id"] == i
            assert "name" in horse
            assert "color" in horse
            assert horse["position"] == 0

    @pytest.mark.asyncio
    async def test_start_initializes_player_data(self):
        """Test that player data is initialized."""
        player_ids = ["p1", "p2", "p3"]
        game = HorseRace(room_code="TEST", player_ids=player_ids)
        await game.start()

        for player_id in player_ids:
            assert player_id in game.state.player_data
            assert game.state.player_data[player_id]["bet"] is None
            assert game.state.player_data[player_id]["bet_placed"] is False
            assert game.state.scores[player_id] == 0


class TestHorseRaceBetting:
    """Test horse race betting phase."""

    @pytest.mark.asyncio
    async def test_place_bet_success(self):
        """Test successful bet placement."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        await game.start()

        result = await game.handle_player_action("p1", "place_bet", {"horse_id": 0})

        assert result["success"] is True
        assert result["bet"] == 0
        assert "horse_name" in result
        assert game.state.player_data["p1"]["bet"] == 0
        assert game.state.player_data["p1"]["bet_placed"] is True

    @pytest.mark.asyncio
    async def test_place_bet_different_horses(self):
        """Test players betting on different horses."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        await game.start()

        await game.handle_player_action("p1", "place_bet", {"horse_id": 0})
        await game.handle_player_action("p2", "place_bet", {"horse_id": 1})

        assert game.state.player_data["p1"]["bet"] == 0
        assert game.state.player_data["p2"]["bet"] == 1

    @pytest.mark.asyncio
    async def test_place_bet_invalid_horse_id(self):
        """Test bet with invalid horse ID."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        await game.start()

        result = await game.handle_player_action("p1", "place_bet", {"horse_id": 99})

        assert "error" in result
        assert game.state.player_data["p1"]["bet"] is None

    @pytest.mark.asyncio
    async def test_place_bet_negative_horse_id(self):
        """Test bet with negative horse ID."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        await game.start()

        result = await game.handle_player_action("p1", "place_bet", {"horse_id": -1})

        assert "error" in result

    @pytest.mark.asyncio
    async def test_place_bet_change_bet(self):
        """Test changing bet."""
        game = HorseRace(room_code="TEST", player_ids=["p1"])
        await game.start()

        # Place initial bet
        await game.handle_player_action("p1", "place_bet", {"horse_id": 0})
        # Change bet
        await game.handle_player_action("p1", "place_bet", {"horse_id": 1})

        assert game.state.player_data["p1"]["bet"] == 1


class TestHorseRaceGameState:
    """Test getting game state."""

    @pytest.mark.asyncio
    async def test_get_state_for_player_during_betting(self):
        """Test player state during betting phase."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        await game.start()
        await game.handle_player_action("p1", "place_bet", {"horse_id": 0})

        state = await game.get_state_for_player("p1")

        assert state["phase"] == "setup"
        assert state["your_bet"] == 0
        assert "horses" in state

    @pytest.mark.asyncio
    async def test_get_state_for_display_during_betting(self):
        """Test display state during betting phase."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        await game.start()

        state = await game.get_state_for_display()

        assert state["phase"] == "setup"
        assert "horses" in state
        assert len(state["horses"]) == HorseRace.NUM_HORSES
        assert "betting_duration" in state

    @pytest.mark.asyncio
    async def test_get_current_scores(self):
        """Test getting current scores."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        await game.start()

        scores = game.get_current_scores()

        assert "p1" in scores
        assert "p2" in scores
        assert scores["p1"] == 0
        assert scores["p2"] == 0


class TestHorseRaceResults:
    """Test game results."""

    @pytest.mark.asyncio
    async def test_get_results_structure(self):
        """Test results structure."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        await game.start()

        # Manually set finished state for testing
        game.state.phase = GamePhase.FINISHED
        game.state.round_data["winner"] = 0

        results = await game.get_results()

        assert "game_type" in results
        assert results["game_type"] == "horse_race"
        assert "winner_horse" in results
        assert "scores" in results
        assert "player_bets" in results


class TestHorseRaceHelpers:
    """Test helper methods."""

    def test_is_finished_false(self):
        """Test is_finished when game not finished."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        assert not game.is_finished()

    def test_is_finished_true(self):
        """Test is_finished when game finished."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        game.state.phase = GamePhase.FINISHED
        assert game.is_finished()

    def test_calculate_winner_with_clear_winner(self):
        """Test winner calculation with clear winner."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2", "p3"])
        game.state.scores = {"p1": 100, "p2": 50, "p3": 0}

        winner = game._calculate_winner()
        assert winner == "p1"

    def test_calculate_winner_with_tie(self):
        """Test winner calculation with tie."""
        game = HorseRace(room_code="TEST", player_ids=["p1", "p2"])
        game.state.scores = {"p1": 100, "p2": 100}

        winner = game._calculate_winner()
        assert winner is None  # Tie

    def test_calculate_winner_no_scores(self):
        """Test winner calculation with no scores."""
        game = HorseRace(room_code="TEST", player_ids=["p1"])
        game.state.scores = {}

        winner = game._calculate_winner()
        assert winner is None
