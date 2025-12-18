"""Unit tests for logging utilities."""

import json
from datetime import datetime

from app.core.logging import serialize_log_record


class TestLoggingSerializer:
    """Tests for log serialization."""

    def test_serialize_basic_log_record(self):
        """Test serializing a basic log record."""

        # Create a mock log record
        class MockLevel:
            name = "INFO"

        record = {
            "time": datetime(2024, 1, 1, 12, 0, 0),
            "level": MockLevel(),
            "message": "Test log message",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "exception": None,
            "extra": None,
        }

        result = serialize_log_record(record)
        data = json.loads(result)

        assert data["timestamp"] == "2024-01-01T12:00:00"
        assert data["level"] == "INFO"
        assert data["message"] == "Test log message"
        assert data["module"] == "test_module"
        assert data["function"] == "test_function"
        assert data["line"] == 42
        assert "exception" not in data
        assert "extra" not in data

    def test_serialize_log_record_with_exception(self):
        """Test serializing log record with exception."""

        class MockLevel:
            name = "ERROR"

        class MockExceptionType:
            __name__ = "ValueError"

        class MockException:
            type = MockExceptionType()
            value = ValueError("Test error")
            traceback = "Traceback..."

        record = {
            "time": datetime(2024, 1, 1, 12, 0, 0),
            "level": MockLevel(),
            "message": "Error occurred",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "exception": MockException(),
            "extra": None,
        }

        result = serialize_log_record(record)
        data = json.loads(result)

        assert data["level"] == "ERROR"
        assert data["message"] == "Error occurred"
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "Test error" in data["exception"]["value"]
        assert data["exception"]["traceback"] == "Traceback..."

    def test_serialize_log_record_with_extra_fields(self):
        """Test serializing log record with extra fields."""

        class MockLevel:
            name = "DEBUG"

        record = {
            "time": datetime(2024, 1, 1, 12, 0, 0),
            "level": MockLevel(),
            "message": "Debug message",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "exception": None,
            "extra": {"user_id": 123, "request_id": "abc-def"},
        }

        result = serialize_log_record(record)
        data = json.loads(result)

        assert data["level"] == "DEBUG"
        assert data["message"] == "Debug message"
        assert "extra" in data
        assert data["extra"]["user_id"] == 123
        assert data["extra"]["request_id"] == "abc-def"

    def test_serialize_log_record_with_empty_extra(self):
        """Test serializing log record with empty extra dict."""

        class MockLevel:
            name = "INFO"

        record = {
            "time": datetime(2024, 1, 1, 12, 0, 0),
            "level": MockLevel(),
            "message": "Test message",
            "module": "test_module",
            "function": "test_function",
            "line": 42,
            "exception": None,
            "extra": {},
        }

        result = serialize_log_record(record)
        data = json.loads(result)

        # Empty extra dict should not be included
        assert "extra" not in data

    def test_serialize_log_record_returns_valid_json(self):
        """Test that serialize_log_record always returns valid JSON."""

        class MockLevel:
            name = "WARNING"

        record = {
            "time": datetime(2024, 12, 31, 23, 59, 59),
            "level": MockLevel(),
            "message": "Year end warning",
            "module": "warnings",
            "function": "warn",
            "line": 100,
            "exception": None,
            "extra": {"severity": "high", "count": 5},
        }

        result = serialize_log_record(record)

        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)

        # Verify structure
        assert "timestamp" in data
        assert "level" in data
        assert "message" in data
        assert "module" in data
        assert "function" in data
        assert "line" in data
