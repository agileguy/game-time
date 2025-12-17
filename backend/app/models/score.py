"""Score database model."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.game_session import GameSession
    from app.models.player import Player


class Score(Base):
    """
    Score model representing a player's performance in a game session.

    Tracks total score, per-round scores, and bonus points.
    """

    __tablename__ = "scores"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    game_session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Score data
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Per-round scores (flexible JSON array for different game types)
    round_scores: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )

    # Bonus points (for streaks, speed bonuses, etc.)
    bonus_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationships
    game_session: Mapped["GameSession"] = relationship(
        "GameSession",
        back_populates="scores",
    )

    player: Mapped["Player"] = relationship(
        "Player",
        back_populates="scores",
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "score >= 0",
            name="valid_score",
        ),
        CheckConstraint(
            "bonus_points >= 0",
            name="valid_bonus_points",
        ),
        UniqueConstraint(
            "game_session_id",
            "player_id",
            name="unique_player_per_session",
        ),
        Index("idx_scores_game_session", "game_session_id"),
        Index("idx_scores_player", "player_id"),
        Index("idx_scores_score", "score", postgresql_using="btree"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Score(id={self.id}, player_id={self.player_id}, "
            f"game_session_id={self.game_session_id}, score={self.score})>"
        )

    @property
    def total_score(self) -> int:
        """
        Calculate total score including bonus points.

        Returns:
            int: Total score
        """
        return self.score + self.bonus_points
