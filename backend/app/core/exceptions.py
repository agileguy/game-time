"""Custom exceptions for the application."""

from typing import Any


class GameTimeException(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize exception.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(GameTimeException):
    """Validation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize validation error."""
        super().__init__(message, status_code=400, details=details)


class RoomNotFoundError(GameTimeException):
    """Room not found error."""

    def __init__(self, room_code: str) -> None:
        """Initialize room not found error."""
        super().__init__(
            message=f"Room '{room_code}' not found",
            status_code=404,
            details={"room_code": room_code},
        )


class RoomFullError(GameTimeException):
    """Room is full error."""

    def __init__(self, room_code: str, max_players: int) -> None:
        """Initialize room full error."""
        super().__init__(
            message=f"Room '{room_code}' is full (max {max_players} players)",
            status_code=409,
            details={"room_code": room_code, "max_players": max_players},
        )


class PlayerNotFoundError(GameTimeException):
    """Player not found error."""

    def __init__(self, player_id: int) -> None:
        """Initialize player not found error."""
        super().__init__(
            message=f"Player {player_id} not found",
            status_code=404,
            details={"player_id": player_id},
        )


class UnauthorizedError(GameTimeException):
    """Unauthorized access error."""

    def __init__(self, message: str = "Unauthorized") -> None:
        """Initialize unauthorized error."""
        super().__init__(message, status_code=401)


class ForbiddenError(GameTimeException):
    """Forbidden access error."""

    def __init__(self, message: str = "Forbidden") -> None:
        """Initialize forbidden error."""
        super().__init__(message, status_code=403)


class RateLimitExceededError(GameTimeException):
    """Rate limit exceeded error."""

    def __init__(self, retry_after: int) -> None:
        """
        Initialize rate limit error.

        Args:
            retry_after: Seconds until rate limit resets
        """
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            details={"retry_after": retry_after},
        )


class GameStateError(GameTimeException):
    """Invalid game state error."""

    def __init__(self, message: str, current_state: str) -> None:
        """
        Initialize game state error.

        Args:
            message: Error message
            current_state: Current game state
        """
        super().__init__(
            message=message,
            status_code=409,
            details={"current_state": current_state},
        )


class WebSocketError(GameTimeException):
    """WebSocket connection error."""

    def __init__(self, message: str) -> None:
        """Initialize WebSocket error."""
        super().__init__(message, status_code=400)
