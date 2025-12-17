"""Unit tests for application configuration."""

import pytest
from pydantic import ValidationError

from app.config import Settings


class TestSettings:
    """Tests for Settings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()

        assert settings.app_name == "Game Time"
        assert settings.debug is False
        assert settings.database_pool_size == 20
        assert settings.redis_max_connections == 50

    def test_room_code_length_validation_valid(self):
        """Test room code length validation accepts valid values."""
        settings = Settings(room_code_length=4)
        assert settings.room_code_length == 4

        settings = Settings(room_code_length=6)
        assert settings.room_code_length == 6

    def test_room_code_length_validation_invalid(self):
        """Test room code length validation rejects invalid values."""
        with pytest.raises(ValidationError):
            Settings(room_code_length=3)  # Too short

        with pytest.raises(ValidationError):
            Settings(room_code_length=7)  # Too long

    def test_max_players_validation_valid(self):
        """Test max players validation accepts valid values."""
        settings = Settings(max_players_per_room=2)
        assert settings.max_players_per_room == 2

        settings = Settings(max_players_per_room=20)
        assert settings.max_players_per_room == 20

    def test_max_players_validation_invalid(self):
        """Test max players validation rejects invalid values."""
        with pytest.raises(ValidationError):
            Settings(max_players_per_room=1)  # Too few

        with pytest.raises(ValidationError):
            Settings(max_players_per_room=21)  # Too many

    def test_cors_origins_parsing(self):
        """Test CORS origins parsing from string."""
        settings = Settings(allowed_origins="http://localhost:3000,http://localhost:8000")
        origins = settings.cors_origins

        assert isinstance(origins, list)
        assert len(origins) == 2
        assert "http://localhost:3000" in origins
        assert "http://localhost:8000" in origins

    def test_cors_origins_parsing_with_spaces(self):
        """Test CORS origins parsing handles spaces."""
        settings = Settings(allowed_origins="http://localhost:3000 , http://localhost:8000")
        origins = settings.cors_origins

        # Should strip spaces
        assert "http://localhost:3000" in origins
        assert "http://localhost:8000" in origins
