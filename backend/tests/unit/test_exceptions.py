"""Unit tests for custom exceptions."""

import pytest

from app.core.exceptions import (
    ForbiddenError,
    GameStateError,
    GameTimeException,
    PlayerNotFoundError,
    RateLimitExceededError,
    RoomFullError,
    RoomNotFoundError,
    UnauthorizedError,
    ValidationError,
    WebSocketError,
)


class TestGameTimeException:
    """Tests for base GameTimeException."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = GameTimeException("Test error")
        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.details == {}
        assert str(exc) == "Test error"

    def test_exception_with_status_code(self):
        """Test exception with custom status code."""
        exc = GameTimeException("Test error", status_code=404)
        assert exc.message == "Test error"
        assert exc.status_code == 404
        assert exc.details == {}

    def test_exception_with_details(self):
        """Test exception with details."""
        details = {"key": "value", "count": 42}
        exc = GameTimeException("Test error", details=details)
        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.details == details

    def test_exception_with_all_params(self):
        """Test exception with all parameters."""
        details = {"reason": "test"}
        exc = GameTimeException("Test error", status_code=400, details=details)
        assert exc.message == "Test error"
        assert exc.status_code == 400
        assert exc.details == details


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error_basic(self):
        """Test basic validation error."""
        exc = ValidationError("Invalid input")
        assert exc.message == "Invalid input"
        assert exc.status_code == 400
        assert exc.details == {}

    def test_validation_error_with_details(self):
        """Test validation error with details."""
        details = {"field": "email", "error": "invalid format"}
        exc = ValidationError("Validation failed", details=details)
        assert exc.message == "Validation failed"
        assert exc.status_code == 400
        assert exc.details == details


class TestRoomNotFoundError:
    """Tests for RoomNotFoundError."""

    def test_room_not_found_error(self):
        """Test room not found error."""
        exc = RoomNotFoundError("ABCD")
        assert exc.message == "Room 'ABCD' not found"
        assert exc.status_code == 404
        assert exc.details == {"room_code": "ABCD"}

    def test_room_not_found_error_different_code(self):
        """Test room not found with different room code."""
        exc = RoomNotFoundError("XYZ123")
        assert exc.message == "Room 'XYZ123' not found"
        assert exc.status_code == 404
        assert exc.details == {"room_code": "XYZ123"}


class TestRoomFullError:
    """Tests for RoomFullError."""

    def test_room_full_error(self):
        """Test room full error."""
        exc = RoomFullError("ABCD", 12)
        assert exc.message == "Room 'ABCD' is full (max 12 players)"
        assert exc.status_code == 409
        assert exc.details == {"room_code": "ABCD", "max_players": 12}

    def test_room_full_error_different_values(self):
        """Test room full with different values."""
        exc = RoomFullError("TEST", 8)
        assert exc.message == "Room 'TEST' is full (max 8 players)"
        assert exc.status_code == 409
        assert exc.details == {"room_code": "TEST", "max_players": 8}


class TestPlayerNotFoundError:
    """Tests for PlayerNotFoundError."""

    def test_player_not_found_error(self):
        """Test player not found error."""
        exc = PlayerNotFoundError(42)
        assert exc.message == "Player 42 not found"
        assert exc.status_code == 404
        assert exc.details == {"player_id": 42}

    def test_player_not_found_error_different_id(self):
        """Test player not found with different ID."""
        exc = PlayerNotFoundError(123)
        assert exc.message == "Player 123 not found"
        assert exc.status_code == 404
        assert exc.details == {"player_id": 123}


class TestUnauthorizedError:
    """Tests for UnauthorizedError."""

    def test_unauthorized_error_default(self):
        """Test unauthorized error with default message."""
        exc = UnauthorizedError()
        assert exc.message == "Unauthorized"
        assert exc.status_code == 401
        assert exc.details == {}

    def test_unauthorized_error_custom_message(self):
        """Test unauthorized error with custom message."""
        exc = UnauthorizedError("Invalid session")
        assert exc.message == "Invalid session"
        assert exc.status_code == 401
        assert exc.details == {}


class TestForbiddenError:
    """Tests for ForbiddenError."""

    def test_forbidden_error_default(self):
        """Test forbidden error with default message."""
        exc = ForbiddenError()
        assert exc.message == "Forbidden"
        assert exc.status_code == 403
        assert exc.details == {}

    def test_forbidden_error_custom_message(self):
        """Test forbidden error with custom message."""
        exc = ForbiddenError("Not the host")
        assert exc.message == "Not the host"
        assert exc.status_code == 403
        assert exc.details == {}


class TestRateLimitExceededError:
    """Tests for RateLimitExceededError."""

    def test_rate_limit_exceeded_error(self):
        """Test rate limit exceeded error."""
        exc = RateLimitExceededError(60)
        assert exc.message == "Rate limit exceeded"
        assert exc.status_code == 429
        assert exc.details == {"retry_after": 60}

    def test_rate_limit_exceeded_error_different_time(self):
        """Test rate limit exceeded with different retry time."""
        exc = RateLimitExceededError(120)
        assert exc.message == "Rate limit exceeded"
        assert exc.status_code == 429
        assert exc.details == {"retry_after": 120}


class TestGameStateError:
    """Tests for GameStateError."""

    def test_game_state_error(self):
        """Test game state error."""
        exc = GameStateError("Cannot start game", "lobby")
        assert exc.message == "Cannot start game"
        assert exc.status_code == 409
        assert exc.details == {"current_state": "lobby"}

    def test_game_state_error_different_state(self):
        """Test game state error with different state."""
        exc = GameStateError("Game already finished", "finished")
        assert exc.message == "Game already finished"
        assert exc.status_code == 409
        assert exc.details == {"current_state": "finished"}


class TestWebSocketError:
    """Tests for WebSocketError."""

    def test_websocket_error(self):
        """Test WebSocket error."""
        exc = WebSocketError("Connection failed")
        assert exc.message == "Connection failed"
        assert exc.status_code == 400
        assert exc.details == {}

    def test_websocket_error_different_message(self):
        """Test WebSocket error with different message."""
        exc = WebSocketError("Invalid message format")
        assert exc.message == "Invalid message format"
        assert exc.status_code == 400
        assert exc.details == {}


class TestExceptionInheritance:
    """Tests for exception inheritance."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from GameTimeException."""
        exceptions = [
            ValidationError("test"),
            RoomNotFoundError("TEST"),
            RoomFullError("TEST", 12),
            PlayerNotFoundError(1),
            UnauthorizedError(),
            ForbiddenError(),
            RateLimitExceededError(60),
            GameStateError("test", "lobby"),
            WebSocketError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, GameTimeException)
            assert isinstance(exc, Exception)

    def test_exception_can_be_caught_as_base(self):
        """Test that exceptions can be caught as GameTimeException."""
        with pytest.raises(GameTimeException) as exc_info:
            raise ValidationError("test error")

        assert exc_info.value.message == "test error"
        assert exc_info.value.status_code == 400
