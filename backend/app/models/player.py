"""Player database model."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.score import Score


class Player(Base):
    """
    Player model representing a participant in a room.

    Players are tied to a specific room and session.
    """

    __tablename__ = "players"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to room
    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Player details
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Session management
    session_id: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )

    # Player status
    is_host: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    connected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
    )

    last_seen: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
    )

    # Connection metadata (for security/debugging)
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
    )

    # Relationships
    room: Mapped["Room"] = relationship(
        "Room",
        back_populates="players",
    )

    scores: Mapped[list["Score"]] = relationship(
        "Score",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 50",
            name="valid_name_length",
        ),
        CheckConstraint(
            "session_id ~ '^[a-f0-9]{64}$'",
            name="valid_session_id_format",
        ),
        Index("idx_players_room_id", "room_id"),
        Index("idx_players_session_id", "session_id"),
        Index(
            "idx_players_connected",
            "connected",
            postgresql_where="connected = TRUE",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Player(id={self.id}, name='{self.name}', room_id={self.room_id})>"
