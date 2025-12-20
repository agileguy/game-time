"""Unit tests for trivia game."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.games.base import GamePhase
from app.games.trivia import Trivia
from app.models.trivia_question import TriviaQuestion


class TestTriviaGameInfo:
    """Test trivia game information methods."""

    def test_game_type(self):
        """Test game type identifier."""
        assert Trivia.game_type() == "trivia"

    def test_display_name(self):
        """Test display name."""
        assert Trivia.display_name() == "Trivia Challenge"

    def test_min_players(self):
        """Test minimum players."""
        assert Trivia.min_players() == 2
        assert Trivia.min_players() > 0

    def test_max_players(self):
        """Test maximum players."""
        assert Trivia.max_players() == 12
        assert Trivia.max_players() >= Trivia.min_players()


class TestTriviaInitialization:
    """Test trivia initialization."""

    def test_init(self):
        """Test game initialization."""
        room_code = "TEST123"
        player_ids = ["player1", "player2", "player3"]

        game = Trivia(room_code=room_code, player_ids=player_ids)

        assert game.room_code == room_code
        assert game.player_ids == player_ids
        assert game.state.game_type == "trivia"
        assert game.state.phase == GamePhase.WAITING
        assert not game.is_finished()

    def test_init_with_min_players(self):
        """Test initialization with minimum players."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])
        assert len(game.player_ids) == 2

    def test_init_with_max_players(self):
        """Test initialization with maximum players."""
        player_ids = [f"player{i}" for i in range(12)]
        game = Trivia(room_code="TEST", player_ids=player_ids)
        assert len(game.player_ids) == 12


