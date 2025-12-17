# Testing Guide

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Quick Start](#quick-start)
3. [Testing Infrastructure](#testing-infrastructure)
4. [Unit Testing](#unit-testing)
5. [Integration Testing](#integration-testing)
6. [End-to-End Testing](#end-to-end-testing)
7. [Load & Performance Testing](#load--performance-testing)
8. [Security Testing](#security-testing)
9. [Test Execution](#test-execution)
10. [CI/CD Integration](#cicd-integration)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

## Testing Philosophy

### The Testing Pyramid

We follow the testing pyramid approach to maintain fast, reliable, and maintainable tests:

```
        /\
       /  \
      / E2E \       ← Few (Slow, Expensive, Brittle)
     /______\
    /        \
   /Integration\   ← Some (Medium Speed, Medium Cost)
  /____________\
 /              \
/   Unit Tests   \  ← Many (Fast, Cheap, Stable)
/__________________\
```

**Ratio Target**: 70% Unit | 20% Integration | 10% E2E

### Test Coverage Goals

| Component | Target | Rationale |
|-----------|--------|-----------|
| Overall | 80%+ | Industry best practice |
| Business Logic | 95%+ | Critical path coverage |
| Game Rules | 100% | Zero tolerance for bugs |
| Security Functions | 95%+ | Critical for user safety |
| Frontend (Vanilla JS) | 60%+ | Challenging without build tools |

### When to Write Which Test

**Write Unit Tests when:**
- Testing pure functions
- Testing business logic in isolation
- Testing edge cases and error handling
- Validating data transformations
- Testing utility functions

**Write Integration Tests when:**
- Testing API endpoints
- Testing database operations
- Testing service layer interactions
- Testing external dependencies (Redis, etc.)
- Testing WebSocket communication

**Write E2E Tests when:**
- Testing critical user journeys
- Testing multi-component workflows
- Testing real browser interactions
- Validating full system integration
- Testing responsive behavior

### Test-Driven Development (TDD)

We encourage TDD for new features:

1. **Red**: Write a failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve code while keeping tests green

**Benefits:**
- Better design through testable code
- Immediate feedback loop
- Living documentation
- Regression protection from day one

## Quick Start

### Run All Tests (Docker)

```bash
# One command to rule them all
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# View coverage report
open htmlcov/index.html
```

### Run Specific Test Suite

```bash
# Unit tests only (fast)
docker-compose -f docker-compose.test.yml run --rm backend pytest tests/unit -v

# Integration tests
docker-compose -f docker-compose.test.yml run --rm backend pytest tests/integration -v

# E2E tests
docker-compose -f docker-compose.test.yml run --rm playwright npm test

# Load tests
docker-compose -f docker-compose.test.yml run --rm locust
```

### Run Tests Locally (without Docker)

```bash
# Backend tests
cd backend
source venv/bin/activate
pytest tests/unit -v
pytest tests/integration -v
pytest --cov=app --cov-report=html

# Frontend tests (if using)
cd ../frontend
npm test

# E2E tests
cd ../tests/e2e
npx playwright test
```

## Testing Infrastructure

### Directory Structure

```
game-time/
├── backend/
│   └── app/
│       └── tests/           # Backend tests live here (pytest convention)
│           ├── conftest.py
│           ├── pytest.ini
│           ├── unit/
│           ├── integration/
│           ├── security/
│           └── fixtures/
│
├── tests/
│   ├── docker-compose.test.yml
│   │
│   ├── e2e/                 # End-to-end browser tests
│   │   ├── Dockerfile.playwright
│   │   ├── playwright.config.ts
│   │   ├── package.json
│   │   ├── pages/           # Page Object Model
│   │   │   ├── display/
│   │   │   └── controller/
│   │   ├── tests/
│   │   └── fixtures/
│   │
│   └── load/                # Load testing
│       ├── locustfile.py
│       ├── websocket_load.py
│       └── scenarios/
│
└── TESTING.md
```

### Docker Test Environment

**docker-compose.test.yml**

```yaml
version: '3.8'

services:
  # PostgreSQL test database (in-memory for speed)
  test-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: gametime_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    tmpfs:
      - /var/lib/postgresql/data  # In-memory for speed
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d gametime_test"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis test instance
  test-redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # Backend test runner
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.test
    depends_on:
      test-db:
        condition: service_healthy
      test-redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://test_user:test_pass@test-db/gametime_test
      REDIS_URL: redis://test-redis:6379/0
      TESTING: "true"
      SECRET_KEY: test-secret-key-do-not-use-in-production
    volumes:
      - ./backend:/app
      - test-coverage:/coverage
    command: >
      sh -c "
        alembic upgrade head &&
        python scripts/seed_trivia.py --test &&
        pytest tests/
          --cov=app
          --cov-report=html:/coverage
          --cov-report=term
          --cov-fail-under=80
          -v
      "

  # Playwright E2E test runner
  playwright:
    build:
      context: ./tests/e2e
      dockerfile: Dockerfile.playwright
    depends_on:
      backend:
        condition: service_completed_successfully
    environment:
      BASE_URL: http://backend:8000
    volumes:
      - ./tests/e2e:/tests
      - test-results:/results
      - playwright-screenshots:/screenshots
    command: npx playwright test --reporter=html

  # Locust load testing
  locust:
    image: locustio/locust:latest
    depends_on:
      backend:
        condition: service_completed_successfully
    ports:
      - "8089:8089"
    volumes:
      - ./tests/load:/locust
    command: -f /locust/locustfile.py --host=http://backend:8000

volumes:
  test-coverage:
  test-results:
  playwright-screenshots:
```

### Backend Test Dockerfile

**backend/Dockerfile.test**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/base.txt requirements/dev.txt ./requirements/
RUN pip install --no-cache-dir -r requirements/dev.txt

# Copy application code
COPY . .

# Install the app in development mode
RUN pip install -e .

CMD ["pytest"]
```

### Playwright Dockerfile

**tests/e2e/Dockerfile.playwright**

```dockerfile
FROM mcr.microsoft.com/playwright:v1.40.0-focal

WORKDIR /tests

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Install Playwright browsers
RUN npx playwright install --with-deps chromium firefox webkit

# Copy test files
COPY . .

CMD ["npx", "playwright", "test"]
```

## Unit Testing

### Backend Unit Tests

#### Pytest Configuration

**backend/tests/pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts =
    -v
    --strict-markers
    --tb=short
    --cov-branch
    --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    security: Security tests
filterwarnings =
    error
    ignore::DeprecationWarning
```

#### Shared Fixtures

**backend/tests/conftest.py**

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.config import settings


# Database fixtures
@pytest_asyncio.fixture
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create a test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """Create a test HTTP client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Redis fixtures
@pytest_asyncio.fixture
async def redis_client():
    """Create a test Redis client."""
    import redis.asyncio as aioredis

    client = await aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )

    yield client

    await client.flushdb()
    await client.close()


# Test data fixtures
@pytest.fixture
def sample_room_data():
    """Sample room creation data."""
    return {
        "code": "TEST",
        "host_player_id": None,
        "max_players": 12,
    }


@pytest.fixture
def sample_player_data():
    """Sample player data."""
    return {
        "name": "TestPlayer",
        "session_id": "a" * 64,  # 64-char hex string
    }
```

#### Test Factories

**backend/tests/fixtures/factories.py**

```python
import factory
from factory import Faker, SubFactory
from app.models import Room, Player, GameSession, Score


class RoomFactory(factory.Factory):
    class Meta:
        model = Room

    code = Faker('lexify', text='????', letters='ABCDEFGHJKMNPQRSTUVWXYZ23456789')
    status = 'lobby'
    max_players = 12
    is_public = True


class PlayerFactory(factory.Factory):
    class Meta:
        model = Player

    name = Faker('first_name')
    session_id = Faker('sha256')
    is_host = False
    connected = True
    room = SubFactory(RoomFactory)


class GameSessionFactory(factory.Factory):
    class Meta:
        model = GameSession

    game_type = 'horse_race'
    state = {}
    room = SubFactory(RoomFactory)


class ScoreFactory(factory.Factory):
    class Meta:
        model = Score

    score = Faker('pyint', min_value=0, max_value=1000)
    game_session = SubFactory(GameSessionFactory)
    player = SubFactory(PlayerFactory)
```

#### Example Unit Tests

**backend/tests/unit/test_room_code_generator.py**

```python
import pytest
from app.utils.room_code import generate_room_code, is_valid_room_code


class TestRoomCodeGeneration:
    """Tests for room code generation and validation."""

    def test_generate_room_code_length(self):
        """Room code should be 4-6 characters."""
        code = generate_room_code()
        assert 4 <= len(code) <= 6

    def test_generate_room_code_format(self):
        """Room code should only contain valid characters."""
        code = generate_room_code()
        valid_chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
        assert all(c in valid_chars for c in code)

    def test_generate_room_code_no_ambiguous_chars(self):
        """Room code should not contain ambiguous characters."""
        code = generate_room_code()
        ambiguous = '0O1IL'
        assert not any(c in code for c in ambiguous)

    def test_generate_room_code_uniqueness(self):
        """Generated codes should be reasonably unique."""
        codes = {generate_room_code() for _ in range(1000)}
        # Should have at least 900 unique codes out of 1000
        assert len(codes) > 900

    @pytest.mark.parametrize("code,expected", [
        ("ABCD", True),
        ("XY7Z", True),
        ("12345", True),
        ("ABC", False),      # Too short
        ("ABCDEFG", False),  # Too long
        ("AB0D", False),     # Contains 0
        ("ABIL", False),     # Contains I and L
        ("ab cd", False),    # Lowercase and space
    ])
    def test_room_code_validation(self, code, expected):
        """Test room code validation rules."""
        assert is_valid_room_code(code) == expected


**backend/tests/unit/test_games/test_horse_race.py**

```python
import pytest
from app.games.horse_race import HorseRaceGame


class TestHorseRaceGame:
    """Tests for horse race game logic."""

    @pytest.fixture
    def game(self):
        """Create a horse race game instance."""
        return HorseRaceGame(
            room_id=1,
            players=[{"id": 1, "name": "Player1"}],
            config={"num_horses": 6, "track_length": 100}
        )

    def test_game_initialization(self, game):
        """Game should initialize with correct state."""
        assert game.num_horses == 6
        assert len(game.horses) == 6
        assert all(pos == 0 for pos in game.horse_positions.values())
        assert game.phase == "betting"

    def test_place_bet_valid(self, game):
        """Valid bet should be accepted."""
        result = game.place_bet(player_id=1, horse_number=3)
        assert result["success"] is True
        assert game.bets[1] == 3

    def test_place_bet_invalid_horse(self, game):
        """Bet on invalid horse should fail."""
        result = game.place_bet(player_id=1, horse_number=10)
        assert result["success"] is False
        assert "invalid" in result["error"].lower()

    def test_place_bet_after_betting_closes(self, game):
        """Bet after betting phase should fail."""
        game.phase = "racing"
        result = game.place_bet(player_id=1, horse_number=3)
        assert result["success"] is False

    def test_race_tick_movement(self, game):
        """Horses should move forward during race."""
        game.phase = "racing"
        initial_positions = game.horse_positions.copy()

        game.tick_race()

        # At least some horses should have moved
        assert any(
            game.horse_positions[h] > initial_positions[h]
            for h in range(game.num_horses)
        )

    def test_race_tick_random_movement(self, game):
        """Horse movement should be random (within bounds)."""
        game.phase = "racing"

        movements = []
        for _ in range(100):
            before = game.horse_positions[0]
            game.tick_race()
            after = game.horse_positions[0]
            movements.append(after - before)

        # Should have variety in movement (0-3 units)
        assert set(movements) <= {0, 1, 2, 3}
        assert len(set(movements)) > 1  # Not all the same

    def test_race_finish_detection(self, game):
        """Race should detect when horse finishes."""
        game.phase = "racing"
        game.horse_positions[0] = 100

        winner = game.check_winner()
        assert winner == 0
        assert game.phase == "finished"

    def test_score_calculation_winner(self, game):
        """Winning bet should award full points."""
        game.place_bet(player_id=1, horse_number=0)
        game.horse_positions[0] = 100
        game.phase = "finished"

        scores = game.calculate_scores()
        assert scores[1] == 100

    def test_score_calculation_no_bet(self, game):
        """No bet should award no points."""
        game.horse_positions[0] = 100
        game.phase = "finished"

        scores = game.calculate_scores()
        assert scores.get(1, 0) == 0
```

**backend/tests/unit/test_validators.py**

```python
import pytest
from pydantic import ValidationError
from app.schemas.player import PlayerCreate
from app.schemas.room import RoomCreate


class TestPlayerValidation:
    """Tests for player data validation."""

    def test_valid_player_name(self):
        """Valid player name should pass validation."""
        player = PlayerCreate(name="Alice")
        assert player.name == "Alice"

    @pytest.mark.parametrize("name", [
        "",           # Empty
        " ",          # Whitespace only
        "A" * 51,     # Too long
    ])
    def test_invalid_player_name(self, name):
        """Invalid player names should fail validation."""
        with pytest.raises(ValidationError):
            PlayerCreate(name=name)

    def test_player_name_sanitization(self):
        """Player name should be sanitized."""
        player = PlayerCreate(name="  Alice  ")
        assert player.name == "Alice"  # Whitespace trimmed

    def test_player_name_html_escaping(self):
        """Player name should escape HTML."""
        player = PlayerCreate(name="<script>alert('xss')</script>")
        # Should be escaped or rejected
        assert "<script>" not in player.name


class TestWebSocketMessageValidation:
    """Tests for WebSocket message validation."""

    def test_valid_message_schema(self):
        """Valid WebSocket message should pass validation."""
        from app.schemas.websocket import WebSocketMessage

        msg = WebSocketMessage(
            type="join_room",
            data={"code": "ABCD"},
            timestamp=1234567890
        )
        assert msg.type == "join_room"

    def test_invalid_message_type(self):
        """Invalid message type should fail validation."""
        from app.schemas.websocket import WebSocketMessage

        with pytest.raises(ValidationError):
            WebSocketMessage(
                type="invalid_type",
                data={},
                timestamp=1234567890
            )

    def test_message_size_limit(self):
        """Message data should have size limit."""
        from app.schemas.websocket import WebSocketMessage

        large_data = {"key": "x" * 100000}  # >10KB
        with pytest.raises(ValidationError):
            WebSocketMessage(
                type="player_action",
                data=large_data,
                timestamp=1234567890
            )
```

### Frontend Unit Tests (JavaScript)

While we use vanilla JavaScript (no build step), we can still write unit tests using a simple test runner like Jest or Mocha.

**frontend/tests/websocket-client.test.js**

```javascript
// Using Jest
import { WebSocketClient } from '../shared/js/websocket-client.js';

describe('WebSocketClient', () => {
  let client;
  let mockWs;

  beforeEach(() => {
    mockWs = {
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    };

    global.WebSocket = jest.fn(() => mockWs);
    client = new WebSocketClient('ws://localhost:8000/ws/test');
  });

  test('connects to WebSocket server', () => {
    expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws/test');
  });

  test('sends message with correct format', () => {
    client.send('test_event', { foo: 'bar' });

    expect(mockWs.send).toHaveBeenCalled();
    const sentData = JSON.parse(mockWs.send.mock.calls[0][0]);

    expect(sentData.type).toBe('test_event');
    expect(sentData.data).toEqual({ foo: 'bar' });
    expect(sentData.timestamp).toBeDefined();
  });

  test('handles reconnection on disconnect', (done) => {
    client.autoReconnect = true;

    // Simulate disconnect
    const disconnectHandler = mockWs.addEventListener.mock.calls
      .find(call => call[0] === 'close')[1];

    disconnectHandler();

    setTimeout(() => {
      expect(global.WebSocket).toHaveBeenCalledTimes(2);
      done();
    }, 1100); // After reconnect delay
  });

  test('validates message schema before sending', () => {
    expect(() => {
      client.send('', {});  // Empty type
    }).toThrow();
  });
});
```

## Integration Testing

### API Endpoint Tests

**backend/tests/integration/test_api_rooms.py**

```python
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestRoomAPI:
    """Integration tests for room API endpoints."""

    @pytest.mark.asyncio
    async def test_create_room(self, client: AsyncClient):
        """POST /api/rooms should create a new room."""
        response = await client.post("/api/rooms")

        assert response.status_code == 201
        data = response.json()
        assert "code" in data
        assert "created_at" in data
        assert data["status"] == "lobby"

    @pytest.mark.asyncio
    async def test_get_room_by_code(self, client: AsyncClient, db_session):
        """GET /api/rooms/{code} should return room details."""
        # Create a room first
        create_response = await client.post("/api/rooms")
        room_code = create_response.json()["code"]

        # Get the room
        response = await client.get(f"/api/rooms/{room_code}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == room_code

    @pytest.mark.asyncio
    async def test_get_nonexistent_room(self, client: AsyncClient):
        """GET /api/rooms/{code} should return 404 for nonexistent room."""
        response = await client.get("/api/rooms/XXXX")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_join_room(self, client: AsyncClient):
        """POST /api/rooms/{code}/join should add player to room."""
        # Create room
        create_response = await client.post("/api/rooms")
        room_code = create_response.json()["code"]

        # Join room
        response = await client.post(
            f"/api/rooms/{room_code}/join",
            json={"name": "TestPlayer"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["player"]["name"] == "TestPlayer"
        assert "session_id" in data

    @pytest.mark.asyncio
    async def test_join_full_room(self, client: AsyncClient, db_session):
        """Cannot join room at max capacity."""
        # Create room with max_players=2
        # Add 2 players
        # Try to add 3rd player
        # Should fail with 403
        pass  # Implementation left as exercise


### WebSocket Integration Tests

**backend/tests/integration/test_websocket.py**

```python
import pytest
import websockets
import json
from httpx import AsyncClient


@pytest.mark.integration
class TestWebSocketCommunication:
    """Integration tests for WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, client: AsyncClient):
        """WebSocket connection should be established."""
        # Create session
        response = await client.post("/api/sessions")
        session_id = response.json()["session_id"]

        # Connect WebSocket
        async with websockets.connect(
            f"ws://localhost:8000/ws/{session_id}"
        ) as websocket:
            # Should receive connected message
            message = await websocket.recv()
            data = json.loads(message)
            assert data["type"] == "connected"

    @pytest.mark.asyncio
    async def test_join_room_via_websocket(self, client: AsyncClient):
        """Player should be able to join room via WebSocket."""
        # Create room
        room_response = await client.post("/api/rooms")
        room_code = room_response.json()["code"]

        # Create session
        session_response = await client.post("/api/sessions")
        session_id = session_response.json()["session_id"]

        # Connect and join
        async with websockets.connect(
            f"ws://localhost:8000/ws/{session_id}"
        ) as websocket:
            # Send join_room message
            await websocket.send(json.dumps({
                "type": "join_room",
                "data": {"code": room_code, "name": "TestPlayer"},
                "timestamp": 1234567890
            }))

            # Should receive player_joined confirmation
            message = await websocket.recv()
            data = json.loads(message)
            assert data["type"] == "player_joined"
            assert data["data"]["name"] == "TestPlayer"

    @pytest.mark.asyncio
    async def test_broadcast_to_room(self, client: AsyncClient):
        """Message should be broadcast to all players in room."""
        # Create room
        room_response = await client.post("/api/rooms")
        room_code = room_response.json()["code"]

        # Create 2 sessions
        session1_resp = await client.post("/api/sessions")
        session2_resp = await client.post("/api/sessions")
        session1_id = session1_resp.json()["session_id"]
        session2_id = session2_resp.json()["session_id"]

        # Connect both players
        async with websockets.connect(
            f"ws://localhost:8000/ws/{session1_id}"
        ) as ws1, websockets.connect(
            f"ws://localhost:8000/ws/{session2_id}"
        ) as ws2:
            # Both join room
            for ws, name in [(ws1, "Player1"), (ws2, "Player2")]:
                await ws.send(json.dumps({
                    "type": "join_room",
                    "data": {"code": room_code, "name": name},
                    "timestamp": 1234567890
                }))
                await ws.recv()  # Consume join confirmation

            # Player 2 should receive broadcast when Player 1 joins
            message = await ws2.recv()
            data = json.loads(message)
            assert data["type"] == "player_joined"
            assert data["data"]["name"] == "Player1"

    @pytest.mark.asyncio
    async def test_websocket_rate_limiting(self, client: AsyncClient):
        """WebSocket should enforce rate limiting."""
        session_resp = await client.post("/api/sessions")
        session_id = session_resp.json()["session_id"]

        async with websockets.connect(
            f"ws://localhost:8000/ws/{session_id}"
        ) as websocket:
            # Send 100 messages rapidly (exceeds 60/min limit)
            for i in range(100):
                await websocket.send(json.dumps({
                    "type": "ping",
                    "data": {},
                    "timestamp": 1234567890 + i
                }))

            # Should receive rate limit error
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                if data["type"] == "error":
                    assert "rate limit" in data["data"]["message"].lower()
                    break
```

### Database Integration Tests

**backend/tests/integration/test_database.py**

```python
import pytest
from sqlalchemy import select
from app.models import Room, Player


@pytest.mark.integration
class TestDatabaseOperations:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    async def test_create_room(self, db_session):
        """Should create room in database."""
        room = Room(code="TEST", status="lobby")
        db_session.add(room)
        await db_session.commit()

        # Verify in database
        result = await db_session.execute(
            select(Room).where(Room.code == "TEST")
        )
        saved_room = result.scalar_one()
        assert saved_room.code == "TEST"
        assert saved_room.status == "lobby"

    @pytest.mark.asyncio
    async def test_cascade_delete_players(self, db_session):
        """Deleting room should cascade delete players."""
        # Create room with players
        room = Room(code="TEST")
        player1 = Player(name="Player1", session_id="a"*64, room=room)
        player2 = Player(name="Player2", session_id="b"*64, room=room)

        db_session.add_all([room, player1, player2])
        await db_session.commit()
        room_id = room.id

        # Delete room
        await db_session.delete(room)
        await db_session.commit()

        # Players should be deleted
        result = await db_session.execute(
            select(Player).where(Player.room_id == room_id)
        )
        assert result.first() is None

    @pytest.mark.asyncio
    async def test_unique_constraint_room_code(self, db_session):
        """Room code should be unique."""
        room1 = Room(code="TEST")
        db_session.add(room1)
        await db_session.commit()

        # Try to create duplicate
        room2 = Room(code="TEST")
        db_session.add(room2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()
```

## End-to-End Testing

### Playwright Configuration

**tests/e2e/playwright.config.ts**

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: '/results/html' }],
    ['junit', { outputFile: '/results/junit.xml' }],
    ['list'],
  ],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 13'] },
    },
  ],

  webServer: {
    command: 'uvicorn app.main:app --host 0.0.0.0 --port 8000',
    port: 8000,
    reuseExistingServer: !process.env.CI,
  },
});
```

### Page Object Model

**tests/e2e/pages/display/lobby.page.ts**

```typescript
import { Page, Locator } from '@playwright/test';

export class DisplayLobbyPage {
  readonly page: Page;
  readonly roomCode: Locator;
  readonly playerList: Locator;
  readonly startGameButton: Locator;
  readonly gameSelectButtons: Locator;

  constructor(page: Page) {
    this.page = page;
    this.roomCode = page.locator('.room-code');
    this.playerList = page.locator('.player-list');
    this.startGameButton = page.locator('button:text("Start Game")');
    this.gameSelectButtons = page.locator('.game-select button');
  }

  async goto() {
    await this.page.goto('/display');
  }

  async createRoom(): Promise<string> {
    await this.page.click('button:text("Create Room")');
    await this.roomCode.waitFor({ state: 'visible' });
    return await this.roomCode.textContent() || '';
  }

  async getPlayerNames(): Promise<string[]> {
    const players = await this.playerList.locator('.player-name').all();
    return await Promise.all(players.map(p => p.textContent()));
  }

  async selectGame(gameName: string) {
    await this.page.click(`button:text("${gameName}")`);
  }

  async startGame() {
    await this.startGameButton.click();
  }
}
```

**tests/e2e/pages/controller/join.page.ts**

```typescript
import { Page, Locator } from '@playwright/test';

export class ControllerJoinPage {
  readonly page: Page;
  readonly roomCodeInput: Locator;
  readonly playerNameInput: Locator;
  readonly joinButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.roomCodeInput = page.locator('#room-code');
    this.playerNameInput = page.locator('#player-name');
    this.joinButton = page.locator('button:text("Join")');
  }

  async goto() {
    await this.page.goto('/controller');
  }

  async joinRoom(roomCode: string, playerName: string) {
    await this.roomCodeInput.fill(roomCode);
    await this.playerNameInput.fill(playerName);
    await this.joinButton.click();
  }
}
```

### E2E Test Examples

**tests/e2e/tests/full_game_flow.spec.ts**

```typescript
import { test, expect } from '@playwright/test';
import { DisplayLobbyPage } from '../pages/display/lobby.page';
import { ControllerJoinPage } from '../pages/controller/join.page';

test.describe('Complete Horse Race Game Flow', () => {
  test('should complete full game from room creation to results', async ({ browser }) => {
    // Create browser contexts for display and 4 players
    const displayContext = await browser.newContext();
    const player1Context = await browser.newContext();
    const player2Context = await browser.newContext();
    const player3Context = await browser.newContext();
    const player4Context = await browser.newContext();

    const displayPage = await displayContext.newPage();
    const player1Page = await player1Context.newPage();
    const player2Page = await player2Context.newPage();
    const player3Page = await player3Context.newPage();
    const player4Page = await player4Context.newPage();

    // Step 1: Display creates room
    const displayLobby = new DisplayLobbyPage(displayPage);
    await displayLobby.goto();
    const roomCode = await displayLobby.createRoom();
    expect(roomCode).toMatch(/^[A-Z0-9]{4,6}$/);

    // Step 2: Players join
    const players = [
      { page: player1Page, name: 'Alice' },
      { page: player2Page, name: 'Bob' },
      { page: player3Page, name: 'Charlie' },
      { page: player4Page, name: 'Diana' },
    ];

    for (const player of players) {
      const joinPage = new ControllerJoinPage(player.page);
      await joinPage.goto();
      await joinPage.joinRoom(roomCode, player.name);

      // Verify joined successfully
      await expect(player.page.locator('.lobby-screen')).toBeVisible();
    }

    // Step 3: Verify all players visible on display
    const playerNames = await displayLobby.getPlayerNames();
    expect(playerNames).toHaveLength(4);
    expect(playerNames).toContain('Alice');
    expect(playerNames).toContain('Bob');
    expect(playerNames).toContain('Charlie');
    expect(playerNames).toContain('Diana');

    // Step 4: Host selects Horse Race
    await displayLobby.selectGame('Horse Race');
    await displayPage.waitForTimeout(500); // UI animation

    // Step 5: Host starts game
    await displayLobby.startGame();

    // Step 6: Betting phase - players place bets
    for (const player of players) {
      await expect(player.page.locator('.betting-screen')).toBeVisible();
      await player.page.click('.horse-button[data-horse="3"]'); // All bet on horse 3
      await expect(player.page.locator('.bet-placed')).toBeVisible();
    }

    // Step 7: Wait for race to finish
    await displayPage.waitForSelector('.race-finished', { timeout: 30000 });

    // Step 8: Verify results screen
    await expect(displayPage.locator('.results-screen')).toBeVisible();
    await expect(displayPage.locator('.final-scores')).toBeVisible();

    // Step 9: Verify scores were calculated
    const scores = await displayPage.locator('.player-score').all();
    expect(scores.length).toBe(4);

    // Cleanup
    await displayContext.close();
    await player1Context.close();
    await player2Context.close();
    await player3Context.close();
    await player4Context.close();
  });
});
```

**tests/e2e/tests/reconnection.spec.ts**

```typescript
import { test, expect } from '@playwright/test';

test.describe('Reconnection Handling', () => {
  test('should reconnect player after network interruption', async ({ page, context }) => {
    // Join a game
    await page.goto('/controller');
    await page.fill('#room-code', 'TEST');
    await page.fill('#player-name', 'TestPlayer');
    await page.click('button:text("Join")');

    await expect(page.locator('.lobby-screen')).toBeVisible();

    // Simulate network offline
    await context.setOffline(true);
    await page.waitForSelector('.connection-lost', { timeout: 5000 });

    // Reconnect
    await context.setOffline(false);
    await page.waitForSelector('.connection-restored', { timeout: 10000 });

    // Verify still in lobby
    await expect(page.locator('.lobby-screen')).toBeVisible();
    await expect(page.locator('.player-name:text("TestPlayer")')).toBeVisible();
  });
});
```

**tests/e2e/tests/multiplayer.spec.ts**

```typescript
import { test, expect } from '@playwright/test';

test.describe('Multiplayer Synchronization', () => {
  test('all players should see same game state', async ({ browser }) => {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    // Both players join same room
    const roomCode = 'TEST';
    for (const [page, name] of [[page1, 'Player1'], [page2, 'Player2']]) {
      await page.goto('/controller');
      await page.fill('#room-code', roomCode);
      await page.fill('#player-name', name);
      await page.click('button:text("Join")');
    }

    // Both should see each other
    await expect(page1.locator('.player-name:text("Player2")')).toBeVisible();
    await expect(page2.locator('.player-name:text("Player1")')).toBeVisible();

    // If host starts game, both should transition
    // (Assuming Player1 is host)
    await page1.click('button:text("Start Game")');

    await expect(page1.locator('.game-screen')).toBeVisible();
    await expect(page2.locator('.game-screen')).toBeVisible();

    await context1.close();
    await context2.close();
  });
});
```

## Load & Performance Testing

### Locust Configuration

**tests/load/locustfile.py**

```python
from locust import HttpUser, task, between, events
import random
import string


class GameTimeUser(HttpUser):
    """Simulates a user playing Game Time."""

    wait_time = between(1, 3)

    def on_start(self):
        """Called when user starts."""
        self.session_id = None
        self.room_code = None
        self.player_id = None

    @task(1)
    def create_room(self):
        """Host creates a room."""
        with self.client.post(
            "/api/rooms",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.room_code = data["code"]
                response.success()
            else:
                response.failure(f"Failed to create room: {response.status_code}")

    @task(5)
    def join_room(self):
        """Player joins existing room."""
        if not self.room_code:
            self.room_code = self.get_random_active_room()

        if self.room_code:
            player_name = ''.join(random.choices(string.ascii_letters, k=8))

            with self.client.post(
                f"/api/rooms/{self.room_code}/join",
                json={"name": player_name},
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    self.session_id = data["session_id"]
                    self.player_id = data["player"]["id"]
                    response.success()
                else:
                    response.failure(f"Failed to join: {response.status_code}")

    @task(3)
    def get_room_state(self):
        """Poll room state."""
        if self.room_code:
            with self.client.get(
                f"/api/rooms/{self.room_code}",
                name="/api/rooms/[code]"
            ) as response:
                pass

    def get_random_active_room(self):
        """Get a random active room code."""
        # In real scenario, would query active rooms
        # For load test, use predefined codes
        return random.choice(['TEST1', 'TEST2', 'TEST3'])


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Create test rooms before load test starts."""
    print("Creating test rooms...")
    # Create some test rooms
    # Implementation depends on your setup


class HighLoadUser(HttpUser):
    """Aggressive user for stress testing."""

    wait_time = between(0.1, 0.5)

    @task
    def rapid_requests(self):
        """Make rapid requests to test rate limiting."""
        for _ in range(10):
            self.client.get("/api/rooms")
```

**tests/load/websocket_load.py**

```python
import asyncio
import websockets
import json
from locust import User, task, events
from locust.env import Environment


class WebSocketUser(User):
    """Load test WebSocket connections."""

    abstract = True

    def __init__(self, environment: Environment):
        super().__init__(environment)
        self.ws = None
        self.session_id = "test_session_" + str(id(self))

    async def connect(self):
        """Establish WebSocket connection."""
        uri = f"ws://localhost:8000/ws/{self.session_id}"
        self.ws = await websockets.connect(uri)

    async def send_message(self, msg_type: str, data: dict):
        """Send WebSocket message."""
        message = {
            "type": msg_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.ws.send(json.dumps(message))

    async def receive_message(self):
        """Receive WebSocket message."""
        return json.loads(await self.ws.recv())

    @task
    async def ping_pong(self):
        """Send ping, expect pong."""
        if not self.ws:
            await self.connect()

        start_time = asyncio.get_event_loop().time()
        await self.send_message("ping", {})
        response = await self.receive_message()

        total_time = (asyncio.get_event_loop().time() - start_time) * 1000

        if response["type"] == "pong":
            events.request.fire(
                request_type="WebSocket",
                name="ping",
                response_time=total_time,
                response_length=len(json.dumps(response)),
                exception=None,
                context={}
            )
        else:
            events.request.fire(
                request_type="WebSocket",
                name="ping",
                response_time=total_time,
                response_length=0,
                exception=Exception("Expected pong"),
                context={}
            )
```

### Running Load Tests

```bash
# Start Locust web UI
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Configure:
# - Number of users: 100
# - Spawn rate: 10 users/second
# - Run time: 5 minutes

# Headless mode
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless \
  --html results/load-test-report.html
```

## Security Testing

**backend/tests/security/test_input_validation.py**

```python
import pytest
from httpx import AsyncClient


@pytest.mark.security
class TestInputValidation:
    """Security tests for input validation."""

    @pytest.mark.asyncio
    async def test_xss_prevention_player_name(self, client: AsyncClient):
        """Player name should be sanitized against XSS."""
        malicious_names = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg/onload=alert('xss')>",
        ]

        for name in malicious_names:
            response = await client.post(
                "/api/players",
                json={"name": name}
            )

            # Should either reject or sanitize
            if response.status_code == 200:
                data = response.json()
                # Ensure script tags are escaped or removed
                assert "<script>" not in data["name"].lower()
                assert "onerror" not in data["name"].lower()

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, client: AsyncClient):
        """Should prevent SQL injection attacks."""
        sql_injections = [
            "'; DROP TABLE rooms; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM players--",
        ]

        for injection in sql_injections:
            response = await client.get(f"/api/rooms/{injection}")

            # Should return 404, not 500 (SQL error)
            assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, client: AsyncClient):
        """Should prevent path traversal attacks."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//....//etc/passwd",
        ]

        for attempt in traversal_attempts:
            response = await client.get(f"/api/rooms/{attempt}")
            assert response.status_code in [400, 404]


@pytest.mark.security
class TestRateLimiting:
    """Security tests for rate limiting."""

    @pytest.mark.asyncio
    async def test_room_creation_rate_limit(self, client: AsyncClient):
        """Should enforce rate limit on room creation."""
        # Try to create 10 rooms rapidly (exceeds 5/hour limit)
        responses = []
        for _ in range(10):
            response = await client.post("/api/rooms")
            responses.append(response)

        # Some requests should be rate limited
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes  # Too Many Requests

    @pytest.mark.asyncio
    async def test_api_request_rate_limit(self, client: AsyncClient):
        """Should enforce global API rate limit."""
        # Make 150 requests rapidly (exceeds 100/min limit)
        limited = False
        for _ in range(150):
            response = await client.get("/api/health")
            if response.status_code == 429:
                limited = True
                break

        assert limited, "Rate limiting should have kicked in"
```

## Test Execution

### Running Tests Locally

```bash
# Activate virtual environment
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test suite
pytest tests/unit -v
pytest tests/integration -v
pytest tests/security -v

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_room_code_generator.py -v

# Run specific test
pytest tests/unit/test_room_code_generator.py::TestRoomCodeGeneration::test_generate_room_code_length -v

# Run tests matching pattern
pytest -k "room" -v

# Run tests with markers
pytest -m "unit" -v
pytest -m "security" -v

# Parallel execution
pytest -n auto  # Use all CPU cores
pytest -n 4     # Use 4 workers

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Verbose output
pytest -vv
```

### Docker Test Execution

```bash
# Run all tests in Docker
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Run specific service
docker-compose -f docker-compose.test.yml run --rm backend pytest tests/unit

# Interactive debugging
docker-compose -f docker-compose.test.yml run --rm backend bash
# Then inside container:
# pytest --pdb tests/unit/test_failing.py

# Clean up
docker-compose -f docker-compose.test.yml down -v
```

### Test Parallelization

```bash
# pytest-xdist for parallel execution
pytest -n auto  # Auto-detect CPU cores

# Distribute by test file
pytest -n 4 --dist=loadfile

# Distribute by test function
pytest -n 4 --dist=loadscope
```

## CI/CD Integration

### GitHub Actions Workflow

**.github/workflows/test.yml**

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: gametime_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements/dev.txt

      - name: Run unit tests
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost/gametime_test
          REDIS_URL: redis://localhost:6379/0
          TESTING: true
        run: |
          cd backend
          pytest tests/unit -v --cov=app --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: unit
          name: unit-tests

  integration-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: gametime_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements/dev.txt

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost/gametime_test
          REDIS_URL: redis://localhost:6379/0
          TESTING: true
        run: |
          cd backend
          alembic upgrade head
          pytest tests/integration -v --cov=app --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: integration
          name: integration-tests

  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: tests/e2e/package-lock.json

      - name: Install Playwright
        working-directory: tests/e2e
        run: |
          npm ci
          npx playwright install --with-deps

      - name: Start services
        run: |
          docker-compose up -d
          # Wait for services to be ready
          sleep 10

      - name: Run E2E tests
        working-directory: tests/e2e
        run: npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
          retention-days: 30

  security-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Run security scan
        run: |
          cd backend
          pip install bandit safety
          bandit -r app -f json -o bandit-report.json
          safety check --json

      - name: Upload security report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: backend/bandit-report.json
```

## Best Practices

### Test Organization

**DO:**
- Keep tests close to the code they test
- Use descriptive test names that explain what is being tested
- Group related tests in classes
- Use fixtures for common setup
- Test one thing per test
- Follow AAA pattern (Arrange, Act, Assert)

**DON'T:**
- Put all tests in one giant file
- Use generic names like `test_1`, `test_2`
- Test multiple things in one test
- Rely on test execution order
- Use sleep/wait unless absolutely necessary (use await/waitFor instead)

### Test Data Management

```python
# Good: Use factories
def test_room_creation(db_session):
    room = RoomFactory.create(code="TEST")
    assert room.code == "TEST"

# Avoid: Manual object creation everywhere
def test_room_creation(db_session):
    room = Room(
        code="TEST",
        status="lobby",
        created_at=datetime.now(),
        max_players=12,
        # ... 10 more fields
    )
```

### Async Testing

```python
# Good: Use pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected

# Avoid: sync wrappers
def test_async_function():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(some_async_function())
```

### Test Independence

```python
# Good: Each test is independent
@pytest.fixture
def clean_room(db_session):
    room = create_room()
    yield room
    delete_room(room.id)

# Bad: Tests depend on each other
def test_create_room():
    global room_id
    room_id = create_room()

def test_join_room():
    # Uses global room_id from previous test
    join_room(room_id)
```

### Mocking

```python
# Good: Mock external dependencies
@pytest.mark.asyncio
async def test_api_call(mocker):
    mock_http = mocker.patch('httpx.AsyncClient.get')
    mock_http.return_value.json.return_value = {"data": "test"}

    result = await fetch_external_data()
    assert result["data"] == "test"

# Avoid: Mocking internal logic
# (defeats the purpose of testing)
```

## Troubleshooting

### Common Issues

#### Tests Pass Locally but Fail in CI

**Cause**: Environment differences, timing issues, missing dependencies

**Solution:**
```bash
# Run tests in Docker locally to match CI
docker-compose -f docker-compose.test.yml up

# Check for hardcoded paths
grep -r "localhost" tests/
grep -r "/Users/" tests/

# Ensure deterministic behavior
# - Use fixed seeds for random data
# - Use time mocking for time-dependent tests
```

#### Flaky Tests

**Cause**: Race conditions, timing issues, external dependencies

**Solution:**
```python
# Use proper waits instead of sleep
# Bad:
time.sleep(1)
assert element.is_visible()

# Good:
await element.wait_for(state="visible", timeout=5000)

# Use retries for inherently flaky operations
@pytest.mark.flaky(reruns=3)
async def test_sometimes_flaky():
    ...
```

#### Slow Tests

**Cause**: Too many E2E tests, no parallelization, slow fixtures

**Solution:**
```bash
# Run in parallel
pytest -n auto

# Profile slow tests
pytest --durations=10

# Use faster fixtures
# - In-memory database (tmpfs)
# - Mock external calls
# - Reuse expensive fixtures
```

#### Coverage Not Increasing

**Cause**: Untested code paths, missing test markers

**Solution:**
```bash
# View uncovered lines
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Check which files are excluded
cat .coveragerc

# Run all test types
pytest tests/ --cov=app
```

### Getting Help

- **Documentation**: See PLAN.md for architecture details
- **GitHub Issues**: Search for similar test issues
- **Pytest Docs**: https://docs.pytest.org/
- **Playwright Docs**: https://playwright.dev/
- **Stack Overflow**: Tag with `pytest`, `playwright`, `fastapi`

---

**Last Updated**: 2025-01-15
**Version**: 1.0

Testing is not just about finding bugs—it's about building confidence that our code works as intended. Happy testing!
