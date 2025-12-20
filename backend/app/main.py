"""Main FastAPI application entry point."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import to register game manager
import app.services.game_manager as game_manager_module
from app.config import settings
from app.core.logging import get_logger
from app.database import close_db, init_db
from app.games.horse_race import HorseRace
from app.redis_client import redis_client
from app.routes import games, health, rooms, websocket
from app.services.game_manager import GameManager, GameRegistry

logger = get_logger()

# Global task for game state broadcaster
_broadcaster_task: asyncio.Task | None = None


async def broadcast_game_states():
    """Periodically broadcast game state updates for active games."""
    from app.services.game_manager import get_game_manager

    # Wait a bit for everything to initialize
    await asyncio.sleep(2)

    logger.info("Game state broadcaster started")

    try:
        while True:
            await asyncio.sleep(1)  # Broadcast every second

            try:
                # Import here to avoid issues with initialization order
                from app.services.websocket_manager import connection_manager

                if connection_manager is None:
                    continue

                game_manager = get_game_manager()

                # Get all active games
                for room_code in list(game_manager._active_games.keys()):
                    try:
                        # Get all connection IDs for this room
                        connection_ids = connection_manager.room_connections.get(room_code, [])

                        for connection_id in connection_ids:
                            try:
                                # Find session_id for this connection_id (reverse lookup)
                                session_id = None
                                for sid, cid in connection_manager.session_connections.items():
                                    if cid == connection_id:
                                        session_id = sid
                                        break

                                if not session_id:
                                    logger.debug(
                                        f"No session_id found for connection {connection_id}"
                                    )
                                    continue

                                # Get player-specific state
                                try:
                                    player_state = await game_manager.get_state_for_player(
                                        room_code, session_id
                                    )

                                    # Validate state has required fields
                                    if not player_state or "horses" not in player_state:
                                        logger.warning(
                                            f"Invalid player state for {session_id} in room {room_code}: {player_state}"
                                        )
                                        continue

                                    # Send to this specific player
                                    await connection_manager.send_personal_message(
                                        message={
                                            "type": "game_state_update",
                                            "data": player_state,
                                        },
                                        connection_id=connection_id,
                                    )
                                except Exception as state_error:
                                    logger.warning(
                                        f"Error getting state for player {session_id}: {state_error}"
                                    )
                                    # Don't send update if we can't get valid state
                                    continue

                            except Exception as e:
                                logger.debug(f"Error broadcasting to {connection_id}: {e}")

                    except Exception as e:
                        logger.debug(f"Error broadcasting state for room {room_code}: {e}")

            except Exception as e:
                logger.error(f"Error in game state broadcaster: {e}", exc_info=True)

    except asyncio.CancelledError:
        logger.info("Game state broadcaster stopped")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    global _broadcaster_task

    # Startup
    await init_db()
    await redis_client.connect()

    # Initialize game manager
    game_manager_module.game_manager = GameManager(redis_client.client)

    # Register games
    GameRegistry.register(HorseRace)

    # Start game state broadcaster
    _broadcaster_task = asyncio.create_task(broadcast_game_states())
    logger.info(f"Created broadcaster task: {_broadcaster_task}")

    yield

    # Shutdown
    if _broadcaster_task:
        _broadcaster_task.cancel()
        try:
            await _broadcaster_task
        except asyncio.CancelledError:
            pass

    await close_db()
    await redis_client.disconnect()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Multiplayer party game platform with dual-screen experience",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(rooms.router)
app.include_router(games.router)
app.include_router(websocket.router)


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """
    Root endpoint.

    Returns:
        JSONResponse: API information
    """
    return JSONResponse(
        content={
            "name": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }
    )