class TestTriviaStart:
    """Test trivia start phase."""

    def _create_mock_question(self, id: int) -> TriviaQuestion:
        """Create a mock trivia question."""
        question = MagicMock(spec=TriviaQuestion)
        question.id = id
        question.question = f"Question {id}"
        question.options = ["Option A", "Option B", "Option C", "Option D"]
        question.correct_answer = 0
        question.category = "General"
        question.difficulty = "easy"
        question.to_dict_with_answer.return_value = {
            "id": id,
            "question": f"Question {id}",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "category": "General",
            "difficulty": "easy",
        }
        return question

    @pytest.mark.asyncio
    async def test_start_initializes_game(self):
        """Test that start initializes the game properly."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])

        # Mock database query
        mock_questions = [self._create_mock_question(i) for i in range(5)]
        with patch.object(game, "_load_random_questions", return_value=mock_questions):
            with patch.object(game, "_start_question", new_callable=AsyncMock):
                result = await game.start()

                # Should move to setup phase
                assert game.state.phase == GamePhase.SETUP
                assert game.state.started_at is not None
                assert game.state.total_rounds == Trivia.NUM_QUESTIONS
                assert game.state.current_round == 0

                # Should return initial state
                assert "phase" in result
                assert "current_question" in result
                assert "total_questions" in result

    @pytest.mark.asyncio
    async def test_start_initializes_questions(self):
        """Test that questions are initialized correctly."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])

        mock_questions = [self._create_mock_question(i) for i in range(5)]
        with patch.object(game, "_load_random_questions", return_value=mock_questions):
            with patch.object(game, "_start_question", new_callable=AsyncMock):
                await game.start()

                questions = game.state.round_data["questions"]
                assert len(questions) == Trivia.NUM_QUESTIONS

                for i, q in enumerate(questions):
                    assert q["id"] == i
                    assert "question" in q
                    assert "options" in q
                    assert len(q["options"]) == 4
                    assert "correct_answer" in q

    @pytest.mark.asyncio
    async def test_start_initializes_player_data(self):
        """Test that player data is initialized."""
        player_ids = ["p1", "p2", "p3"]
        game = Trivia(room_code="TEST", player_ids=player_ids)

        mock_questions = [self._create_mock_question(i) for i in range(5)]
        with patch.object(game, "_load_random_questions", return_value=mock_questions):
            with patch.object(game, "_start_question", new_callable=AsyncMock):
                await game.start()

                for player_id in player_ids:
                    assert player_id in game.state.player_data
                    assert game.state.player_data[player_id]["answers"] == []
                    assert game.state.player_data[player_id]["answer_times"] == []
                    assert game.state.player_data[player_id]["correct_count"] == 0
                    assert game.state.scores[player_id] == 0

    @pytest.mark.asyncio
    async def test_start_raises_error_with_insufficient_questions(self):
        """Test that start raises error if not enough questions."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])

        # Only 2 questions available, but need 5
        mock_questions = [self._create_mock_question(i) for i in range(2)]
        with patch.object(game, "_load_random_questions", return_value=mock_questions):
            with pytest.raises(ValueError, match="Not enough questions"):
                await game.start()


class TestTriviaAnswerSubmission:
    """Test trivia answer submission."""

    def _setup_game_with_questions(self, player_ids: list[str]) -> Trivia:
        """Helper to create a game with mocked questions."""
        game = Trivia(room_code="TEST", player_ids=player_ids)
        game.state.phase = GamePhase.SETUP
        game.state.round_data = {
            "questions": [
                {
                    "id": 1,
                    "question": "Test question?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 2,
                    "category": "General",
                    "difficulty": "easy",
                }
            ],
            "current_question_index": 0,
            "question_start_time": datetime.now(timezone.utc).isoformat(),
        }
        for player_id in player_ids:
            game.state.player_data[player_id] = {
                "current_answer": None,
                "answered_at": None,
                "answers": [],
                "answer_times": [],
                "correct_count": 0,
            }
        return game

    @pytest.mark.asyncio
    async def test_submit_answer_success(self):
        """Test successful answer submission."""
        game = self._setup_game_with_questions(["p1", "p2"])

        result = await game.handle_player_action("p1", "submit_answer", {"answer": 2})

        assert result["success"] is True
        assert result["answer"] == 2
        assert game.state.player_data["p1"]["current_answer"] == 2
        assert game.state.player_data["p1"]["answered_at"] is not None

    @pytest.mark.asyncio
    async def test_submit_answer_all_options(self):
        """Test submitting each answer option."""
        game = self._setup_game_with_questions(["p1", "p2", "p3", "p4"])

        for i, player_id in enumerate(["p1", "p2", "p3", "p4"]):
            result = await game.handle_player_action(player_id, "submit_answer", {"answer": i})
            assert result["success"] is True
            assert game.state.player_data[player_id]["current_answer"] == i

    @pytest.mark.asyncio
    async def test_submit_answer_invalid_value(self):
        """Test submitting invalid answer value."""
        game = self._setup_game_with_questions(["p1"])

        result = await game.handle_player_action("p1", "submit_answer", {"answer": 5})
        assert "error" in result

        result = await game.handle_player_action("p1", "submit_answer", {"answer": -1})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_submit_answer_invalid_type(self):
        """Test submitting invalid answer type."""
        game = self._setup_game_with_questions(["p1"])

        result = await game.handle_player_action("p1", "submit_answer", {"answer": "A"})
        assert "error" in result

        result = await game.handle_player_action("p1", "submit_answer", {"answer": None})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_submit_answer_wrong_phase(self):
        """Test submitting answer in wrong phase."""
        game = self._setup_game_with_questions(["p1"])
        game.state.phase = GamePhase.ROUND_END

        result = await game.handle_player_action("p1", "submit_answer", {"answer": 0})
        assert "error" in result
        assert "Not in question phase" in result["error"]

    @pytest.mark.asyncio
    async def test_submit_answer_change_answer(self):
        """Test changing answer."""
        game = self._setup_game_with_questions(["p1"])

        # Submit first answer
        await game.handle_player_action("p1", "submit_answer", {"answer": 0})
        first_time = game.state.player_data["p1"]["answered_at"]

        # Change answer
        await game.handle_player_action("p1", "submit_answer", {"answer": 1})
        second_time = game.state.player_data["p1"]["answered_at"]

        assert game.state.player_data["p1"]["current_answer"] == 1
        assert second_time >= first_time

    @pytest.mark.asyncio
    async def test_unknown_action(self):
        """Test unknown action type."""
        game = self._setup_game_with_questions(["p1"])

        result = await game.handle_player_action("p1", "invalid_action", {})
        assert "error" in result


class TestTriviaScoring:
    """Test trivia scoring calculation."""

    def test_calculate_score_instant_answer(self):
        """Test score for instant answer."""
        game = Trivia(room_code="TEST", player_ids=["p1"])
        score = game._calculate_score(0)
        assert score == Trivia.BASE_POINTS + Trivia.MAX_SPEED_BONUS

    def test_calculate_score_very_fast_answer(self):
        """Test score for very fast answer."""
        game = Trivia(room_code="TEST", player_ids=["p1"])
        score = game._calculate_score(1.0)  # 1 second
        # Should get most of speed bonus
        assert score > Trivia.BASE_POINTS + 40
        assert score <= Trivia.BASE_POINTS + Trivia.MAX_SPEED_BONUS

    def test_calculate_score_medium_speed(self):
        """Test score for medium speed answer."""
        game = Trivia(room_code="TEST", player_ids=["p1"])
        score = game._calculate_score(5.0)  # 5 seconds (half time)
        # Should get about half speed bonus
        expected = Trivia.BASE_POINTS + (Trivia.MAX_SPEED_BONUS // 2)
        assert abs(score - expected) <= 5  # Allow small rounding difference

    def test_calculate_score_slow_answer(self):
        """Test score for slow answer."""
        game = Trivia(room_code="TEST", player_ids=["p1"])
        score = game._calculate_score(9.0)  # 9 seconds
        # Should get minimal speed bonus
        assert score > Trivia.BASE_POINTS
        assert score < Trivia.BASE_POINTS + 10

    def test_calculate_score_at_deadline(self):
        """Test score at exactly deadline."""
        game = Trivia(room_code="TEST", player_ids=["p1"])
        score = game._calculate_score(10.0)  # Exactly at deadline
        assert score == Trivia.BASE_POINTS

    def test_calculate_score_after_deadline(self):
        """Test score after deadline (shouldn't happen but handle gracefully)."""
        game = Trivia(room_code="TEST", player_ids=["p1"])
        score = game._calculate_score(15.0)  # After deadline
        assert score == Trivia.BASE_POINTS


class TestTriviaPhaseTransitions:
    """Test trivia phase transitions."""

    @pytest.mark.asyncio
    async def test_show_question_results(self):
        """Test showing question results."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])
        game.state.phase = GamePhase.SETUP
        game.state.round_data = {
            "questions": [
                {
                    "id": 1,
                    "question": "Test?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 2,
                    "category": "General",
                    "difficulty": "easy",
                }
            ],
            "current_question_index": 0,
            "question_start_time": datetime.now(timezone.utc).isoformat(),
        }

        for player_id in ["p1", "p2"]:
            game.state.player_data[player_id] = {
                "current_answer": 2,  # Correct answer
                "answered_at": datetime.now(timezone.utc).isoformat(),
                "answers": [],
                "answer_times": [],
                "correct_count": 0,
            }
            game.state.scores[player_id] = 0

        await game._show_question_results()

        assert game.state.phase == GamePhase.ROUND_END
        assert game.state.scores["p1"] > 0
        assert game.state.scores["p2"] > 0
        assert game.state.player_data["p1"]["correct_count"] == 1
        assert game.state.player_data["p2"]["correct_count"] == 1

    @pytest.mark.asyncio
    async def test_advance_to_next_question(self):
        """Test advancing to next question."""
        game = Trivia(room_code="TEST", player_ids=["p1"])
        game.state.phase = GamePhase.ROUND_END
        game.state.current_round = 0
        game.state.round_data = {
            "current_question_index": 0,
            "questions": [{"id": i} for i in range(5)],
        }

        with patch.object(game, "_start_question", new_callable=AsyncMock):
            await game._advance_to_next_question()

            assert game.state.phase == GamePhase.SETUP
            assert game.state.round_data["current_question_index"] == 1
            assert game.state.current_round == 1

    @pytest.mark.asyncio
    async def test_advance_to_finish(self):
        """Test advancing to finish after last question."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])
        game.state.phase = GamePhase.ROUND_END
        game.state.round_data = {
            "current_question_index": 4,  # Last question (index 4 of 5)
            "questions": [{"id": i} for i in range(5)],
        }
        game.state.scores = {"p1": 450, "p2": 300}

        await game._advance_to_next_question()

        assert game.state.phase == GamePhase.FINISHED
        assert game.state.finished_at is not None
        assert game.state.winner_id == "p1"


class TestTriviaGameState:
    """Test getting game state."""

    def _create_game_with_state(self) -> Trivia:
        """Helper to create game with test state."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])
        game.state.phase = GamePhase.SETUP
        game.state.round_data = {
            "questions": [
                {
                    "id": 1,
                    "question": "Test question?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 2,
                    "category": "General",
                    "difficulty": "easy",
                }
            ],
            "current_question_index": 0,
            "question_start_time": datetime.now(timezone.utc).isoformat(),
        }
        for player_id in ["p1", "p2"]:
            game.state.player_data[player_id] = {
                "current_answer": None,
                "answered_at": None,
                "answers": [],
                "answer_times": [],
                "correct_count": 0,
            }
            game.state.scores[player_id] = 0
        return game

    @pytest.mark.asyncio
    async def test_get_state_for_player_during_setup(self):
        """Test player state during setup phase."""
        game = self._create_game_with_state()

        state = await game.get_state_for_player("p1")

        assert state["phase"] == "setup"
        assert "current_question" in state
        assert "correct_answer" not in state["current_question"]  # Hidden during setup
        assert state["your_answer"] is None
        assert state["your_score"] == 0

    @pytest.mark.asyncio
    async def test_get_state_for_player_after_answering(self):
        """Test player state after answering."""
        game = self._create_game_with_state()
        game.state.player_data["p1"]["current_answer"] = 2

        state = await game.get_state_for_player("p1")

        assert state["your_answer"] == 2

    @pytest.mark.asyncio
    async def test_get_state_for_player_during_round_end(self):
        """Test player state during round end phase."""
        game = self._create_game_with_state()
        game.state.phase = GamePhase.ROUND_END
        game.state.player_data["p1"]["last_score"] = 130
        game.state.player_data["p1"]["correct_count"] = 1
        game.state.scores["p1"] = 130

        state = await game.get_state_for_player("p1")

        assert state["phase"] == "round_end"
        assert "correct_answer" in state["current_question"]  # Shown in results
        assert state["last_score"] == 130
        assert state["correct_count"] == 1

    @pytest.mark.asyncio
    async def test_get_state_for_display_during_setup(self):
        """Test display state during setup phase."""
        game = self._create_game_with_state()
        game.state.player_data["p1"]["current_answer"] = 0
        game.state.player_data["p2"]["current_answer"] = 1

        state = await game.get_state_for_display()

        assert state["phase"] == "setup"
        assert "current_question" in state
        assert "correct_answer" not in state["current_question"]  # Hidden
        assert state["answer_counts"] == [1, 1, 0, 0]
        assert len(state["players_answered"]) == 2
        assert state["total_players"] == 2

    @pytest.mark.asyncio
    async def test_get_state_for_display_during_round_end(self):
        """Test display state during round end phase."""
        game = self._create_game_with_state()
        game.state.phase = GamePhase.ROUND_END
        game.state.player_data["p1"]["current_answer"] = 2
        game.state.player_data["p1"]["last_score"] = 130
        game.state.player_data["p2"]["current_answer"] = 0
        game.state.player_data["p2"]["last_score"] = 0
        game.state.scores["p1"] = 130
        game.state.scores["p2"] = 0

        state = await game.get_state_for_display()

        assert state["phase"] == "round_end"
        assert "correct_answer" in state["current_question"]  # Shown
        assert "player_results" in state
        assert len(state["player_results"]) == 2

    @pytest.mark.asyncio
    async def test_get_state_for_display_finished(self):
        """Test display state when finished."""
        game = self._create_game_with_state()
        game.state.phase = GamePhase.FINISHED
        game.state.scores = {"p1": 450, "p2": 300}
        game.state.player_data["p1"]["correct_count"] = 4
        game.state.player_data["p2"]["correct_count"] = 2
        game.state.winner_id = "p1"

        state = await game.get_state_for_display()

        assert state["phase"] == "finished"
        assert state["winner_id"] == "p1"
        assert state["final_scores"] == {"p1": 450, "p2": 300}
        assert "leaderboard" in state
        assert state["leaderboard"][0]["player_id"] == "p1"  # Sorted by score


class TestTriviaResults:
    """Test game results."""

    @pytest.mark.asyncio
    async def test_get_results_structure(self):
        """Test results structure."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])
        game.state.phase = GamePhase.FINISHED
        game.state.scores = {"p1": 450, "p2": 300}
        game.state.player_data["p1"] = {"correct_count": 4}
        game.state.player_data["p2"] = {"correct_count": 2}
        game.state.winner_id = "p1"

        results = await game.get_results()

        assert "game_type" in results
        assert results["game_type"] == "trivia"
        assert "winner_id" in results
        assert results["winner_id"] == "p1"
        assert "scores" in results
        assert "player_stats" in results
        assert "total_questions" in results

    @pytest.mark.asyncio
    async def test_get_results_player_stats(self):
        """Test results include player statistics."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])
        game.state.phase = GamePhase.FINISHED
        game.state.scores = {"p1": 500, "p2": 250}
        game.state.player_data["p1"] = {"correct_count": 5}
        game.state.player_data["p2"] = {"correct_count": 2}

        results = await game.get_results()

        assert "p1" in results["player_stats"]
        assert "p2" in results["player_stats"]
        assert results["player_stats"]["p1"]["score"] == 500
        assert results["player_stats"]["p1"]["correct_count"] == 5
        assert results["player_stats"]["p1"]["accuracy"] == 100.0
        assert results["player_stats"]["p2"]["accuracy"] == 40.0


class TestTriviaHelpers:
    """Test helper methods."""

    def test_is_finished_false(self):
        """Test is_finished when game not finished."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])
        assert not game.is_finished()

    def test_is_finished_true(self):
        """Test is_finished when game finished."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])
        game.state.phase = GamePhase.FINISHED
        assert game.is_finished()

    def test_calculate_winner_with_clear_winner(self):
        """Test winner calculation with clear winner."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2", "p3"])
        game.state.scores = {"p1": 500, "p2": 300, "p3": 100}

        winner = game._calculate_winner()
        assert winner == "p1"

    def test_calculate_winner_with_tie(self):
        """Test winner calculation with tie."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])
        game.state.scores = {"p1": 500, "p2": 500}

        winner = game._calculate_winner()
        assert winner is None  # Tie

    def test_calculate_winner_no_scores(self):
        """Test winner calculation with no scores."""
        game = Trivia(room_code="TEST", player_ids=["p1"])
        game.state.scores = {}

        winner = game._calculate_winner()
        assert winner is None

    def test_get_current_scores(self):
        """Test getting current scores."""
        game = Trivia(room_code="TEST", player_ids=["p1", "p2"])
        game.state.scores = {"p1": 250, "p2": 150}

        scores = game.get_current_scores()

        assert scores == {"p1": 250, "p2": 150}
        # Ensure it returns a copy
        scores["p1"] = 999
        assert game.state.scores["p1"] == 250
