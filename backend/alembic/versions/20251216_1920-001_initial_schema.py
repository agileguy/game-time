"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-12-16 19:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create rooms table
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="lobby"),
        sa.Column("current_game", sa.String(length=50), nullable=True),
        sa.Column("host_player_id", sa.Integer(), nullable=True),
        sa.Column("max_players", sa.Integer(), nullable=False, server_default="12"),
        sa.Column(
            "settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "last_activity",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint("status IN ('lobby', 'playing', 'finished')", name="valid_status"),
        sa.CheckConstraint(
            "current_game IN ('horse_race', 'trivia', 'memory') OR current_game IS NULL",
            name="valid_game",
        ),
        sa.CheckConstraint("max_players >= 2 AND max_players <= 12", name="valid_max_players"),
        sa.CheckConstraint("code ~ '^[A-Z0-9]{4,6}$'", name="valid_code_format"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("idx_rooms_code", "rooms", ["code"])
    op.create_index("idx_rooms_status", "rooms", ["status"])
    op.create_index("idx_rooms_last_activity", "rooms", ["last_activity"])

    # Create players table
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("is_host", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("connected", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "last_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.CheckConstraint(
            "LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 50",
            name="valid_name_length",
        ),
        sa.CheckConstraint("session_id ~ '^[a-f0-9]{64}$'", name="valid_session_id_format"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index("idx_players_room_id", "players", ["room_id"])
    op.create_index("idx_players_session_id", "players", ["session_id"])
    op.create_index(
        "idx_players_connected",
        "players",
        ["connected"],
        postgresql_where=sa.text("connected = TRUE"),
    )

    # Create game_sessions table
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("game_type", sa.String(length=50), nullable=False),
        sa.Column(
            "state", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("winner_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "game_type IN ('horse_race', 'trivia', 'memory')",
            name="valid_game_type",
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR finished_at > started_at",
            name="valid_finish_time",
        ),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["winner_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_game_sessions_room_id", "game_sessions", ["room_id"])
    op.create_index("idx_game_sessions_game_type", "game_sessions", ["game_type"])
    op.create_index("idx_game_sessions_finished_at", "game_sessions", ["finished_at"])

    # Create scores table
    op.create_table(
        "scores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("game_session_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "round_scores",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("bonus_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint("score >= 0", name="valid_score"),
        sa.CheckConstraint("bonus_points >= 0", name="valid_bonus_points"),
        sa.ForeignKeyConstraint(["game_session_id"], ["game_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game_session_id", "player_id", name="unique_player_per_session"),
    )
    op.create_index("idx_scores_game_session", "scores", ["game_session_id"])
    op.create_index("idx_scores_player", "scores", ["player_id"])
    op.create_index("idx_scores_score", "scores", ["score"], postgresql_using="btree")


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table("scores")
    op.drop_table("game_sessions")
    op.drop_table("players")
    op.drop_table("rooms")
