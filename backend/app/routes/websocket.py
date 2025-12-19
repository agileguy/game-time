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
from app.services.game_manager import get_game_manager

logger = get_logger()

router = APIRouter(prefix="/api", tags=["websocket"])


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
    heartbeat_task = None

    try:
        # Validate session
        logger.info(f"WebSocket connecting: session={session_id[:8]}...")
        if not await player_manager.validate_session(session_id):
            logger.warning(f"Invalid session: {session_id[:8]}...")
            await websocket.close(code=4001, reason="Invalid session")
            return

        # Get player
        player = await player_manager.get_player_by_session(session_id)
        if not player:
            logger.warning(f"Player not found for session: {session_id[:8]}...")
            await websocket.close(code=4002, reason="Player not found")
            return

        player_id = player.id
        logger.info(f"Player {player_id} ({player.name}) attempting WebSocket connection")

        room = await room_manager.get_room_by_id(player.room_id)
        if not room:
            logger.warning(f"Room not found for player {player_id}")
            await websocket.close(code=4003, reason="Room not found")
            return

        room_code = room.code
        logger.info(f"Player {player_id} joining room {room_code}")

        # Connect WebSocket
        connection_id = await connection_manager.connect(websocket, session_id, room_code)
        logger.info(f"WebSocket connected: player={player_id}, connection={connection_id[:8]}...")

        # Store connection in Redis
        await player_manager.store_connection(session_id, connection_id, room_code)

        # Update player connection status
        await player_manager.update_player_connection(player_id, connected=True)
        await db.commit()
        logger.info(f"Player {player_id} connection status updated to connected=True")

        # Send initial room state
        try:
            await send_room_state(room, connection_id, room_manager, player_manager)
            logger.info(f"Sent room state to connection {connection_id}")
        except Exception as e:
            logger.error(f"Failed to send room state: {e}", exc_info=True)
            raise

        # Notify others that player joined
        player_joined_msg = {
            "type": "player_joined",
            "data": {
                "player_id": player_id,
                "player_name": player.name,
                "is_host": player.is_host,
            },
        }
        logger.info(
            f"Player {player_id} broadcasting player_joined to room {room_code}: {player_joined_msg}"
        )
        try:
            await connection_manager.broadcast_to_room(
                message=player_joined_msg,
                room_code=room_code,
                exclude=connection_id,
            )
            logger.info(f"Player {player_id} broadcast complete successfully")
        except Exception as e:
            logger.error(f"Player {player_id} broadcast failed: {e}", exc_info=True)

        # Broadcast updated room state to ALL players (including new player)
        # This ensures everyone sees the updated player list
        logger.info(f"Broadcasting updated room state to all players in room {room_code}")
        try:
            await send_room_state_to_all(room, room_code, room_manager, player_manager)
            logger.info("Room state broadcast complete")
        except Exception as e:
            logger.error(f"Failed to broadcast room state: {e}", exc_info=True)

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat(websocket, connection_id, player_id))

        # Message loop
        logger.info(f"Player {player_id} entering message loop")
        while True:
            try:
                # Receive message
                logger.debug(f"Player {player_id} waiting for message...")
                message = await connection_manager.receive_message(websocket)
                logger.info(f"Player {player_id} received message: {message.type}")

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

            except WebSocketDisconnect as e:
                logger.info(f"Player {player_id} received WebSocketDisconnect in message loop: {e}")
                break
            except WebSocketError as e:
                logger.error(f"Player {player_id} WebSocketError in message loop: {e}")
                # WebSocket is broken, exit the loop
                break
            except Exception as e:
                logger.error(
                    f"Error handling message for player {player_id}: {e}",
                    extra={"session_id": session_id},
                    exc_info=True,
                )
                try:
                    await connection_manager.send_error("Internal error", connection_id)
                except Exception:
                    # If we can't send error, connection is broken
                    logger.error(f"Could not send error to player {player_id}, breaking connection")
                    break
                await db.rollback()

    except WebSocketDisconnect as e:
        logger.info(
            f"Player {player_id} WebSocket disconnected normally (outer): code={getattr(e, 'code', 'N/A')}, reason={getattr(e, 'reason', 'N/A')}"
        )
        pass
    except Exception as e:
        logger.error(
            f"WebSocket error for player {player_id}: {e}",
            extra={"session_id": session_id},
            exc_info=True,
        )
    finally:
        # Cleanup
        logger.info(f"WebSocket cleanup starting for player {player_id}")
        if heartbeat_task:
            heartbeat_task.cancel()

        if connection_id and room_code:
            # Disconnect WebSocket
            await connection_manager.disconnect(connection_id, session_id, room_code)

            # Remove connection from Redis
            await player_manager.remove_connection(session_id)

            # Update player connection status
            if player_id:
                logger.info(f"Setting player {player_id} connection status to disconnected")
                # Get player info before updating connection status
                player = await player_manager.get_player_by_id(player_id)
                player_name = player.name if player else f"Player {player_id}"

                # Check if player was host before updating connection
                was_host = player.is_host if player else False

                await player_manager.update_player_connection(player_id, connected=False)
                await db.commit()

                # Notify others that player left
                await connection_manager.broadcast_to_room(
                    message={
                        "type": "player_left",
                        "data": {
                            "player_id": player_id,
                            "player_name": player_name,
                        },
                    },
                    room_code=room_code,
                )

                # If player was host, transfer to another player
                if was_host:
                    room = await room_manager.get_room_by_code(room_code)
                    if room:
                        # Import Optional and Player for type hints
                        from app.models.player import Player as PlayerModel

                        new_host: PlayerModel | None = await room_manager._transfer_host(room)
                        await db.commit()

                        # Refresh room to get latest state
                        await db.refresh(room)

                        if new_host:
                            logger.info(
                                f"Host transferred to player {new_host.id} ({new_host.name})"
                            )
                            # Broadcast host transfer event
                            await connection_manager.broadcast_to_room(
                                message={
                                    "type": "host_transferred",
                                    "data": {
                                        "new_host_id": new_host.id,
                                        "new_host_name": new_host.name,
                                    },
                                },
                                room_code=room_code,
                            )

                # Broadcast updated room state to all remaining players
                try:
                    room = await room_manager.get_room_by_code(room_code)
                    if room:
                        logger.info(
                            f"Broadcasting updated room state after player {player_id} left"
                        )
                        await send_room_state_to_all(room, room_code, room_manager, player_manager)
                except Exception as e:
                    logger.error(
                        f"Failed to broadcast room state after player left: {e}", exc_info=True
                    )

                logger.info(f"WebSocket cleanup complete for player {player_id}")


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
            session_id=p.session_id,
            name=p.name,
            is_host=p.is_host,
            connected=p.connected,
        )
        for p in players
    ]

    # Log player connection statuses
    logger.info(f"Room {room.code} players: {[(p.name, p.connected) for p in players]}")

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
            "type": "room_state",
            "data": room_state.model_dump(by_alias=True),
        },
        connection_id=connection_id,
    )


