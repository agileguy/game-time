"""WebSocket connection manager."""

import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from app.core.exceptions import WebSocketError
from app.core.logging import get_logger

logger = get_logger()


class WebSocketMessage(BaseModel):
    """WebSocket message schema."""

    type: str
    data: dict[str, Any]
    timestamp: int | None = None
    message_id: str | None = None

    def __init__(self, **data):
        """Initialize with timestamp and message_id if not provided."""
        if "timestamp" not in data:
            data["timestamp"] = int(datetime.utcnow().timestamp() * 1000)
        if "message_id" not in data:
            data["message_id"] = str(uuid.uuid4())
        super().__init__(**data)


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        # connection_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}
        # session_id -> connection_id
        self.session_connections: dict[str, str] = {}
        # room_code -> list[connection_id]
        self.room_connections: dict[str, list[str]] = {}

    def generate_connection_id(self) -> str:
        """
        Generate unique connection ID.

        Returns:
            str: Connection ID
        """
        return str(uuid.uuid4())

    async def connect(self, websocket: WebSocket, session_id: str, room_code: str) -> str:
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: WebSocket connection
            session_id: Player session ID
            room_code: Room code

        Returns:
            str: Connection ID
        """
        await websocket.accept()

        connection_id = self.generate_connection_id()

        # Store connection
        self.active_connections[connection_id] = websocket

        # Map session to connection
        self.session_connections[session_id] = connection_id

        # Add to room
        if room_code not in self.room_connections:
            self.room_connections[room_code] = []
        self.room_connections[room_code].append(connection_id)

        logger.info(
            "WebSocket connected",
            extra={
                "connection_id": connection_id,
                "session_id": session_id,
                "room_code": room_code,
            },
        )

        return connection_id

    async def disconnect(self, connection_id: str, session_id: str, room_code: str):
        """
        Disconnect and cleanup a WebSocket connection.

        Args:
            connection_id: Connection ID
            session_id: Session ID
            room_code: Room code
        """
        # Remove from active connections
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        # Remove session mapping
        if session_id in self.session_connections:
            del self.session_connections[session_id]

        # Remove from room
        if room_code in self.room_connections:
            if connection_id in self.room_connections[room_code]:
                self.room_connections[room_code].remove(connection_id)

            # Clean up empty room lists
            if not self.room_connections[room_code]:
                del self.room_connections[room_code]

        logger.info(
            "WebSocket disconnected",
            extra={
                "connection_id": connection_id,
                "session_id": session_id,
                "room_code": room_code,
            },
        )

    async def send_personal_message(self, message: dict[str, Any], connection_id: str):
        """
        Send message to a specific connection.

        Args:
            message: Message to send
            connection_id: Target connection ID
        """
        if connection_id not in self.active_connections:
            return

        websocket = self.active_connections[connection_id]

        try:
            # Check if WebSocket is still open
            if websocket.client_state.name != "CONNECTED":
                logger.warning(
                    f"WebSocket not connected, state: {websocket.client_state.name}",
                    extra={"connection_id": connection_id},
                )
                # Remove from active connections
                del self.active_connections[connection_id]
                return

            # Wrap in WebSocketMessage for consistent format
            ws_message = WebSocketMessage(
                type=message.get("type", "message"), data=message.get("data", message)
            )
            await websocket.send_json(ws_message.model_dump())
        except Exception as e:
            logger.error(f"Error sending message: {e}", extra={"connection_id": connection_id})
            # Remove broken connection
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]

    async def send_to_session(self, message: dict[str, Any], session_id: str):
        """
        Send message to a specific session.

        Args:
            message: Message to send
            session_id: Target session ID
        """
        if session_id not in self.session_connections:
            return

        connection_id = self.session_connections[session_id]
        await self.send_personal_message(message, connection_id)

    async def broadcast_to_room(
        self, message: dict[str, Any], room_code: str, exclude: str | None = None
    ):
        """
        Broadcast message to all connections in a room.

        Args:
            message: Message to broadcast
            room_code: Room code
            exclude: Optional connection ID to exclude
        """
        if room_code not in self.room_connections:
            return

        # Wrap in WebSocketMessage
        ws_message = WebSocketMessage(
            type=message.get("type", "message"), data=message.get("data", message)
        )
        message_json = ws_message.model_dump()

        # Create a copy of the list to avoid modification during iteration
        connection_ids = list(self.room_connections[room_code])

        for connection_id in connection_ids:
            if exclude and connection_id == exclude:
                continue

            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    # Check if WebSocket is still open
                    if websocket.client_state.name != "CONNECTED":
                        logger.warning(
                            "Skipping disconnected WebSocket in broadcast",
                            extra={"connection_id": connection_id},
                        )
                        # Remove from active connections
                        del self.active_connections[connection_id]
                        continue

                    await websocket.send_json(message_json)
                except Exception as e:
                    logger.error(
                        f"Error broadcasting to {connection_id}: {e}",
                        extra={"room_code": room_code},
                    )
                    # Remove broken connection
                    if connection_id in self.active_connections:
                        del self.active_connections[connection_id]

    async def receive_message(self, websocket: WebSocket) -> WebSocketMessage:
        """
        Receive and validate a message from WebSocket.

        Args:
            websocket: WebSocket connection

        Returns:
            WebSocketMessage: Validated message

        Raises:
            WebSocketError: If message is invalid
            WebSocketDisconnect: If connection is closed
        """
        try:
            data = await websocket.receive_json()

            # Validate message format
            message = WebSocketMessage(**data)
            return message

        except WebSocketDisconnect:
            raise
        except ValidationError as e:
            raise WebSocketError(f"Invalid message format: {e}") from e
        except json.JSONDecodeError as e:
            raise WebSocketError("Invalid JSON") from e
        except Exception as e:
            raise WebSocketError(f"Error receiving message: {e}") from e

    async def send_error(self, error: str, connection_id: str, code: str = "ERROR"):
        """
        Send error message to a connection.

        Args:
            error: Error message
            connection_id: Target connection ID
            code: Error code
        """
        error_message = {
            "type": "error",
            "data": {
                "code": code,
                "message": error,
                "retryable": False,
            },
        }
        await self.send_personal_message(error_message, connection_id)

    def get_room_connection_count(self, room_code: str) -> int:
        """
        Get number of active connections in a room.

        Args:
            room_code: Room code

        Returns:
            int: Connection count
        """
        if room_code not in self.room_connections:
            return 0
        return len(self.room_connections[room_code])

    def is_connected(self, session_id: str) -> bool:
        """
        Check if a session has an active connection.

        Args:
            session_id: Session ID

        Returns:
            bool: True if connected
        """
        return session_id in self.session_connections


# Global connection manager instance
connection_manager = ConnectionManager()
