"""Trivia game implementation."""

import asyncio
import random
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from app.core.logging import get_logger
from app.database import AsyncSessionLocal
from app.games.base import BaseGame, GamePhase
from app.models.trivia_question import TriviaQuestion

logger = get_logger()


class Trivia(BaseGame):
    """
    Trivia quiz game.

    Players answer multiple-choice questions for points with speed bonus.
    """

    # Game constants
    NUM_QUESTIONS = 5
    ANSWER_TIME = 10  # seconds
    BASE_POINTS = 100
    MAX_SPEED_BONUS = 50
    RESULTS_DISPLAY_TIME = 5  # seconds to show results before next question

    def __init__(self, room_code: str, player_ids: list[str]):
        """Initialize trivia game."""
        super().__init__(room_code, player_ids)
        self._question_task: asyncio.Task | None = None

    @classmethod
    def game_type(cls) -> str:
        """Return game type identifier."""
        return "trivia"

    @classmethod
    def display_name(cls) -> str:
        """Return human-readable name."""
        return "Trivia Challenge"

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
        Start the game with first question.

        Returns:
            dict: Initial game state
        """
        self.state.phase = GamePhase.SETUP
        self.state.started_at = datetime.now(timezone.utc)
        self.state.total_rounds = self.NUM_QUESTIONS
        self.state.current_round = 0

        # Load 5 random questions from database
        questions = await self._load_random_questions(self.NUM_QUESTIONS)

        if len(questions) < self.NUM_QUESTIONS:
            logger.error(
                "Not enough trivia questions in database",
                room_code=self.room_code,
                available=len(questions),
                required=self.NUM_QUESTIONS,
            )
            raise ValueError(
                f"Not enough questions in database. Need {self.NUM_QUESTIONS}, found {len(questions)}"
            )

        # Store all questions in round_data
        self.state.round_data = {
            "questions": [q.to_dict_with_answer() for q in questions],
            "current_question_index": 0,
            "question_start_time": None,
            "answer_deadline": None,
        }

        # Initialize player data
        for player_id in self.player_ids:
            self.state.player_data[player_id] = {
                "answers": [],  # List of answers for each question
                "answer_times": [],  # List of answer timestamps
                "correct_count": 0,
            }

        # Initialize scores to 0
        for player_id in self.player_ids:
            self.state.scores[player_id] = 0

        logger.info(
            "Started trivia game",
            room_code=self.room_code,
            num_questions=len(questions),
        )

        # Start first question
        await self._start_question()

        return await self.get_state_for_display()

    async def _load_random_questions(self, count: int) -> list[TriviaQuestion]:
        """
        Load random questions from database.

        Args:
            count: Number of questions to load

        Returns:
            list[TriviaQuestion]: Random questions
        """
        async with AsyncSessionLocal() as db:
            # Get random questions using SQL random function
            result = await db.execute(
                select(TriviaQuestion).order_by(func.random()).limit(count)
            )
            questions = result.scalars().all()
            return list(questions)

    async def _start_question(self) -> None:
        """Start the current question timer."""
        current_time = datetime.now(timezone.utc)
        self.state.round_data["question_start_time"] = current_time.isoformat()
        self.state.round_data["answer_deadline"] = (
            current_time.timestamp() + self.ANSWER_TIME
        )

        # Reset player answers for this question
        for player_id in self.player_ids:
            # Don't reset the entire player_data, just set current answer to None
            if "current_answer" not in self.state.player_data[player_id]:
                self.state.player_data[player_id]["current_answer"] = None
                self.state.player_data[player_id]["answered_at"] = None
            else:
                self.state.player_data[player_id]["current_answer"] = None
                self.state.player_data[player_id]["answered_at"] = None

        logger.info(
            "Started question",
            room_code=self.room_code,
            question_index=self.state.round_data["current_question_index"],
            answer_time=self.ANSWER_TIME,
        )

        # Cancel existing task if any
        if self._question_task and not self._question_task.done():
            self._question_task.cancel()

        # Schedule auto-advance after answer time
        self._question_task = asyncio.create_task(self._auto_advance_question())

    async def _auto_advance_question(self) -> None:
        """Automatically advance to results after answer time expires."""
        try:
            await asyncio.sleep(self.ANSWER_TIME)

            # Only advance if still in SETUP phase
            if self.state.phase == GamePhase.SETUP:
                logger.info(
                    "Answer time expired, showing results",
                    room_code=self.room_code,
                    question_index=self.state.round_data["current_question_index"],
                )
                await self._show_question_results()

                # Wait for results display time
                await asyncio.sleep(self.RESULTS_DISPLAY_TIME)

                # Advance to next question or finish
                await self._advance_to_next_question()

        except asyncio.CancelledError:
            logger.debug(
                "Question timer cancelled",
                room_code=self.room_code,
            )

    async def _show_question_results(self) -> None:
        """Show results for current question."""
        self.state.phase = GamePhase.ROUND_END

        # Calculate scores for this question
        current_question_index = self.state.round_data["current_question_index"]
        current_question = self.state.round_data["questions"][current_question_index]
        correct_answer = current_question["correct_answer"]
        question_start_time = datetime.fromisoformat(
            self.state.round_data["question_start_time"]
        )

        for player_id in self.player_ids:
            player_data = self.state.player_data[player_id]
            player_answer = player_data.get("current_answer")

            if player_answer is not None and player_answer == correct_answer:
                # Calculate score with speed bonus
                answered_at = player_data.get("answered_at")
                if answered_at:
                    answer_time = datetime.fromisoformat(answered_at)
                    time_taken = (answer_time - question_start_time).total_seconds()
                    score = self._calculate_score(time_taken)
                else:
                    # No timestamp, give base points only
                    score = self.BASE_POINTS

                # Add to total score
                self.state.scores[player_id] += score
                player_data["correct_count"] += 1
                player_data["last_score"] = score

                logger.info(
                    "Player answered correctly",
                    room_code=self.room_code,
                    player_id=player_id,
                    question_index=current_question_index,
                    score=score,
                )
            else:
                # Wrong answer or no answer
                player_data["last_score"] = 0

            # Record the answer in history
            player_data["answers"].append(player_answer)
            if player_data.get("answered_at"):
                player_data["answer_times"].append(player_data["answered_at"])
            else:
                player_data["answer_times"].append(None)

        logger.info(
            "Showing question results",
            room_code=self.room_code,
            question_index=current_question_index,
            correct_answer=correct_answer,
        )

    async def _advance_to_next_question(self) -> None:
        """Advance to next question or finish game."""
        current_index = self.state.round_data["current_question_index"]

        if current_index + 1 < self.NUM_QUESTIONS:
            # Move to next question
            self.state.round_data["current_question_index"] += 1
            self.state.current_round += 1
            self.state.phase = GamePhase.SETUP

            logger.info(
                "Advancing to next question",
                room_code=self.room_code,
                next_question_index=self.state.round_data["current_question_index"],
            )

            # Start next question
            await self._start_question()
        else:
            # Game finished
            await self._finish_game()

    async def _finish_game(self) -> None:
        """Finish the game and calculate final results."""
        self.state.phase = GamePhase.FINISHED
        self.state.finished_at = datetime.now(timezone.utc)
        self.state.winner_id = self._calculate_winner()

        logger.info(
            "Trivia game finished",
            room_code=self.room_code,
            winner_id=self.state.winner_id,
            final_scores=self.state.scores,
        )

    def _calculate_score(self, time_taken_seconds: float) -> int:
        """
        Calculate score with speed bonus.

        Args:
            time_taken_seconds: Time taken to answer in seconds

        Returns:
            int: Total score (base + speed bonus)
        """
        if time_taken_seconds <= 0:
            # Instant answer gets full bonus
            return self.BASE_POINTS + self.MAX_SPEED_BONUS

        # Linear decay: MAX_SPEED_BONUS points at 0s, 0 points at ANSWER_TIME
        time_ratio = min(time_taken_seconds / self.ANSWER_TIME, 1.0)
        speed_bonus = self.MAX_SPEED_BONUS * (1 - time_ratio)

        return self.BASE_POINTS + int(speed_bonus)

    async def handle_player_action(
        self, player_id: str, action: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle player actions (answer submission).

        Args:
            player_id: Player session ID
            action: Action type
            data: Action data

        Returns:
            dict: Response data
        """
        if action == "submit_answer":
            return await self._handle_submit_answer(player_id, data)
        else:
            return {"error": f"Unknown action: {action}"}

    async def _handle_submit_answer(
        self, player_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle a player submitting an answer."""
        if self.state.phase != GamePhase.SETUP:
            return {"error": "Not in question phase"}

        answer = data.get("answer")
        if answer is None or not isinstance(answer, int) or answer < 0 or answer > 3:
            return {"error": "Invalid answer. Must be 0-3"}

        # Record the answer
        self.state.player_data[player_id]["current_answer"] = answer
        self.state.player_data[player_id]["answered_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        logger.info(
            "Player submitted answer",
            room_code=self.room_code,
            player_id=player_id,
            answer=answer,
            question_index=self.state.round_data["current_question_index"],
        )

        return {
            "success": True,
            "answer": answer,
        }

    async def get_state_for_player(self, player_id: str) -> dict[str, Any]:
        """
        Get game state for a specific player.

        Args:
            player_id: Player session ID

        Returns:
            dict: Player-specific state
        """
        player_data = self.state.player_data.get(player_id, {})
        current_question_index = self.state.round_data.get("current_question_index", 0)

        # Get current question (without correct answer in SETUP phase)
        questions = self.state.round_data.get("questions", [])
        current_question = None
        if current_question_index < len(questions):
            q = questions[current_question_index]
            if self.state.phase == GamePhase.SETUP:
                # Hide correct answer during question phase
                current_question = {
                    "id": q["id"],
                    "question": q["question"],
                    "options": q["options"],
                    "category": q["category"],
                    "difficulty": q["difficulty"],
                }
            else:
                # Show correct answer during results phase
                current_question = q

        state = {
            "phase": self.state.phase.value,
            "current_question_index": current_question_index,
            "total_questions": self.NUM_QUESTIONS,
            "current_question": current_question,
            "your_answer": player_data.get("current_answer"),
            "your_score": self.state.scores.get(player_id, 0),
            "answer_time": self.ANSWER_TIME,
            "question_start_time": self.state.round_data.get("question_start_time"),
        }

        if self.state.phase == GamePhase.ROUND_END:
            state["last_score"] = player_data.get("last_score", 0)
            state["correct_count"] = player_data.get("correct_count", 0)

        if self.state.phase == GamePhase.FINISHED:
            state["winner_id"] = self.state.winner_id
            state["all_scores"] = self.state.scores
            state["correct_count"] = player_data.get("correct_count", 0)

        return state

    async def get_state_for_display(self) -> dict[str, Any]:
        """
        Get game state for display screen.

        Returns:
            dict: Display state
        """
        current_question_index = self.state.round_data.get("current_question_index", 0)
        questions = self.state.round_data.get("questions", [])

        # Get current question
        current_question = None
        if current_question_index < len(questions):
            q = questions[current_question_index]
            if self.state.phase == GamePhase.SETUP:
                # Hide correct answer during question phase
                current_question = {
                    "id": q["id"],
                    "question": q["question"],
                    "options": q["options"],
                    "category": q["category"],
                    "difficulty": q["difficulty"],
                }
            else:
                # Show correct answer during results phase
                current_question = q

        # Calculate answer counts for each option
        answer_counts = [0, 0, 0, 0]
        players_answered = []
        for player_id, player_data in self.state.player_data.items():
            answer = player_data.get("current_answer")
            if answer is not None:
                answer_counts[answer] += 1
                players_answered.append(player_id)

        state = {
            "phase": self.state.phase.value,
            "current_question_index": current_question_index,
            "total_questions": self.NUM_QUESTIONS,
            "current_question": current_question,
            "answer_counts": answer_counts,
            "players_answered": players_answered,
            "total_players": len(self.player_ids),
            "answer_time": self.ANSWER_TIME,
            "question_start_time": self.state.round_data.get("question_start_time"),
        }

        if self.state.phase == GamePhase.ROUND_END:
            # Show player results
            player_results = []
            for player_id in self.player_ids:
                player_data = self.state.player_data[player_id]
                player_results.append(
                    {
                        "player_id": player_id,
                        "answer": player_data.get("current_answer"),
                        "score": player_data.get("last_score", 0),
                        "total_score": self.state.scores.get(player_id, 0),
                    }
                )
            state["player_results"] = player_results

        if self.state.phase == GamePhase.FINISHED:
            state["winner_id"] = self.state.winner_id
            state["final_scores"] = self.state.scores
            # Add leaderboard sorted by score
            leaderboard = sorted(
                [
                    {
                        "player_id": player_id,
                        "score": score,
                        "correct_count": self.state.player_data[player_id].get(
                            "correct_count", 0
                        ),
                    }
                    for player_id, score in self.state.scores.items()
                ],
                key=lambda x: x["score"],
                reverse=True,
            )
            state["leaderboard"] = leaderboard

        return state

    async def get_results(self) -> dict[str, Any]:
        """
        Get final game results.

        Returns:
            dict: Results with scores and winner
        """
        # Calculate accuracy for each player
        player_stats = {}
        for player_id in self.player_ids:
            player_data = self.state.player_data[player_id]
            correct_count = player_data.get("correct_count", 0)
            player_stats[player_id] = {
                "score": self.state.scores.get(player_id, 0),
                "correct_count": correct_count,
                "accuracy": (correct_count / self.NUM_QUESTIONS * 100)
                if self.NUM_QUESTIONS > 0
                else 0,
            }

        results = {
            "game_type": self.game_type(),
            "winner_id": self.state.winner_id,
            "scores": self.state.scores,
            "player_stats": player_stats,
            "total_questions": self.NUM_QUESTIONS,
        }

        return results
