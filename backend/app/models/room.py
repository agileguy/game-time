"""Room database model."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Room(Base, TimestampMixin):
    """
    Room model for game lobbies.

    A room is where players gather before and during games.
    """

    __tablename__ = "rooms"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Room code (unique identifier for players to join)
    code: Mapped[str] = mapped_column(
        String(6),
        unique=True,
        nullable=False,
        index=True,
    )

    # Room status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="lobby",
        index=True,
    )

    # Current game being played
    current_game: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Host player ID
    host_player_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Player limits
    max_players: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=12,
    )

    # Room settings (flexible JSON storage)
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Public/private flag
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Activity tracking
    last_activity: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    # Relationships
    players: Mapped[list["Player"]] = relationship(  # noqa: F821
        "Player",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    game_sessions: Mapped[list["GameSession"]] = relationship(  # noqa: F821
        "GameSession",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('lobby', 'playing', 'finished')",
            name="valid_status",
        ),
        CheckConstraint(
            "current_game IN ('horse_race', 'trivia', 'memory') OR current_game IS NULL",
            name="valid_game",
        ),
        CheckConstraint(
            "max_players >= 2 AND max_players <= 12",
            name="valid_max_players",
        ),
        CheckConstraint(
            "code ~ '^[A-Z0-9]{4,6}$'",
            name="valid_code_format",
        ),
        Index("idx_rooms_code", "code"),
        Index("idx_rooms_status", "status"),
        Index("idx_rooms_last_activity", "last_activity"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Room(id={self.id}, code='{self.code}', status='{self.status}')>"
