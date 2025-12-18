"""Room-related Pydantic schemas."""

from pydantic import BaseModel, Field, field_validator


class CreateRoomRequest(BaseModel):
    """Request to create a new room."""

    host_name: str = Field(..., min_length=1, max_length=50, description="Host player name")
    max_players: int = Field(default=12, ge=2, le=12, description="Maximum number of players")
    is_public: bool = Field(default=True, description="Whether room is public")

    @field_validator("host_name")
    @classmethod
    def validate_host_name(cls, v: str) -> str:
        """Validate and sanitize host name."""
        v = v.strip()
        if not v:
            raise ValueError("Host name cannot be empty")
        return v


class CreateRoomResponse(BaseModel):
    """Response after creating a room."""

    room_code: str = Field(..., description="Room code for joining")
    room_id: int = Field(..., description="Room ID")
    session_id: str = Field(..., description="Host session ID")
    player_id: int = Field(..., description="Host player ID")
    player_name: str = Field(..., description="Host player name")
    is_host: bool = Field(..., description="Whether player is host")


class JoinRoomRequest(BaseModel):
    """Request to join a room."""

    player_name: str = Field(..., min_length=1, max_length=50, description="Player name")

    @field_validator("player_name")
    @classmethod
    def validate_player_name(cls, v: str) -> str:
        """Validate and sanitize player name."""
        v = v.strip()
        if not v:
            raise ValueError("Player name cannot be empty")
        return v


class JoinRoomResponse(BaseModel):
    """Response after joining a room."""

    room_code: str = Field(..., description="Room code")
    room_id: int = Field(..., description="Room ID")
    session_id: str = Field(..., description="Player session ID")
    player_id: int = Field(..., description="Player ID")
    player_name: str = Field(..., description="Player name")
    is_host: bool = Field(..., description="Whether player is host")


class RoomDetailResponse(BaseModel):
    """Room details response."""

    room_code: str = Field(..., description="Room code")
    room_id: int = Field(..., description="Room ID")
    status: str = Field(..., description="Room status (lobby, playing, finished)")
    max_players: int = Field(..., description="Maximum number of players")
    active_players: int = Field(..., description="Number of active players")
    is_public: bool = Field(..., description="Whether room is public")
    current_game: str | None = Field(None, description="Current game type")


class PlayerInfo(BaseModel):
    """Player information."""

    player_id: int = Field(..., description="Player ID", serialization_alias="id")
    session_id: str = Field(..., description="Player session ID")
    name: str = Field(..., description="Player name")
    is_host: bool = Field(..., description="Whether player is host")
    connected: bool = Field(..., description="Whether player is connected")


class RoomState(BaseModel):
    """Full room state for WebSocket."""

    room_code: str
    room_id: int
    status: str
    max_players: int
    current_game: str | None
    host_player_id: int | None
    players: list[PlayerInfo]