async def send_room_state_to_all(
    room,
    room_code: str,
    room_manager: RoomManager,
    player_manager: PlayerManager,
):
    """Broadcast full room state to all connections in the room."""
    # Get all players
    players = await player_manager.get_room_players(room.id)

    # Build player info list
    player_infos = [
        PlayerInfo(
            player_id=p.id,
            session_id=p.session_id,
            name=p.name,
            is_host=p.is_host,
            connected=p.connected,
        )
        for p in players
    ]

    # Log player connection statuses
    logger.info(
        f"Broadcasting room {room.code} state with players: {[(p.name, p.connected) for p in players]}"
    )

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

    # Broadcast to all connections in room
    await connection_manager.broadcast_to_room(
        message={
            "type": "room_state",
            "data": room_state.model_dump(by_alias=True),
        },
        room_code=room_code,
    )


async def send_heartbeat(
    websocket: WebSocket,
    connection_id: str,
    player_id: int,
):
    """Send periodic heartbeat to keep connection alive."""
    logger.info(f"Heartbeat task started for player {player_id}")
    try:
        while True:
            logger.debug(f"Heartbeat sleeping 30s for player {player_id}")
            await asyncio.sleep(30)  # 30 second heartbeat
            logger.debug(f"Heartbeat awake, sending ping to player {player_id}")
            try:
                await connection_manager.send_personal_message(
                    message={"type": "ping", "data": {}},
                    connection_id=connection_id,
                )
                logger.debug(f"Heartbeat ping sent to player {player_id}")
                # Note: last_seen is updated when messages are received, not here
            except Exception as e:
                logger.error(f"Heartbeat error for player {player_id}: {e}")
                break
    except asyncio.CancelledError:
        logger.info(f"Heartbeat task cancelled for player {player_id}")
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

    # Handle ping (heartbeat) - respond with pong
    if message_type == "ping":
        await connection_manager.send_personal_message(
            message={"type": "pong", "data": {}},
            connection_id=connection_id,
        )
        return

    # Handle pong (heartbeat response)
    if message_type == "pong":
        return

    # Handle leave room
    if message_type == "leave_room":
        # Get player info before leaving
        player = await player_manager.get_player_by_id(player_id)
        player_name = player.name if player else f"Player {player_id}"

        room, new_host = await room_manager.leave_room(player_id)
        await db.commit()

        # Notify others that player left
        await connection_manager.broadcast_to_room(
            message={
                "type": "player_left",
                "data": {
                    "player_id": player_id,
                    "player_name": player_name,
                },
            },
            room_code=room_code,
        )

        # If host was transferred, broadcast event
        if new_host:
            logger.info(f"Host transferred to player {new_host.id} ({new_host.name}) after leave")
            await connection_manager.broadcast_to_room(
                message={
                    "type": "host_transferred",
                    "data": {
                        "new_host_id": new_host.id,
                        "new_host_name": new_host.name,
                    },
                },
                room_code=room_code,
            )

        # Broadcast updated room state
        if room:
            # Refresh room to get updated player list after deletion
            await db.refresh(room)
            await send_room_state_to_all(room, room_code, room_manager, player_manager)

        return

    # Handle kick player (host only)
    if message_type == "kick_player":
        target_player_id = message.data.get("player_id")
        if target_player_id:
            try:
                # Get player name before kicking
                target_player = await player_manager.get_player_by_id(target_player_id)
                target_player_name = (
                    target_player.name if target_player else f"Player {target_player_id}"
                )

                await room_manager.kick_player(
                    room_id=message.data.get("room_id"),
                    player_id=target_player_id,
                    kicker_id=player_id,
                )

                # Notify room
                await connection_manager.broadcast_to_room(
                    message={
                        "type": "player_kicked",
                        "data": {
                            "player_id": target_player_id,
                            "player_name": target_player_name,
                        },
                    },
                    room_code=room_code,
                )

                # Broadcast updated room state after kick
                room = await room_manager.get_room_by_code(room_code)
                if room:
                    await send_room_state_to_all(room, room_code, room_manager, player_manager)
            except ValidationError as e:
                await connection_manager.send_error(str(e), connection_id, "FORBIDDEN")

    # Handle start game (host only)
    elif message_type == "start_game":
        game_type = message.data.get("game_type")
        # Get player
        player = await player_manager.get_player_by_id(player_id)
        if player and player.is_host:
            # Update room status
            room = await room_manager.get_room_by_id(player.room_id)
            if room and room.status == "lobby":
                try:
                    # Ensure all pending transactions are committed before creating game
                    # This is critical to ensure create_game sees all players that have joined
                    await db.commit()

                    # Create and start game instance
                    game_manager = get_game_manager()
                    game = await game_manager.create_game(db, room_code, game_type)
                    initial_state = await game_manager.start_game(room_code)

                    # Update room status
                    room.status = "playing"
                    room.current_game = game_type
                    await db.commit()

                    # Notify room - send game_started with initial state
                    await connection_manager.broadcast_to_room(
                        message={
                            "type": "game_started",
                            "data": {
                                "game_type": game_type,
                                **initial_state,
                            },
                        },
                        room_code=room_code,
                    )
                    logger.info(f"Game {game_type} started in room {room_code}")
                except Exception as e:
                    logger.error(f"Failed to start game: {e}")
                    await connection_manager.send_error(
                        f"Failed to start game: {str(e)}", connection_id, "GAME_ERROR"
                    )
        else:
            await connection_manager.send_error(
                "Only host can start game", connection_id, "FORBIDDEN"
            )

    # Handle game action (during active game)
    elif message_type == "game_action":
        try:
            game_manager = get_game_manager()
            action = message.data.get("action")
            action_data = message.data.get("data", {})

            # Handle player action in game
            response = await game_manager.handle_player_action(
                room_code, session_id, action, action_data
            )

            # Send response to player
            await connection_manager.send_personal_message(
                message={
                    "type": "game_action_response",
                    "data": response,
                },
                connection_id=connection_id,
            )

            # Broadcast game state update to all players
            display_state = await game_manager.get_state_for_display(room_code)
            await connection_manager.broadcast_to_room(
                message={
                    "type": "game_state_update",
                    "data": display_state,
                },
                room_code=room_code,
            )
        except Exception as e:
            logger.error(f"Game action error: {e}")
            await connection_manager.send_error(
                f"Game action failed: {str(e)}", connection_id, "GAME_ERROR"
            )

    # Unknown message type
    else:
        logger.warning(f"Unknown message type: {message_type}")
