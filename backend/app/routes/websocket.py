"""WebSocket endpoint for real-time communication."""

import asyncio

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError, WebSocketError
from app.core.logging import get_logger
from app.database import get_db
from app.redis_client import get_redis
from app.schemas.room import PlayerInfo, RoomState
from app.services import PlayerManager, RoomManager, connection_manager

logger = get_logger()

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    WebSocket endpoint for real-time game communication.

    Args:
        websocket: WebSocket connection
        session_id: Player session ID
        db: Database session
        redis: Redis client
    """
    player_manager = PlayerManager(db, redis)
    room_manager = RoomManager(db)

    connection_id = None
    room_code = None
    player_id = None

    try:
        # Validate session
        if not await player_manager.validate_session(session_id):
            await websocket.close(code=4001, reason="Invalid session")
            return

        # Get player
        player = await player_manager.get_player_by_session(session_id)
        if not player:
            await websocket.close(code=4002, reason="Player not found")
            return

        player_id = player.id
        room = await room_manager.get_room_by_id(player.room_id)
        if not room:
            await websocket.close(code=4003, reason="Room not found")
            return

        room_code = room.code

        # Connect WebSocket
        connection_id = await connection_manager.connect(websocket, session_id, room_code)

        # Store connection in Redis
        await player_manager.store_connection(session_id, connection_id, room_code)

        # Update player connection status
        await player_manager.update_player_connection(player_id, connected=True)
        await db.commit()

        # Send initial room state
        await send_room_state(room, connection_id, room_manager, player_manager)

        # Notify others that player joined
        await connection_manager.broadcast_to_room(
            message={
                "type": "player_joined",
                "data": {
                    "player_id": player_id,
                    "player_name": player.name,
                    "is_host": player.is_host,
                },
            },
            room_code=room_code,
            exclude=connection_id,
        )

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            send_heartbeat(websocket, connection_id, player_manager, player_id)
        )

        # Message loop
        while True:
            try:
                # Receive message
                message = await connection_manager.receive_message(websocket)

                # Update last seen
                await player_manager.update_last_seen(player_id)

                # Handle message
                await handle_message(
                    message=message,
                    connection_id=connection_id,
                    session_id=session_id,
                    player_id=player_id,
                    room_code=room_code,
                    db=db,
                    redis=redis,
                )

                await db.commit()

            except WebSocketDisconnect:
                break
            except WebSocketError as e:
                await connection_manager.send_error(str(e), connection_id)
            except Exception as e:
                logger.error(f"Error handling message: {e}", extra={"session_id": session_id})
                await connection_manager.send_error("Internal error", connection_id)
                await db.rollback()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}", extra={"session_id": session_id})
    finally:
        # Cleanup
        if heartbeat_task:
            heartbeat_task.cancel()

        if connection_id and room_code:
            # Disconnect WebSocket
            await connection_manager.disconnect(connection_id, session_id, room_code)

            # Remove connection from Redis
            await player_manager.remove_connection(session_id)

            # Update player connection status
            if player_id:
                await player_manager.update_player_connection(player_id, connected=False)
                await db.commit()

                # Notify others that player left
                await connection_manager.broadcast_to_room(
                    message={
                        "type": "player_left",
                        "data": {"player_id": player_id},
                    },
                    room_code=room_code,
                )


async def send_room_state(
    room,
    connection_id: str,
    room_manager: RoomManager,
    player_manager: PlayerManager,
):
    """Send full room state to a connection."""
    # Get all players
    players = await player_manager.get_room_players(room.id)

    # Build player info list
    player_infos = [
        PlayerInfo(
            player_id=p.id,
            name=p.name,
            is_host=p.is_host,
            connected=p.connected,
        )
        for p in players
    ]

    # Build room state
    room_state = RoomState(
        room_code=room.code,
        room_id=room.id,
        status=room.status,
        max_players=room.max_players,
        current_game=room.current_game,
        host_player_id=room.host_player_id,
        players=player_infos,
    )

    # Send to connection
    await connection_manager.send_personal_message(
        message={
            "type": "lobby_state",
            "data": room_state.model_dump(),
        },
        connection_id=connection_id,
    )


async def send_heartbeat(
    websocket: WebSocket,
    connection_id: str,
    player_manager: PlayerManager,
    player_id: int,
):
    """Send periodic heartbeat to keep connection alive."""
    try:
        while True:
            await asyncio.sleep(30)  # 30 second heartbeat
            try:
                await connection_manager.send_personal_message(
                    message={"type": "ping", "data": {}},
                    connection_id=connection_id,
                )
                # Update last seen
                await player_manager.update_last_seen(player_id)
            except Exception:
                break
    except asyncio.CancelledError:
        pass


async def handle_message(
    message,
    connection_id: str,
    session_id: str,
    player_id: int,
    room_code: str,
    db: AsyncSession,
    redis: aioredis.Redis,
):
    """
    Handle incoming WebSocket messages.

    Args:
        message: WebSocket message
        connection_id: Connection ID
        session_id: Session ID
        player_id: Player ID
        room_code: Room code
        db: Database session
        redis: Redis client
    """
    room_manager = RoomManager(db)
    player_manager = PlayerManager(db, redis)

    message_type = message.type

    # Handle pong (heartbeat response)
    if message_type == "pong":
        return

    # Handle leave room
    if message_type == "leave_room":
        await room_manager.leave_room(player_id)
        return

    # Handle kick player (host only)
    if message_type == "kick_player":
        target_player_id = message.data.get("player_id")
        if target_player_id:
            try:
                await room_manager.kick_player(
                    room_id=message.data.get("room_id"),
                    player_id=target_player_id,
                    kicker_id=player_id,
                )

                # Notify room
                await connection_manager.broadcast_to_room(
                    message={
                        "type": "player_kicked",
                        "data": {"player_id": target_player_id},
                    },
                    room_code=room_code,
                )
            except ValidationError as e:
                await connection_manager.send_error(str(e), connection_id, "FORBIDDEN")

    # Handle start game (host only)
    elif message_type == "start_game":
        game_type = message.data.get("game_type")
        if game_type:
            # Get player
            player = await player_manager.get_player_by_id(player_id)
            if player and player.is_host:
                # Update room status
                room = await room_manager.get_room_by_id(player.room_id)
                if room and room.status == "lobby":
                    room.status = "playing"
                    room.current_game = game_type
                    await db.flush()

                    # Notify room
                    await connection_manager.broadcast_to_room(
                        message={
                            "type": "game_starting",
                            "data": {"game_type": game_type},
                        },
                        room_code=room_code,
                    )
            else:
                await connection_manager.send_error(
                    "Only host can start game", connection_id, "FORBIDDEN"
                )

    # Unknown message type
    else:
        logger.warning(f"Unknown message type: {message_type}")
