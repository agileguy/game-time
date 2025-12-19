"""Game API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.game_manager import GameRegistry, get_game_manager

router = APIRouter(prefix="/api/games", tags=["games"])


class GameInfo(BaseModel):
    """Game information schema."""

    type: str
    name: str
    min_players: int
    max_players: int


class GameListResponse(BaseModel):
    """Response for listing available games."""

    games: list[GameInfo]


@router.get("", response_model=GameListResponse)
async def list_games() -> GameListResponse:
    """
    List all available game types.

    Returns:
        GameListResponse: List of available games
    """
    games = GameRegistry.list_games()
    return GameListResponse(
        games=[
            GameInfo(
                type=game["type"],
                name=game["name"],
                min_players=game["min_players"],
                max_players=game["max_players"],
            )
            for game in games
        ]
    )


class CreateGameRequest(BaseModel):
    """Request to create a new game."""

    room_code: str
    game_type: str


class CreateGameResponse(BaseModel):
    """Response after creating a game."""

    success: bool
    game_type: str
    room_code: str


@router.post("/create", response_model=CreateGameResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    request: CreateGameRequest,
    db: AsyncSession = Depends(get_db),
) -> CreateGameResponse:
    """
    Create a new game instance.

    Args:
        request: Game creation request
        db: Database session

    Returns:
        CreateGameResponse: Game creation confirmation

    Raises:
        HTTPException: If game creation fails
    """
    try:
        game_manager = get_game_manager()
        await game_manager.create_game(
            db=db,
            room_code=request.room_code,
            game_type=request.game_type,
        )

        return CreateGameResponse(
            success=True,
            game_type=request.game_type,
            room_code=request.room_code,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
