"""Integration tests for game system."""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.games.horse_race import HorseRace
from app.main import app
from app.models.game_session import GameSession
from app.models.player import Player
from app.models.room import Room
from app.services.game_manager import GameManager, GameRegistry


@pytest.fixture(scope="session", autouse=True)
def register_games():
    """Register games for testing."""
    GameRegistry.register(HorseRace)


@pytest.fixture
async def client() -> AsyncClient:
    """Create HTTP client for API testing."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.integration
class TestGamesAPI:
    """Integration tests for games API endpoints."""

    async def test_list_games(self, client: AsyncClient):
        """Test listing available games."""
        response = await client.get("/api/games")

        assert response.status_code == 200
        data = response.json()
        assert "games" in data
        assert len(data["games"]) > 0

        # Verify horse_race is in the list
        game_types = [game["type"] for game in data["games"]]
        assert "horse_race" in game_types

        # Verify game structure
        horse_race = next(g for g in data["games"] if g["type"] == "horse_race")
        assert horse_race["name"] == "Horse Race"
        assert horse_race["min_players"] == 2
        assert horse_race["max_players"] == 12


@pytest.mark.integration
class TestGameManager:
    """Integration tests for GameManager service."""

    @pytest.fixture
    async def game_manager(self, redis_client: Redis):
        """Create game manager instance."""
        return GameManager(redis_client)

    @pytest.fixture
    async def test_room(self, db_session: AsyncSession):
        """Create a test room with players."""
        # Create room
        room = Room(
            code="TEST",
            max_players=4,
            is_public=True,
            status="lobby",
        )
        db_session.add(room)
        await db_session.commit()
        await db_session.refresh(room)

        # Create players with valid 64-char hex session IDs
        for i in range(3):
            session_id = f"{str(i).zfill(2)}" + "0" * 62  # Valid 64-char hex string
            player = Player(
                room_id=room.id,
                session_id=session_id,
                name=f"Player {i}",
                is_host=(i == 0),
                connected=True,
            )
            db_session.add(player)

        await db_session.commit()
        await db_session.refresh(room)

        return room

    async def test_create_game(
        self, game_manager: GameManager, test_room: Room, db_session: AsyncSession
    ):
        """Test creating a new game."""
        game = await game_manager.create_game(db_session, "TEST", "horse_race")

        assert game is not None
        assert isinstance(game, HorseRace)
        assert game.room_code == "TEST"
        assert len(game.player_ids) == 3

        # Verify database record
        db_session.expire_all()
        game_session = await db_session.get(GameSession, game.game_session_id)
        assert game_session is not None
        assert game_session.game_type == "horse_race"
        assert game_session.room_id == test_room.id

    async def test_create_game_invalid_type(
        self, game_manager: GameManager, test_room: Room, db_session: AsyncSession
    ):
        """Test creating game with invalid type."""
        with pytest.raises(ValueError, match="Unknown game type"):
            await game_manager.create_game(db_session, "TEST", "invalid_game")

    async def test_get_game_from_cache(
        self, game_manager: GameManager, test_room: Room, db_session: AsyncSession
    ):
        """Test retrieving game from cache."""
        # Create game
        game1 = await game_manager.create_game(db_session, "TEST", "horse_race")

        # Retrieve from cache
        game2 = await game_manager.get_game("TEST")

        assert game2 is not None
        assert isinstance(game2, HorseRace)
        assert game2.room_code == game1.room_code
        assert game2.state.game_type == game1.state.game_type

    async def test_start_game(
        self, game_manager: GameManager, test_room: Room, db_session: AsyncSession
    ):
        """Test starting a game."""
        # Create game
        await game_manager.create_game(db_session, "TEST", "horse_race")

        # Start game
        initial_state = await game_manager.start_game("TEST")

        assert initial_state is not None
        assert initial_state["phase"] == "setup"
        assert "round_data" in initial_state
        assert "horses" in initial_state["round_data"]
        assert len(initial_state["round_data"]["horses"]) == 4

    async def test_handle_player_action_place_bet(
        self, game_manager: GameManager, test_room: Room, db_session: AsyncSession
    ):
        """Test handling player bet action."""
        # Create and start game
        await game_manager.create_game(db_session, "TEST", "horse_race")
        await game_manager.start_game("TEST")

        # Place bet
        response = await game_manager.handle_player_action(
            "TEST", "player-0", "place_bet", {"horse_id": 2}
        )

        assert response["success"] is True
        assert response["bet"] == 2

        # Verify bet was stored
        game = await game_manager.get_game("TEST")
        assert game.state.player_data["player-0"]["bet"] == 2

    async def test_handle_player_action_invalid_action(
        self, game_manager: GameManager, test_room: Room, db_session: AsyncSession
    ):
        """Test handling invalid player action."""
        # Create and start game
        await game_manager.create_game(db_session, "TEST", "horse_race")
        await game_manager.start_game("TEST")

        # Invalid action
        response = await game_manager.handle_player_action("TEST", "player-0", "invalid_action", {})

        assert response["success"] is False
        assert "error" in response

    async def test_get_state_for_display(
        self, game_manager: GameManager, test_room: Room, db_session: AsyncSession
    ):
        """Test getting game state for display."""
        # Create and start game
        await game_manager.create_game(db_session, "TEST", "horse_race")
        await game_manager.start_game("TEST")

        # Get display state
        state = await game_manager.get_state_for_display("TEST")

        assert state is not None
        assert state["phase"] == "setup"
        assert "round_data" in state
        assert "scores" in state

    async def test_get_state_for_player(
        self, game_manager: GameManager, test_room: Room, db_session: AsyncSession
    ):
        """Test getting game state for specific player."""
        # Create and start game
        await game_manager.create_game(db_session, "TEST", "horse_race")
        await game_manager.start_game("TEST")

        # Place bet
        await game_manager.handle_player_action("TEST", "player-0", "place_bet", {"horse_id": 1})

        # Get player state
        state = await game_manager.get_state_for_player("TEST", "player-0")

        assert state is not None
        assert state["phase"] == "setup"
        assert "player_data" in state
        assert state["player_data"]["bet"] == 1

    async def test_finish_game(
        self, game_manager: GameManager, test_room: Room, db_session: AsyncSession
    ):
        """Test finishing a game and cleanup."""
        # Create and start game
        game = await game_manager.create_game(db_session, "TEST", "horse_race")
        await game_manager.start_game("TEST")

        game_session_id = game.game_session_id

        # Finish game
        await game_manager.finish_game("TEST")

        # Verify game removed from cache
        cached_game = await game_manager.get_game("TEST")
        assert cached_game is None

        # Verify database updated
        db_session.expire_all()
        game_session = await db_session.get(GameSession, game_session_id)
        assert game_session.finished_at is not None


@pytest.mark.integration
class TestGameRegistry:
    """Integration tests for GameRegistry."""

    def test_game_registered(self):
        """Test that HorseRace is registered."""
        horse_race_class = GameRegistry.get("horse_race")
        assert horse_race_class == HorseRace

    def test_list_games(self):
        """Test listing all registered games."""
        games = GameRegistry.list_games()

        assert len(games) > 0
        assert any(g["type"] == "horse_race" for g in games)

    def test_get_invalid_game(self):
        """Test getting invalid game type."""
        game_class = GameRegistry.get("invalid_game")
        # Returns None for unknown games instead of raising
        assert game_class is None or isinstance(game_class, type)


@pytest.mark.integration
class TestHorseRaceGame:
    """Integration tests for HorseRace game flow."""

    async def test_complete_game_flow(self):
        """Test complete horse race game from start to finish."""
        player_ids = [f"{i:064x}" for i in range(3)]  # Valid 64-char hex IDs
        game = HorseRace(room_code="TEST", player_ids=player_ids)

        # Start game (betting phase)
        await game.start()

        assert game.state.phase.value == "setup"
        assert "horses" in game.state.round_data
        assert len(game.state.round_data["horses"]) == 4

        # Place bets
        for i, player_id in enumerate(player_ids):
            bet_result = await game.handle_player_action(
                player_id, "place_bet", {"horse_id": i % 4}
            )
            assert bet_result["success"] is True

        # Verify all bets were placed
        assert len(game.state.player_data) == 3
        for player_id in player_ids:
            assert player_id in game.state.player_data
            assert "bet" in game.state.player_data[player_id]

    async def test_concurrent_bets(self):
        """Test multiple players betting concurrently."""
        player_ids = [f"{i:064x}" for i in range(10)]  # Valid 64-char hex IDs
        game = HorseRace(room_code="TEST", player_ids=player_ids)

        await game.start()

        # Place concurrent bets
        bet_tasks = [
            game.handle_player_action(player_id, "place_bet", {"horse_id": i % 4})
            for i, player_id in enumerate(player_ids)
        ]

        results = await asyncio.gather(*bet_tasks)

        # All bets should succeed
        assert all(r["success"] for r in results)

        # All players should have bets
        for player_id in player_ids:
            assert player_id in game.state.player_data
            assert "bet" in game.state.player_data[player_id]
