"""Security utilities for session management and validation."""

import hashlib
import secrets
import string
from datetime import datetime, timedelta

from app.config import settings


def generate_session_id() -> str:
    """
    Generate a cryptographically secure session ID.

    Returns:
        str: 64-character hexadecimal session ID
    """
    return secrets.token_hex(32)


def generate_room_code(length: int | None = None) -> str:
    """
    Generate a unique room code.

    Args:
        length: Code length (defaults to settings.room_code_length)

    Returns:
        str: Uppercase alphanumeric room code
    """
    code_length = length or settings.room_code_length
    # Use uppercase letters and digits, excluding similar-looking characters
    # Exclude: 0, O, I, 1 to avoid confusion
    alphabet = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
    return "".join(secrets.choice(alphabet) for _ in range(code_length))


def validate_room_code(code: str) -> bool:
    """
    Validate room code format.

    Args:
        code: Room code to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not code or not isinstance(code, str):
        return False

    # Must be uppercase alphanumeric, correct length
    if len(code) < 4 or len(code) > 6:
        return False

    return code.isalnum() and code.isupper()


def validate_player_name(name: str) -> bool:
    """
    Validate player name.

    Args:
        name: Player name to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False

    # Remove leading/trailing whitespace
    name = name.strip()

    # Check length (1-50 characters after stripping)
    if len(name) < 1 or len(name) > 50:
        return False

    # Check for only printable characters
    if not all(c.isprintable() for c in name):
        return False

    return True


def sanitize_player_name(name: str) -> str:
    """
    Sanitize player name by removing dangerous characters.

    Args:
        name: Player name to sanitize

    Returns:
        str: Sanitized player name
    """
    # Strip whitespace and truncate to 50 characters
    name = name.strip()[:50]

    # Remove any non-printable characters
    name = "".join(c for c in name if c.isprintable())

    return name


def hash_ip_address(ip_address: str) -> str:
    """
    Hash IP address for privacy-preserving rate limiting.

    Args:
        ip_address: IP address to hash

    Returns:
        str: SHA-256 hash of IP address
    """
    # Use secret key as salt to prevent rainbow table attacks
    salted = f"{settings.secret_key}:{ip_address}"
    return hashlib.sha256(salted.encode()).hexdigest()


def get_session_expiry() -> datetime:
    """
    Get session expiry datetime.

    Returns:
        datetime: Session expiry time
    """
    return datetime.utcnow() + timedelta(hours=settings.session_expire_hours)


def is_session_expired(expiry: datetime) -> bool:
    """
    Check if a session has expired.

    Args:
        expiry: Session expiry datetime

    Returns:
        bool: True if expired, False otherwise
    """
    return datetime.utcnow() > expiry


def validate_session_id(session_id: str) -> bool:
    """
    Validate session ID format.

    Args:
        session_id: Session ID to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not session_id or not isinstance(session_id, str):
        return False

    # Must be 64-character hexadecimal string
    if len(session_id) != 64:
        return False

    try:
        # Verify it's valid hexadecimal
        int(session_id, 16)
        return True
    except ValueError:
        return False
