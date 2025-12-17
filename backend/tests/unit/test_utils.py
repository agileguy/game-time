"""Unit tests for utils module."""


import app.utils
from app.utils import (
    generate_room_code,
    sanitize_player_name,
    validate_player_name,
    validate_room_code,
)


class TestUtilsImport:
    """Tests for utils module imports."""

    def test_utils_module_imports(self):
        """Test that utils module can be imported."""
        assert app.utils is not None

    def test_utils_exports_generate_room_code(self):
        """Test that generate_room_code is exported."""
        assert callable(generate_room_code)
        # Test it works
        code = generate_room_code()
        assert len(code) == 4
        assert code.isalnum()
        assert code.isupper()

    def test_utils_exports_validate_room_code(self):
        """Test that validate_room_code is exported."""
        assert callable(validate_room_code)
        # Test it works
        assert validate_room_code("ABCD") is True
        assert validate_room_code("abc") is False

    def test_utils_exports_validate_player_name(self):
        """Test that validate_player_name is exported."""
        assert callable(validate_player_name)
        # Test it works
        assert validate_player_name("Alice") is True
        assert validate_player_name("") is False

    def test_utils_exports_sanitize_player_name(self):
        """Test that sanitize_player_name is exported."""
        assert callable(sanitize_player_name)
        # Test it works
        result = sanitize_player_name("  Alice  ")
        assert result == "Alice"

    def test_utils_all_exports(self):
        """Test __all__ contains expected exports."""
        assert hasattr(app.utils, "__all__")
        assert "generate_room_code" in app.utils.__all__
        assert "validate_room_code" in app.utils.__all__
        assert "validate_player_name" in app.utils.__all__
        assert "sanitize_player_name" in app.utils.__all__
