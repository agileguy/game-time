"""Game session database model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.player import Player
    from app.models.room import Room
    from app.models.score import Score


class GameSession(Base):
    """
    Game session model representing a single game played in a room.

    Tracks the game type, state, and results.
    """

    __tablename__ = "game_sessions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to room
    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Game type
    game_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Game state (flexible JSON storage for game-specific data)
    state: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        index=True,
    )

    # Winner (nullable if game not finished or no clear winner)
    winner_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("players.id"),
        nullable=True,
    )

    # Relationships
    room: Mapped["Room"] = relationship(
        "Room",
        back_populates="game_sessions",
    )

    winner: Mapped[Optional["Player"]] = relationship(
        "Player",
        foreign_keys=[winner_id],
    )

    scores: Mapped[list["Score"]] = relationship(
        "Score",
        back_populates="game_session",
        cascade="all, delete-orphan",
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "game_type IN ('horse_race', 'trivia', 'memory')",
            name="valid_game_type",
        ),
        CheckConstraint(
            "finished_at IS NULL OR finished_at > started_at",
            name="valid_finish_time",
        ),
        Index("idx_game_sessions_room_id", "room_id"),
        Index("idx_game_sessions_game_type", "game_type"),
        Index("idx_game_sessions_finished_at", "finished_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<GameSession(id={self.id}, game_type='{self.game_type}', room_id={self.room_id})>"

    @property
    def is_finished(self) -> bool:
        """Check if game session is finished."""
        return self.finished_at is not None

    @property
    def duration(self) -> float | None:
        """
        Get game duration in seconds.

        Returns:
            Optional[float]: Duration in seconds, or None if not finished
        """
        if not self.is_finished:
            return None

        return (self.finished_at - self.started_at).total_seconds()
