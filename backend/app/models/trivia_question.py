"""Trivia question database model."""

from sqlalchemy import CheckConstraint, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TriviaQuestion(Base):
    """
    Trivia question model for storing quiz questions.

    Each question has 4 multiple choice options with one correct answer.
    """

    __tablename__ = "trivia_questions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Question text
    question: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Answer options (4 choices stored as JSON array)
    options: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
    )

    # Correct answer index (0-3)
    correct_answer: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Category for filtering/balancing
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Difficulty level
    difficulty: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "correct_answer >= 0 AND correct_answer <= 3",
            name="valid_correct_answer",
        ),
        CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="valid_difficulty",
        ),
        CheckConstraint(
            "jsonb_array_length(options) = 4",
            name="four_options_required",
        ),
        Index("idx_trivia_questions_category", "category"),
        Index("idx_trivia_questions_difficulty", "difficulty"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TriviaQuestion(id={self.id}, category='{self.category}', difficulty='{self.difficulty}')>"

    def to_dict(self) -> dict:
        """
        Convert question to dictionary for API responses.

        Returns:
            dict: Question data including ID, question, options, category, and difficulty
                 (excludes correct_answer for security)
        """
        return {
            "id": self.id,
            "question": self.question,
            "options": self.options,
            "category": self.category,
            "difficulty": self.difficulty,
        }

    def to_dict_with_answer(self) -> dict:
        """
        Convert question to dictionary including the correct answer.

        Use this only for game state storage or admin purposes.

        Returns:
            dict: Complete question data including correct_answer
        """
        return {
            "id": self.id,
            "question": self.question,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "category": self.category,
            "difficulty": self.difficulty,
        }
