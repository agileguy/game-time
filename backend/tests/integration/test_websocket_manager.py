"""Integration tests for WebSocket Manager."""

import pytest

from app.services.websocket_manager import ConnectionManager, WebSocketMessage


@pytest.mark.integration
class TestWebSocketManagerIntegration:
    """Integration tests for ConnectionManager."""

    def test_websocket_message_creation(self):
        """Test WebSocketMessage creation."""
        msg = WebSocketMessage(
            type="test",
            data={"key": "value"},
        )

        assert msg.type == "test"
        assert msg.data == {"key": "value"}
        assert msg.timestamp is not None
        assert msg.message_id is not None

    def test_websocket_message_with_custom_fields(self):
        """Test WebSocketMessage with custom timestamp and ID."""
        msg = WebSocketMessage(
            type="test",
            data={"key": "value"},
            timestamp=1234567890,
            message_id="custom-id",
        )

        assert msg.timestamp == 1234567890
        assert msg.message_id == "custom-id"

    def test_connection_manager_init(self):
        """Test ConnectionManager initialization."""
        manager = ConnectionManager()

        assert len(manager.active_connections) == 0
        assert len(manager.session_connections) == 0
        assert len(manager.room_connections) == 0

    def test_generate_connection_id(self):
        """Test connection ID generation."""
        manager = ConnectionManager()

        conn_id1 = manager.generate_connection_id()
        conn_id2 = manager.generate_connection_id()

        assert conn_id1 != conn_id2
        assert len(conn_id1) == 36  # UUID length
        assert len(conn_id2) == 36

    async def test_connect_and_disconnect(self, mock_websocket):
        """Test connecting and disconnecting WebSocket."""
        manager = ConnectionManager()

        # Connect
        connection_id = await manager.connect(
            websocket=mock_websocket,
            session_id="session_123",
            room_code="ABCD",
        )

        # Verify connected
        assert connection_id in manager.active_connections
        assert manager.session_connections["session_123"] == connection_id
        assert connection_id in manager.room_connections["ABCD"]
        mock_websocket.accept.assert_called_once()

        # Disconnect
        await manager.disconnect(connection_id, "session_123", "ABCD")

        # Verify disconnected
        assert connection_id not in manager.active_connections
        assert "session_123" not in manager.session_connections
        assert "ABCD" not in manager.room_connections

    async def test_send_personal_message(self, mock_websocket):
        """Test sending personal message."""
        manager = ConnectionManager()

        connection_id = await manager.connect(
            websocket=mock_websocket,
            session_id="session_123",
            room_code="ABCD",
        )

        # Send message
        await manager.send_personal_message(
            message={"type": "test", "data": {"msg": "hello"}},
            connection_id=connection_id,
        )

        # Verify sent
        mock_websocket.send_json.assert_called_once()
        sent_data = mock_websocket.send_json.call_args[0][0]
        assert sent_data["type"] == "test"
        assert sent_data["data"]["msg"] == "hello"

    async def test_send_to_session(self, mock_websocket):
        """Test sending message to session."""
        manager = ConnectionManager()

        await manager.connect(
            websocket=mock_websocket,
            session_id="session_123",
            room_code="ABCD",
        )

        # Send to session
        await manager.send_to_session(
            message={"type": "test", "data": {"msg": "hello"}},
            session_id="session_123",
        )

        # Verify sent
        assert mock_websocket.send_json.called

    async def test_broadcast_to_room(self, mock_websocket):
        """Test broadcasting to all connections in room."""
        manager = ConnectionManager()

        # Create mock websockets
        from unittest.mock import AsyncMock, MagicMock

        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws1.client_state.name = "CONNECTED"

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        ws2.client_state.name = "CONNECTED"

        # Connect two clients to same room
        await manager.connect(ws1, "session_1", "ABCD")
        await manager.connect(ws2, "session_2", "ABCD")

        # Broadcast
        await manager.broadcast_to_room(
            message={"type": "announcement", "data": {"msg": "hello all"}},
            room_code="ABCD",
        )

        # Both should receive
        assert ws1.send_json.called
        assert ws2.send_json.called

    async def test_broadcast_to_room_with_exclude(self, mock_websocket):
        """Test broadcasting with exclusion."""
        from unittest.mock import AsyncMock, MagicMock

        manager = ConnectionManager()

        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws1.client_state.name = "CONNECTED"

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        ws2.client_state.name = "CONNECTED"

        # Connect two clients
        conn_id1 = await manager.connect(ws1, "session_1", "ABCD")
        await manager.connect(ws2, "session_2", "ABCD")

        # Broadcast excluding conn_id1
        await manager.broadcast_to_room(
            message={"type": "test", "data": {}},
            room_code="ABCD",
            exclude=conn_id1,
        )

        # Only ws2 should receive
        assert not ws1.send_json.called
        assert ws2.send_json.called

    async def test_send_error(self, mock_websocket):
        """Test sending error message."""
        manager = ConnectionManager()

        connection_id = await manager.connect(
            websocket=mock_websocket,
            session_id="session_123",
            room_code="ABCD",
        )

        # Send error
        await manager.send_error(
            error="Something went wrong",
            connection_id=connection_id,
            code="TEST_ERROR",
        )

        # Verify error message format
        mock_websocket.send_json.assert_called()
        sent_data = mock_websocket.send_json.call_args[0][0]
        assert sent_data["type"] == "error"
        assert sent_data["data"]["code"] == "TEST_ERROR"
        assert sent_data["data"]["message"] == "Something went wrong"
        assert sent_data["data"]["retryable"] is False

    def test_get_room_connection_count(self):
        """Test getting connection count for room."""
        manager = ConnectionManager()

        # No connections
        count = manager.get_room_connection_count("ABCD")
        assert count == 0

        # Add connections manually
        manager.room_connections["ABCD"] = ["conn1", "conn2", "conn3"]
        count = manager.get_room_connection_count("ABCD")
        assert count == 3

    def test_is_connected(self):
        """Test checking if session is connected."""
        manager = ConnectionManager()

        # Not connected
        assert manager.is_connected("session_123") is False

        # Connect
        manager.session_connections["session_123"] = "conn_abc"
        assert manager.is_connected("session_123") is True

    async def test_multiple_rooms(self, mock_websocket):
        """Test managing connections across multiple rooms."""
        from unittest.mock import AsyncMock, MagicMock

        manager = ConnectionManager()

        # Create websockets for different rooms
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws1.client_state.name = "CONNECTED"

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        ws2.client_state.name = "CONNECTED"

        ws3 = MagicMock()
        ws3.accept = AsyncMock()
        ws3.send_json = AsyncMock()
        ws3.client_state.name = "CONNECTED"

        # Connect to different rooms
        await manager.connect(ws1, "s1", "ROOM1")
        await manager.connect(ws2, "s2", "ROOM2")
        await manager.connect(ws3, "s3", "ROOM1")

        # Verify room assignments
        assert manager.get_room_connection_count("ROOM1") == 2
        assert manager.get_room_connection_count("ROOM2") == 1

        # Broadcast to ROOM1
        await manager.broadcast_to_room(
            message={"type": "test", "data": {}},
            room_code="ROOM1",
        )

        # Only ROOM1 connections should receive
        assert ws1.send_json.called
        assert not ws2.send_json.called
        assert ws3.send_json.called

    async def test_cleanup_on_disconnect(self, mock_websocket):
        """Test proper cleanup when disconnecting."""
        manager = ConnectionManager()

        connection_id = await manager.connect(
            websocket=mock_websocket,
            session_id="session_123",
            room_code="ABCD",
        )

        # Verify connections exist
        assert len(manager.active_connections) == 1
        assert len(manager.session_connections) == 1
        assert len(manager.room_connections) == 1

        # Disconnect
        await manager.disconnect(connection_id, "session_123", "ABCD")

        # Verify all cleaned up
        assert len(manager.active_connections) == 0
        assert len(manager.session_connections) == 0
        assert len(manager.room_connections) == 0


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket."""
    from unittest.mock import AsyncMock, MagicMock

    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_json = AsyncMock()
    websocket.close = AsyncMock()
    # Configure client_state for connection checks
    websocket.client_state.name = "CONNECTED"
    return websocket
