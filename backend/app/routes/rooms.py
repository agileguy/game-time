"""Room management HTTP endpoints."""

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RoomFullError, RoomNotFoundError, ValidationError
from app.core.rate_limit import RateLimiter
from app.database import get_db
from app.redis_client import get_redis
from app.schemas.room import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    JoinRoomResponse,
    RoomDetailResponse,
)
from app.services import PlayerManager, RoomManager

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.post("", response_model=CreateRoomResponse, status_code=201)
async def create_room(
    request: Request,
    body: CreateRoomRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Create a new game room.

    Args:
        request: HTTP request (for IP address)
        body: Room creation request
        db: Database session
        redis: Redis client
        rate_limiter: Rate limiter

    Returns:
        CreateRoomResponse: Room and session info

    Raises:
        HTTPException: If validation fails or rate limit exceeded
    """
    # Rate limit check
    client_ip = request.client.host
    rate_limiter = RateLimiter(redis)
    try:
        await rate_limiter.check_room_creation_limit(client_ip)
    except Exception as e:
        raise HTTPException(status_code=429, detail=str(e))

    # Create managers
    room_manager = RoomManager(db)
    player_manager = PlayerManager(db, redis)

    try:
        # Create session for host
        session_id = await player_manager.create_session()

        # Create room with host
        room, host = await room_manager.create_room(
            host_name=body.host_name,
            host_session_id=session_id,
            max_players=body.max_players,
            is_public=body.is_public,
        )

        await db.commit()

        return CreateRoomResponse(
            room_code=room.code,
            room_id=room.id,
            session_id=session_id,
            player_id=host.id,
            player_name=host.name,
            is_host=True,
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create room")


@router.post("/{code}/join", response_model=JoinRoomResponse)
async def join_room(
    code: str,
    body: JoinRoomRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Join an existing room.

    Args:
        code: Room code
        body: Join request
        db: Database session
        redis: Redis client

    Returns:
        JoinRoomResponse: Room and player info

    Raises:
        HTTPException: If room not found or validation fails
    """
    room_manager = RoomManager(db)
    player_manager = PlayerManager(db, redis)

    try:
        # Create session for player
        session_id = await player_manager.create_session()

        # Join room
        room, player = await room_manager.join_room(
            code=code.upper(),
            player_name=body.player_name,
            session_id=session_id,
        )

        await db.commit()

        return JoinRoomResponse(
            room_code=room.code,
            room_id=room.id,
            session_id=session_id,
            player_id=player.id,
            player_name=player.name,
            is_host=player.is_host,
        )

    except RoomNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except RoomFullError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to join room")


@router.get("/{code}", response_model=RoomDetailResponse)
async def get_room(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get room details.

    Args:
        code: Room code
        db: Database session

    Returns:
        RoomDetailResponse: Room details

    Raises:
        HTTPException: If room not found
    """
    room_manager = RoomManager(db)

    try:
        room = await room_manager.get_room_by_code(code.upper())

        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Get active players count
        active_players = await room_manager.get_active_players_count(room.id)

        return RoomDetailResponse(
            room_code=room.code,
            room_id=room.id,
            status=room.status,
            max_players=room.max_players,
            active_players=active_players,
            is_public=room.is_public,
            current_game=room.current_game,
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get room")
