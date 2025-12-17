"""Unit tests for security utilities."""

from datetime import datetime, timedelta

from app.core.security import (
    generate_room_code,
    generate_session_id,
    get_session_expiry,
    hash_ip_address,
    is_session_expired,
    sanitize_player_name,
    validate_player_name,
    validate_room_code,
    validate_session_id,
)


class TestSessionID:
    """Tests for session ID generation and validation."""

    def test_generate_session_id(self):
        """Test session ID generation."""
        session_id = generate_session_id()

        assert isinstance(session_id, str)
        assert len(session_id) == 64
        assert session_id.isalnum()
        assert session_id.islower()  # Hex is lowercase

    def test_generate_unique_session_ids(self):
        """Test that generated session IDs are unique."""
        ids = [generate_session_id() for _ in range(100)]
        assert len(ids) == len(set(ids))  # All unique

    def test_validate_session_id_valid(self):
        """Test validation of valid session ID."""
        session_id = generate_session_id()
        assert validate_session_id(session_id) is True

    def test_validate_session_id_invalid_length(self):
        """Test validation rejects wrong length."""
        assert validate_session_id("abc123") is False

    def test_validate_session_id_invalid_chars(self):
        """Test validation rejects non-hex characters."""
        invalid_id = "z" * 64
        assert validate_session_id(invalid_id) is False

    def test_validate_session_id_none(self):
        """Test validation rejects None."""
        assert validate_session_id(None) is False


class TestRoomCode:
    """Tests for room code generation and validation."""

    def test_generate_room_code_default_length(self):
        """Test room code generation with default length."""
        code = generate_room_code()

        assert isinstance(code, str)
        assert len(code) == 4  # Default from settings
        assert code.isupper()
        assert code.isalnum()

    def test_generate_room_code_custom_length(self):
        """Test room code generation with custom length."""
        code = generate_room_code(length=6)

        assert len(code) == 6
        assert code.isupper()
        assert code.isalnum()

    def test_generate_room_code_no_confusing_chars(self):
        """Test room codes don't contain confusing characters."""
        # Generate many codes to check character set
        codes = [generate_room_code() for _ in range(100)]
        all_chars = "".join(codes)

        # Should not contain O, I, 0, 1
        assert "O" not in all_chars
        assert "I" not in all_chars
        assert "0" not in all_chars
        assert "1" not in all_chars

    def test_validate_room_code_valid(self):
        """Test validation of valid room codes."""
        assert validate_room_code("ABCD") is True
        assert validate_room_code("XY23") is True
        assert validate_room_code("ABCDEF") is True

    def test_validate_room_code_invalid_length(self):
        """Test validation rejects invalid lengths."""
        assert validate_room_code("ABC") is False  # Too short
        assert validate_room_code("ABCDEFG") is False  # Too long

    def test_validate_room_code_lowercase(self):
        """Test validation rejects lowercase."""
        assert validate_room_code("abcd") is False

    def test_validate_room_code_special_chars(self):
        """Test validation rejects special characters."""
        assert validate_room_code("AB-D") is False
        assert validate_room_code("AB D") is False

    def test_validate_room_code_none(self):
        """Test validation rejects None."""
        assert validate_room_code(None) is False


class TestPlayerName:
    """Tests for player name validation and sanitization."""

    def test_validate_player_name_valid(self):
        """Test validation of valid player names."""
        assert validate_player_name("Alice") is True
        assert validate_player_name("Bob123") is True
        assert validate_player_name("Player One") is True

    def test_validate_player_name_strips_whitespace(self):
        """Test that validation handles whitespace."""
        assert validate_player_name("  Alice  ") is True

    def test_validate_player_name_empty(self):
        """Test validation rejects empty names."""
        assert validate_player_name("") is False
        assert validate_player_name("   ") is False

    def test_validate_player_name_too_long(self):
        """Test validation rejects names over 50 chars."""
        long_name = "x" * 51
        assert validate_player_name(long_name) is False

    def test_validate_player_name_none(self):
        """Test validation rejects None."""
        assert validate_player_name(None) is False

    def test_sanitize_player_name_basic(self):
        """Test basic name sanitization."""
        assert sanitize_player_name("Alice") == "Alice"
        assert sanitize_player_name("  Bob  ") == "Bob"

    def test_sanitize_player_name_truncate(self):
        """Test name truncation."""
        long_name = "x" * 100
        sanitized = sanitize_player_name(long_name)
        assert len(sanitized) == 50

    def test_sanitize_player_name_remove_non_printable(self):
        """Test removal of non-printable characters."""
        name_with_control = "Alice\x00\x01"
        sanitized = sanitize_player_name(name_with_control)
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized


class TestIPHashing:
    """Tests for IP address hashing."""

    def test_hash_ip_address(self):
        """Test IP address hashing."""
        ip = "192.168.1.1"
        hashed = hash_ip_address(ip)

        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA-256 hex digest

    def test_hash_ip_address_consistent(self):
        """Test that hashing is consistent."""
        ip = "192.168.1.1"
        hash1 = hash_ip_address(ip)
        hash2 = hash_ip_address(ip)

        assert hash1 == hash2

    def test_hash_ip_address_different_ips(self):
        """Test that different IPs produce different hashes."""
        hash1 = hash_ip_address("192.168.1.1")
        hash2 = hash_ip_address("192.168.1.2")

        assert hash1 != hash2


class TestSessionExpiry:
    """Tests for session expiry utilities."""

    def test_get_session_expiry(self):
        """Test session expiry calculation."""
        expiry = get_session_expiry()

        assert isinstance(expiry, datetime)
        assert expiry > datetime.utcnow()

    def test_is_session_expired_not_expired(self):
        """Test checking non-expired session."""
        future = datetime.utcnow() + timedelta(hours=1)
        assert is_session_expired(future) is False

    def test_is_session_expired_expired(self):
        """Test checking expired session."""
        past = datetime.utcnow() - timedelta(hours=1)
        assert is_session_expired(past) is True
