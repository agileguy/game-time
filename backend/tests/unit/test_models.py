"""Unit tests for database models."""

from datetime import datetime

from app.models import GameSession, Player, Room, Score


class TestRoomModel:
    """Tests for Room model."""

    async def test_create_room(self, db_session):
        """Test creating a room."""
        room = Room(
            code="ABCD",
            status="lobby",
            max_players=12,
        )

        db_session.add(room)
        await db_session.flush()

        assert room.id is not None
        assert room.code == "ABCD"
        assert room.status == "lobby"
        assert room.is_public is True

    async def test_room_timestamps(self, db_session):
        """Test room timestamp fields."""
        room = Room(code="ABCD")
        db_session.add(room)
        await db_session.flush()

        assert isinstance(room.created_at, datetime)
        assert isinstance(room.updated_at, datetime)
        assert isinstance(room.last_activity, datetime)

    async def test_room_default_settings(self, db_session):
        """Test room default settings."""
        room = Room(code="ABCD")
        db_session.add(room)
        await db_session.flush()

        assert room.settings == {}
        assert room.max_players == 12
        assert room.is_public is True


class TestPlayerModel:
    """Tests for Player model."""

    async def test_create_player(self, db_session):
        """Test creating a player."""
        # Create room first
        room = Room(code="ABCD")
        db_session.add(room)
        await db_session.flush()

        # Create player
        player = Player(
            room_id=room.id,
            name="Alice",
            session_id="a" * 64,
        )
        db_session.add(player)
        await db_session.flush()

        assert player.id is not None
        assert player.name == "Alice"
        assert player.room_id == room.id
        assert player.connected is True
        assert player.is_host is False

    async def test_player_timestamps(self, db_session):
        """Test player timestamp fields."""
        room = Room(code="ABCD")
        db_session.add(room)
        await db_session.flush()

        player = Player(
            room_id=room.id,
            name="Alice",
            session_id="a" * 64,
        )
        db_session.add(player)
        await db_session.flush()

        assert isinstance(player.joined_at, datetime)
        assert isinstance(player.last_seen, datetime)

    async def test_player_room_relationship(self, db_session):
        """Test player-room relationship."""
        room = Room(code="ABCD")
        db_session.add(room)
        await db_session.flush()

        player = Player(
            room_id=room.id,
            name="Alice",
            session_id="a" * 64,
        )
        db_session.add(player)
        await db_session.flush()

        # Refresh to load relationships
        await db_session.refresh(room, ["players"])
        await db_session.refresh(player, ["room"])

        assert player.room == room
        assert player in room.players


class TestGameSessionModel:
    """Tests for GameSession model."""

    async def test_create_game_session(self, db_session):
        """Test creating a game session."""
        room = Room(code="ABCD")
        db_session.add(room)
        await db_session.flush()

        game_session = GameSession(
            room_id=room.id,
            game_type="trivia",
            state={"round": 1},
        )
        db_session.add(game_session)
        await db_session.flush()

        assert game_session.id is not None
        assert game_session.game_type == "trivia"
        assert game_session.state == {"round": 1}

    async def test_game_session_is_finished(self, db_session):
        """Test game session finished property."""
        room = Room(code="ABCD")
        db_session.add(room)
        await db_session.flush()

        game_session = GameSession(
            room_id=room.id,
            game_type="trivia",
        )
        db_session.add(game_session)
        await db_session.flush()

        # Not finished initially
        assert game_session.is_finished is False

        # Mark as finished
        game_session.finished_at = datetime.utcnow()
        await db_session.flush()

        assert game_session.is_finished is True

    async def test_game_session_duration(self, db_session):
        """Test game session duration calculation."""
        room = Room(code="ABCD")
        db_session.add(room)
        await db_session.flush()

        game_session = GameSession(
            room_id=room.id,
            game_type="trivia",
        )
        db_session.add(game_session)
        await db_session.flush()

        # No duration when not finished
        assert game_session.duration is None

        # Duration when finished
        game_session.finished_at = datetime.utcnow()
        await db_session.flush()

        assert game_session.duration is not None
        assert game_session.duration >= 0


class TestScoreModel:
    """Tests for Score model."""

    async def test_create_score(self, db_session):
        """Test creating a score."""
        room = Room(code="ABCD")
        db_session.add(room)
        await db_session.flush()

        player = Player(
            room_id=room.id,
            name="Alice",
            session_id="a" * 64,
        )
        db_session.add(player)
        await db_session.flush()

        game_session = GameSession(
            room_id=room.id,
            game_type="trivia",
        )
        db_session.add(game_session)
        await db_session.flush()

        score = Score(
            game_session_id=game_session.id,
            player_id=player.id,
            score=100,
            bonus_points=10,
        )
        db_session.add(score)
        await db_session.flush()

        assert score.id is not None
        assert score.score == 100
        assert score.bonus_points == 10

    async def test_score_total_score(self, db_session):
        """Test total score calculation."""
        room = Room(code="ABCD")
        db_session.add(room)
        await db_session.flush()

        player = Player(
            room_id=room.id,
            name="Alice",
            session_id="a" * 64,
        )
        db_session.add(player)
        await db_session.flush()

        game_session = GameSession(
            room_id=room.id,
            game_type="trivia",
        )
        db_session.add(game_session)
        await db_session.flush()

        score = Score(
            game_session_id=game_session.id,
            player_id=player.id,
            score=100,
            bonus_points=25,
        )
        db_session.add(score)
        await db_session.flush()

        assert score.total_score == 125

    async def test_score_round_scores(self, db_session):
        """Test round scores storage."""
        room = Room(code="ABCD")
        db_session.add(room)
        await db_session.flush()

        player = Player(
            room_id=room.id,
            name="Alice",
            session_id="a" * 64,
        )
        db_session.add(player)
        await db_session.flush()

        game_session = GameSession(
            room_id=room.id,
            game_type="trivia",
        )
        db_session.add(game_session)
        await db_session.flush()

        score = Score(
            game_session_id=game_session.id,
            player_id=player.id,
            score=300,
            round_scores=[100, 100, 100],
        )
        db_session.add(score)
        await db_session.flush()

        assert score.round_scores == [100, 100, 100]
