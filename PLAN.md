# Party Game Platform - Comprehensive Implementation Plan

## Project Overview

Build a production-ready, multiplayer party game system similar to Jackbox, where players use their phones as controllers while viewing a shared display screen. The system will support three initial games: Horse Race Betting, Trivia Quiz, and Memory Game.

**Core Features:**
- Real-time multiplayer gameplay for 2-12 players
- Dual-screen experience (shared display + individual controllers)
- Simple room code join system (no authentication required)
- Persistent game statistics and leaderboards
- Mobile-first responsive design
- Production-ready security and scalability

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+ (Python 3.11+)
  - Native async/await for WebSockets
  - Automatic OpenAPI documentation
  - Pydantic v2 for validation
  - High performance for concurrent connections

- **Database**: PostgreSQL 15+
  - ACID compliance for game state consistency
  - JSONB for flexible game state storage
  - Connection pooling with asyncpg
  - Full-text search for future features

- **Cache/Session Store**: Redis 7+
  - WebSocket session management
  - Rate limiting counters
  - Pub/Sub for horizontal scaling
  - Game state caching

- **Task Queue**: Celery (optional for v2)
  - Background cleanup jobs
  - Statistics aggregation
  - Email notifications

### Frontend
- **Core**: Vanilla HTML5/CSS3/JavaScript (ES6+)
  - Zero build step for simplicity
  - Progressive Web App (PWA) capabilities
  - Service Worker for offline support
  - Web Components for reusability

- **Styling**: CSS Grid + Flexbox
  - Mobile-first responsive design
  - CSS custom properties for theming
  - Smooth animations with CSS transitions

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Process Manager**: Gunicorn + Uvicorn workers
- **Reverse Proxy**: Nginx
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging with JSON format
- **CI/CD**: GitHub Actions

## Project Structure

```
game-time/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI app entry
│   │   ├── config.py                    # Settings management
│   │   ├── database.py                  # DB connection pool
│   │   ├── redis.py                     # Redis connection
│   │   ├── dependencies.py              # FastAPI dependencies
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py              # Security utilities
│   │   │   ├── rate_limit.py            # Rate limiting
│   │   │   ├── exceptions.py            # Custom exceptions
│   │   │   └── logging.py               # Logging config
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # SQLAlchemy base
│   │   │   ├── room.py                  # Room model
│   │   │   ├── player.py                # Player model
│   │   │   ├── game_session.py          # Game session model
│   │   │   ├── score.py                 # Score model
│   │   │   └── trivia_question.py       # Trivia questions
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── room.py                  # Room Pydantic schemas
│   │   │   ├── player.py                # Player schemas
│   │   │   ├── game.py                  # Game schemas
│   │   │   └── websocket.py             # WebSocket message schemas
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── room_manager.py          # Room lifecycle
│   │   │   ├── game_manager.py          # Game orchestration
│   │   │   ├── websocket_manager.py     # WebSocket connections
│   │   │   ├── player_manager.py        # Player management
│   │   │   └── stats_service.py         # Statistics tracking
│   │   │
│   │   ├── games/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Abstract base game
│   │   │   ├── horse_race.py            # Horse race implementation
│   │   │   ├── trivia.py                # Trivia implementation
│   │   │   └── memory.py                # Memory game implementation
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py                # Health check endpoints
│   │   │   ├── rooms.py                 # Room HTTP API
│   │   │   ├── games.py                 # Game HTTP API
│   │   │   ├── stats.py                 # Statistics API
│   │   │   └── websocket.py             # WebSocket endpoint
│   │   │
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── cors.py                  # CORS configuration
│   │   │   ├── error_handler.py         # Global error handling
│   │   │   ├── request_id.py            # Request ID tracking
│   │   │   └── security_headers.py      # Security headers
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── room_code.py             # Room code generation
│   │       ├── session.py               # Session ID generation
│   │       ├── validators.py            # Custom validators
│   │       └── sanitizers.py            # Input sanitization
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                  # Pytest fixtures
│   │   ├── unit/
│   │   │   ├── test_room_manager.py
│   │   │   ├── test_games.py
│   │   │   └── test_validators.py
│   │   ├── integration/
│   │   │   ├── test_room_flow.py
│   │   │   ├── test_game_flow.py
│   │   │   └── test_websocket.py
│   │   └── e2e/
│   │       └── test_full_game.py
│   │
│   ├── alembic/                         # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── scripts/
│   │   ├── seed_trivia.py               # Seed trivia questions
│   │   ├── cleanup_old_rooms.py         # Cleanup script
│   │   └── init_db.py                   # Database initialization
│   │
│   ├── requirements/
│   │   ├── base.txt                     # Core dependencies
│   │   ├── dev.txt                      # Development tools
│   │   └── prod.txt                     # Production extras
│   │
│   ├── Dockerfile
│   ├── .env.example
│   └── pytest.ini
│
├── frontend/
│   ├── shared/
│   │   ├── css/
│   │   │   ├── reset.css                # CSS reset
│   │   │   ├── variables.css            # CSS custom properties
│   │   │   ├── typography.css           # Typography styles
│   │   │   └── utilities.css            # Utility classes
│   │   └── js/
│   │       ├── config.js                # Frontend config
│   │       ├── websocket-client.js      # WebSocket abstraction
│   │       ├── state-manager.js         # Simple state management
│   │       ├── utils.js                 # Utility functions
│   │       └── components/
│   │           ├── player-list.js       # Reusable player list
│   │           └── scoreboard.js        # Reusable scoreboard
│   │
│   ├── display/
│   │   ├── index.html                   # Display entry point
│   │   ├── lobby.html                   # Lobby screen
│   │   ├── game-select.html             # Game selection
│   │   ├── horse-race.html              # Horse race display
│   │   ├── trivia.html                  # Trivia display
│   │   ├── memory.html                  # Memory display
│   │   ├── results.html                 # Results screen
│   │   │
│   │   ├── css/
│   │   │   ├── display.css              # Display-specific styles
│   │   │   ├── lobby.css
│   │   │   ├── horse-race.css
│   │   │   ├── trivia.css
│   │   │   └── memory.css
│   │   │
│   │   └── js/
│   │       ├── display.js               # Display controller
│   │       ├── lobby-display.js
│   │       └── games/
│   │           ├── horse-race-display.js
│   │           ├── trivia-display.js
│   │           └── memory-display.js
│   │
│   ├── controller/
│   │   ├── index.html                   # Controller entry
│   │   ├── join.html                    # Room join screen
│   │   ├── lobby.html                   # Lobby wait screen
│   │   ├── horse-race.html              # Betting interface
│   │   ├── trivia.html                  # Answer selection
│   │   ├── memory.html                  # Card selection
│   │   ├── waiting.html                 # Generic waiting screen
│   │   │
│   │   ├── css/
│   │   │   ├── controller.css           # Controller base styles
│   │   │   ├── join.css
│   │   │   ├── games.css
│   │   │   └── mobile-optimized.css
│   │   │
│   │   └── js/
│   │       ├── controller.js            # Controller manager
│   │       ├── join.js
│   │       └── games/
│   │           ├── horse-race-controller.js
│   │           ├── trivia-controller.js
│   │           └── memory-controller.js
│   │
│   ├── manifest.json                    # PWA manifest
│   ├── service-worker.js                # Service worker
│   └── robots.txt
│
├── nginx/
│   ├── nginx.conf                       # Nginx configuration
│   └── ssl/                             # SSL certificates
│
├── monitoring/
│   ├── prometheus.yml                   # Prometheus config
│   └── grafana/
│       └── dashboards/
│
├── docker-compose.yml                   # Local development
├── docker-compose.prod.yml              # Production setup
├── .github/
│   └── workflows/
│       ├── test.yml                     # CI tests
│       └── deploy.yml                   # CD pipeline
│
├── .gitignore
├── .env.example
├── README.md
├── PLAN.md
├── SECURITY.md
├── CONTRIBUTING.md
└── LICENSE
```

## Database Schema (PostgreSQL)

### Tables with Security & Performance Considerations

#### rooms
```sql
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    code VARCHAR(6) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'lobby' CHECK (status IN ('lobby', 'playing', 'finished')),
    current_game VARCHAR(50) CHECK (current_game IN ('horse_race', 'trivia', 'memory', NULL)),
    host_player_id INTEGER,
    max_players INTEGER DEFAULT 12 CHECK (max_players BETWEEN 2 AND 12),
    settings JSONB DEFAULT '{}',
    is_public BOOLEAN DEFAULT TRUE,

    CONSTRAINT valid_code CHECK (code ~ '^[A-Z0-9]{4,6}$')
);

-- Indexes for performance
CREATE INDEX idx_rooms_code ON rooms(code);
CREATE INDEX idx_rooms_status ON rooms(status);
CREATE INDEX idx_rooms_last_activity ON rooms(last_activity);

-- Auto-update timestamp
CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### players
```sql
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    session_id VARCHAR(128) UNIQUE NOT NULL,
    is_host BOOLEAN DEFAULT FALSE,
    connected BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,

    CONSTRAINT valid_name CHECK (LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 50),
    CONSTRAINT valid_session_id CHECK (session_id ~ '^[a-f0-9]{64}$')
);

CREATE INDEX idx_players_room_id ON players(room_id);
CREATE INDEX idx_players_session_id ON players(session_id);
CREATE INDEX idx_players_connected ON players(connected) WHERE connected = TRUE;
```

#### game_sessions
```sql
CREATE TABLE game_sessions (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    game_type VARCHAR(50) NOT NULL CHECK (game_type IN ('horse_race', 'trivia', 'memory')),
    state JSONB NOT NULL DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE,
    winner_id INTEGER REFERENCES players(id),

    CONSTRAINT valid_finish_time CHECK (finished_at IS NULL OR finished_at > started_at)
);

CREATE INDEX idx_game_sessions_room_id ON game_sessions(room_id);
CREATE INDEX idx_game_sessions_game_type ON game_sessions(game_type);
CREATE INDEX idx_game_sessions_finished_at ON game_sessions(finished_at);
```

#### scores
```sql
CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    game_session_id INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    score INTEGER DEFAULT 0 CHECK (score >= 0),
    round_scores JSONB DEFAULT '[]',
    bonus_points INTEGER DEFAULT 0 CHECK (bonus_points >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(game_session_id, player_id)
);

CREATE INDEX idx_scores_game_session ON scores(game_session_id);
CREATE INDEX idx_scores_player ON scores(player_id);
CREATE INDEX idx_scores_score ON scores(score DESC);
```

#### trivia_questions
```sql
CREATE TABLE trivia_questions (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL CHECK (LENGTH(question) >= 10),
    options JSONB NOT NULL,
    correct_answer INTEGER NOT NULL CHECK (correct_answer BETWEEN 0 AND 3),
    category VARCHAR(50),
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    time_limit INTEGER DEFAULT 15 CHECK (time_limit BETWEEN 5 AND 60),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    times_used INTEGER DEFAULT 0,

    CONSTRAINT valid_options CHECK (jsonb_array_length(options) = 4)
);

CREATE INDEX idx_trivia_category ON trivia_questions(category);
CREATE INDEX idx_trivia_difficulty ON trivia_questions(difficulty);
CREATE INDEX idx_trivia_times_used ON trivia_questions(times_used);
```

#### rate_limits
```sql
CREATE TABLE rate_limits (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    endpoint VARCHAR(100) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(ip_address, endpoint, window_start)
);

CREATE INDEX idx_rate_limits_ip ON rate_limits(ip_address, window_start);
```

#### audit_log
```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    room_id INTEGER REFERENCES rooms(id) ON DELETE SET NULL,
    player_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_log_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX idx_audit_log_room_id ON audit_log(room_id) WHERE room_id IS NOT NULL;
```

## Security Architecture

### Input Validation & Sanitization
1. **Room Codes**: 4-6 uppercase alphanumeric, exclude ambiguous chars (0/O, 1/I/L)
2. **Player Names**: 1-50 chars, sanitize HTML entities, filter profanity
3. **Session IDs**: 256-bit cryptographically secure random tokens
4. **WebSocket Messages**: Validate schema with Pydantic before processing

### Rate Limiting
- **Room Creation**: 5 rooms per IP per hour
- **Room Join**: 10 attempts per IP per minute
- **WebSocket Messages**: 60 messages per connection per minute
- **API Endpoints**: 100 requests per IP per minute

### WebSocket Security
1. **Origin Validation**: Verify WebSocket upgrade origin header
2. **Session Validation**: Authenticate session_id on connect
3. **Message Validation**: Schema validation for all incoming messages
4. **Connection Limits**: Max 2 concurrent connections per session
5. **Heartbeat**: 30-second ping/pong to detect dead connections

### Data Protection
- **Session Storage**: Secure httpOnly cookies (production)
- **Sensitive Data**: Never log session IDs or IP addresses in clear text
- **Database**: Encrypted at rest (managed by cloud provider)
- **Transport**: TLS 1.3 for all connections in production

### CORS Policy
- **Development**: Allow localhost origins
- **Production**: Whitelist specific domains only
- **WebSocket**: Validate upgrade request origin

### DDoS Protection
- Connection limits per IP (max 10 concurrent WebSockets)
- Message size limits (max 10KB per WebSocket message)
- Room size limits (max 12 players per room)
- Automatic cleanup of inactive rooms (1 hour timeout)

### XSS Prevention
- CSP headers with strict policy
- Sanitize all user input before display
- Escape HTML in player names and messages

## WebSocket Communication Protocol

### Connection Flow
1. Client connects to `/ws/{session_id}`
2. Server validates session or creates new one
3. Client sends `join_room` with room code
4. Server validates and broadcasts `player_joined`
5. Heartbeat every 30 seconds
6. Auto-reconnect on disconnect

### Message Format
```typescript
interface WebSocketMessage {
    type: string;                    // Event type
    data: object;                    // Event-specific payload
    timestamp: number;               // Unix timestamp (ms)
    messageId?: string;              // Optional message ID for tracking
}

interface ErrorMessage extends WebSocketMessage {
    type: 'error';
    data: {
        code: string;                // Error code (ROOM_NOT_FOUND, etc.)
        message: string;             // Human-readable error
        retryable: boolean;          // Can client retry?
    };
}
```

### Event Types

#### Connection Management
- `join_room` (C→S): Join a room with code
- `leave_room` (C→S): Leave current room
- `player_joined` (S→C): New player joined
- `player_left` (S→C): Player left
- `reconnect` (C→S): Reconnect with existing session
- `ping` (C↔S): Heartbeat
- `pong` (C↔S): Heartbeat response

#### Lobby Events
- `lobby_state` (S→C): Full lobby state sync
- `player_ready` (C→S): Player marks ready
- `player_unready` (C→S): Player marks not ready
- `kick_player` (C→S): Host kicks player (host only)
- `select_game` (C→S): Host selects game (host only)
- `start_game` (C→S): Host starts game (host only)
- `game_starting` (S→C): Game is starting countdown

#### Game Events
- `game_state` (S→C): Full game state update
- `game_state_delta` (S→C): Partial state update (optimization)
- `player_action` (C→S): Player action (validated per game)
- `round_start` (S→C): New round starting
- `round_end` (S→C): Round complete with results
- `game_end` (S→C): Game finished with final scores

#### Horse Race Events
- `betting_phase` (S→C): Betting phase started
- `place_bet` (C→S): Player places bet on horse
- `bet_placed` (S→C): Bet confirmed
- `race_starting` (S→C): Race about to start (countdown)
- `race_tick` (S→C): Horse positions update (200ms interval)
- `race_finish` (S→C): Race complete, winners announced

#### Trivia Events
- `question` (S→C): New question displayed
- `submit_answer` (C→S): Player submits answer
- `answer_locked` (S→C): Answer submission confirmed
- `reveal_answer` (S→C): Correct answer revealed
- `round_scores` (S→C): Scores for this round

#### Memory Events
- `turn_start` (S→C): Player's turn begins
- `flip_card` (C→S): Player flips card at position
- `card_revealed` (S→C): Card value revealed
- `cards_match` (S→C): Cards matched, removed
- `cards_mismatch` (S→C): Cards flipped back
- `turn_end` (S→C): Turn complete

### Error Codes
```
ROOM_NOT_FOUND         - Room code doesn't exist
ROOM_FULL              - Room at max capacity
ROOM_IN_GAME           - Can't join room during game
INVALID_SESSION        - Session ID invalid/expired
INVALID_ACTION         - Action not allowed in current state
RATE_LIMIT_EXCEEDED    - Too many requests
PLAYER_NOT_HOST        - Action requires host privileges
INVALID_MESSAGE        - Message format invalid
CONNECTION_LIMIT       - Too many connections from IP
```

## Game Implementations

### 1. Horse Race Betting Game

#### Configuration
```python
HORSE_RACE_CONFIG = {
    'num_horses': 6,
    'track_length': 100,
    'tick_interval_ms': 200,
    'betting_time_seconds': 30,
    'min_speed': 1,
    'max_speed': 4,
    'finish_positions_for_points': 2,  # 1st and 2nd get points
}
```

#### Game Flow
1. **Setup Phase** (5s): Display shows horses, names announced
2. **Betting Phase** (30s): Players select horse on controller
3. **Race Phase** (10-20s): Horses race with random movement
4. **Results Phase** (10s): Winners announced, points awarded
5. **Transition**: Return to lobby or next game

#### Scoring System
- **1st Place Bet**: 100 points
- **2nd Place Bet**: 50 points
- **3rd Place Bet**: 25 points
- **Bonus**: If player bets early (+10% bonus)

#### Technical Implementation
- Server-side race simulation (no client-side prediction)
- Deterministic random with seed for replay capability
- Broadcast race_tick every 200ms with all positions
- Smooth client-side interpolation for animations

### 2. Trivia Quiz Game

#### Configuration
```python
TRIVIA_CONFIG = {
    'questions_per_game': 10,
    'time_per_question': 15,
    'points_correct': 100,
    'speed_bonus_max': 50,
    'streak_multiplier': 1.2,  # 20% bonus per streak
    'categories': ['general', 'science', 'history', 'sports', 'entertainment'],
}
```

#### Game Flow
1. **Question Display** (2s): Question and options shown on display
2. **Answer Phase** (15s): Players select answer, timer counts down
3. **Lock Phase** (1s): Answers locked, build suspense
4. **Reveal Phase** (5s): Correct answer revealed, scores updated
5. **Scoreboard** (3s): Updated leaderboard shown
6. **Repeat**: Next question or game end

#### Scoring System
```python
base_points = 100
time_bonus = int((time_remaining / total_time) * 50)
streak_bonus = base_points * (streak_multiplier ** (current_streak - 1))
total = (base_points + time_bonus) * (1 + streak_bonus) if correct else 0
```

#### Anti-Cheating Measures
- Questions selected randomly from pool
- Correct answer never sent to clients until reveal
- Answer submissions timestamped server-side
- Late submissions rejected (grace period 500ms)

### 3. Memory Game

#### Configuration
```python
MEMORY_CONFIG = {
    'grid_size': {
        '2-4': (4, 4),   # 4x4 grid for 2-4 players
        '5-8': (6, 4),   # 6x4 grid for 5-8 players
        '9-12': (6, 6),  # 6x6 grid for 9-12 players
    },
    'turn_time_limit': 30,
    'reveal_time': 2000,  # ms to show mismatched cards
    'points_per_match': 10,
    'turn_order': 'sequential',  # or 'fastest_first'
}
```

#### Game Flow
1. **Setup Phase** (3s): Cards shuffled and placed face-down
2. **Turn Announcement** (2s): Current player announced
3. **First Card** (30s timeout): Player selects first card
4. **Second Card** (30s timeout): Player selects second card
5. **Reveal** (2s): Cards shown to all
6. **Match/Mismatch**: Update scores, determine next player
7. **Repeat**: Until all pairs matched
8. **Results**: Final scores and winner

#### Turn Management
- **Sequential**: Round-robin through players
- **Bonus Turn**: Player who matches gets another turn
- **Timeout**: Auto-forfeit if no action within time limit
- **Skip**: Disconnected players automatically skipped

#### State Synchronization
- Full board state sent to display only
- Controllers only see "your turn" / "waiting" state
- Card flips broadcast to all for suspense
- Prevent double-selection with optimistic locking

## Implementation Phases

### Phase 1: Foundation & Infrastructure (Week 1)

#### 1.1 Project Setup
- Initialize Git repository with proper .gitignore
- Set up Python virtual environment
- Create requirements files (base, dev, prod)
- Configure pre-commit hooks (black, isort, flake8, mypy)
- Set up Docker and docker-compose for development

#### 1.2 Backend Core
- **FastAPI application setup**
  - Main app with proper CORS and middleware
  - Configuration management with pydantic-settings
  - Structured logging with loguru
  - Health check endpoints

- **Database setup**
  - PostgreSQL connection with asyncpg
  - SQLAlchemy 2.0 async models
  - Alembic migrations setup
  - Database initialization script

- **Redis setup**
  - Redis connection pool
  - Session management utilities
  - Rate limiting implementation

#### 1.3 Security Foundation
- Security headers middleware
- Rate limiting middleware
- Input validation utilities
- Session ID generation (cryptographically secure)
- Room code generation with validation

#### 1.4 Testing Infrastructure
- Pytest setup with async support
- Test database fixtures
- Mock WebSocket client
- Coverage configuration (>80% target)
- Playwright setup for E2E tests
  - Install Playwright and browsers
  - Basic playwright.config.ts
  - Simple smoke test (server responds)

**Deliverables:**
- Running FastAPI server with health checks
- Database migrations working
- Redis connected
- Basic test suite passing
- Docker development environment
- First browser automation test (Playwright smoke test)

### Phase 2: Room & Lobby System (Week 1-2)

#### 2.1 Room Management Service
- Create room with unique code generation
- Join room with validation
- Leave room and cleanup
- Room lifecycle management (lobby → playing → finished)
- Auto-cleanup of stale rooms (background task)

#### 2.2 Player Management
- Player registration in room
- Session management with Redis
- Connection tracking
- Host assignment and transfer
- Kick player functionality

#### 2.3 WebSocket Infrastructure
- WebSocket endpoint with authentication
- Connection manager service
- Message routing and validation
- Broadcast utilities (room-wide, role-specific)
- Heartbeat mechanism (ping/pong)
- Reconnection handling

#### 2.4 Frontend - Lobby Views
- **Display Lobby**
  - Room code display (large, clear)
  - Player list with join animations
  - Host controls (start game, kick player)
  - Game selection UI
  - Responsive layout for TV screens

- **Controller Lobby**
  - Join room interface with code input
  - Player name entry
  - Waiting room with player list
  - Ready/not ready toggle
  - Mobile-optimized touch targets

#### 2.5 Shared Frontend Components
- WebSocket client wrapper
- State management system
- Player list component
- Error handling and notifications
- Loading states

**Deliverables:**
- Players can create and join rooms
- Real-time player list updates
- Host can control lobby
- WebSocket reconnection works
- Full test coverage of room flows

### Phase 3: Game Framework (Week 2)

#### 3.1 Base Game System
- Abstract BaseGame class with lifecycle hooks
- Game state management
- Game registration system
- Game selection in lobby
- Transition between lobby ↔ game ↔ results

#### 3.2 Score System
- Score tracking service
- Leaderboard generation
- Round scores vs. cumulative scores
- Score persistence to database

#### 3.3 Results Screen
- **Display Results**
  - Animated scoreboard
  - Winner announcement
  - Game statistics
  - "Play again" or "New game" options

- **Controller Results**
  - Personal stats
  - Final ranking
  - Simple results view

#### 3.4 Game State Synchronization
- Full state sync on join/reconnect
- Delta updates for performance
- Conflict resolution strategies
- State validation

**Deliverables:**
- Game framework ready for implementations
- Score system working
- Results screens functional
- State sync tested and reliable

### Phase 4: Horse Race Game (Week 3)

#### 4.1 Game Logic
- Horse race simulation engine
- Betting system
- Race physics (random movement with constraints)
- Winner determination
- Point calculation

#### 4.2 Display View
- Track and horses visualization
- Betting phase countdown
- Animated race (smooth 60fps)
- Results with replay option
- Sound effects (optional)

#### 4.3 Controller View
- Horse selection interface
- Large, touch-friendly betting buttons
- Bet confirmation
- Waiting screen during race
- Personal result notification

#### 4.4 Testing
- Unit tests for race logic
- Integration tests for full game flow
- Load testing with multiple concurrent games
- WebSocket stress testing

**Deliverables:**
- Fully functional horse race game
- Smooth animations
- Mobile-optimized controller
- Comprehensive test coverage

### Phase 5: Trivia Game (Week 3-4)

#### 5.1 Question Management
- Database seeding script (100+ questions)
- Question selection algorithm (no repeats in same session)
- Category balancing
- Difficulty progression

#### 5.2 Game Logic
- Question distribution
- Answer validation (server-side only)
- Timing system with precision
- Scoring with speed bonus
- Streak tracking

#### 5.3 Display View
- Question and options display
- Answer countdown timer
- Player answer indicators (without revealing answer)
- Correct answer reveal animation
- Running scoreboard

#### 5.4 Controller View
- Large answer buttons (A, B, C, D)
- Visual feedback on selection
- Lock-in confirmation
- Waiting state between questions
- Personal score updates

#### 5.5 Testing
- Question selection randomness
- Anti-cheating validation
- Timing accuracy tests
- Concurrent player answer handling

**Deliverables:**
- Trivia game with 100+ questions
- Fair and accurate scoring
- Engaging animations
- Cheat-proof implementation

### Phase 6: Memory Game (Week 4)

#### 6.1 Game Logic
- Card shuffling and placement
- Turn management system
- Match detection
- Timeout handling
- Winner determination

#### 6.2 Display View
- Card grid layout (responsive to player count)
- Card flip animations
- Turn indicator
- Match/mismatch feedback
- Progressive board clearing

#### 6.3 Controller View
- Turn notification
- Card grid for selection (display-only)
- Simple "waiting" state when not your turn
- Match feedback
- Running score

#### 6.4 State Management
- Optimistic locking for card selection
- Prevent simultaneous selections
- Handle disconnections mid-turn
- Fair turn rotation

**Deliverables:**
- Working memory game
- Fair turn system
- Beautiful animations
- Handles edge cases (disconnections, timeouts)

### Phase 7: Polish, Testing & Production Prep (Week 5)

#### 7.1 Error Handling & Resilience
- Comprehensive error handling
- Graceful degradation
- Automatic reconnection with exponential backoff
- User-friendly error messages
- Fallback UI states

#### 7.2 Performance Optimization
- Database query optimization
- Redis caching strategy
- WebSocket message batching
- Frontend lazy loading
- Asset optimization (minification, compression)

#### 7.3 Accessibility (WCAG 2.1 AA)
- Keyboard navigation
- Screen reader support
- High contrast mode
- Focus indicators
- ARIA labels

#### 7.4 PWA Features
- Service Worker for offline support
- App manifest
- Add to home screen
- Push notifications (optional)

#### 7.5 Monitoring & Logging
- Prometheus metrics
- Structured logging
- Error tracking (Sentry)
- Performance monitoring
- Custom dashboards

#### 7.6 Documentation
- API documentation (OpenAPI/Swagger)
- WebSocket protocol documentation
- Deployment guide
- Development setup guide
- Architecture decision records (ADRs)

#### 7.7 Production Deployment
- Nginx configuration
- SSL/TLS setup
- Environment configuration
- Database backup strategy
- Scaling configuration
- CI/CD pipeline

#### 7.8 Load Testing
- JMeter/Locust test scenarios
- Concurrent room stress test
- WebSocket connection limits
- Database performance under load
- Identify bottlenecks

**Deliverables:**
- Production-ready application
- Comprehensive documentation
- Monitoring and alerting setup
- Deployment automation
- Performance benchmarks

## Development Workflow

### Local Development
```bash
# Start all services
docker-compose up -d

# Backend runs at http://localhost:8000
# Frontend served at http://localhost:8000/static
# PostgreSQL at localhost:5432
# Redis at localhost:6379
# API docs at http://localhost:8000/docs
```

### Testing Strategy
```bash
# Unit tests (fast, no external dependencies)
pytest tests/unit -v

# Integration tests (database, redis)
pytest tests/integration -v

# E2E tests (full game flows)
pytest tests/e2e -v

# Coverage report
pytest --cov=app --cov-report=html
```

### Code Quality
- **Linting**: ruff (replaces flake8, black, isort)
- **Type Checking**: mypy with strict mode
- **Security**: bandit for security issues
- **Dependencies**: pip-audit for vulnerabilities
- **Pre-commit**: Automated checks before commit

### Git Workflow
- **Main branch**: Production-ready code
- **Develop branch**: Integration branch
- **Feature branches**: feature/game-horse-race
- **Commit convention**: Conventional Commits
- **PR reviews**: Required before merge
- **CI checks**: All tests must pass

## Deployment Architecture

### Development
```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│  FastAPI (Uvicorn)          │
│  - Serves static files      │
│  - WebSocket endpoints      │
│  - API endpoints            │
└──────┬──────────────────────┘
       │
   ┌───▼────┬────────┐
   │        │        │
┌──▼──┐ ┌──▼──┐ ┌───▼───┐
│ PG  │ │Redis│ │ Files │
└─────┘ └─────┘ └───────┘
```

### Production
```
                    ┌─────────────┐
                    │     CDN     │
                    │  (Optional) │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Nginx    │
                    │ (SSL + LB)  │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐    ┌────▼─────┐    ┌────▼─────┐
    │  FastAPI  │    │ FastAPI  │    │ FastAPI  │
    │  Worker 1 │    │ Worker 2 │    │ Worker N │
    └─────┬─────┘    └────┬─────┘    └────┬─────┘
          │               │               │
          └───────┬───────┴───────┬───────┘
                  │               │
            ┌─────▼─────┐   ┌─────▼─────┐
            │PostgreSQL │   │   Redis   │
            │ (Primary) │   │ (Cluster) │
            │     +     │   │           │
            │ (Replica) │   │           │
            └───────────┘   └───────────┘
```

### Scaling Considerations
1. **Horizontal Scaling**: Multiple FastAPI workers behind load balancer
2. **Session Affinity**: Use Redis Pub/Sub for cross-worker communication
3. **Database**: Connection pooling, read replicas for analytics
4. **Redis**: Cluster mode for high availability
5. **CDN**: Serve static assets from CDN
6. **Auto-scaling**: Based on CPU/WebSocket connection metrics

## Key Technical Decisions

### Why FastAPI?
- **Async Native**: Built for WebSocket and high concurrency
- **Type Safety**: Pydantic validation prevents entire classes of bugs
- **Performance**: Among the fastest Python frameworks
- **DX**: Automatic API docs, great error messages
- **Ecosystem**: Rich async ecosystem (databases, redis, testing)

### Why PostgreSQL?
- **ACID Compliance**: Critical for game state consistency
- **JSONB**: Flexibility for game-specific state without schema changes
- **Performance**: Excellent for read-heavy workloads with proper indexing
- **Reliability**: Battle-tested, excellent tooling
- **Features**: Full-text search, geospatial (future features)

### Why Vanilla JS?
- **Zero Build Step**: Faster iteration, simpler deployment
- **Performance**: No framework overhead
- **Learning**: Easier for contributors to understand
- **Reliability**: No dependency vulnerabilities, no breaking changes
- **Progressive**: Can add build tools later if needed

### State Management Strategy
1. **Source of Truth**: Server (PostgreSQL + Redis)
2. **In-Memory**: Active game state in Redis for speed
3. **Persistence**: Checkpoint to PostgreSQL every round
4. **Recovery**: Rebuild from PostgreSQL on server restart
5. **Client State**: UI state only, always defer to server

### WebSocket vs. Server-Sent Events (SSE)
- **Chose WebSocket** for bidirectional communication
- **Fallback**: Could implement HTTP polling for legacy clients
- **Trade-offs**: More complex than SSE but better for low latency

### Testing Philosophy
- **Unit Tests**: Business logic, game rules, utilities
- **Integration Tests**: Database operations, services
- **E2E Tests**: Critical user flows (create room, play game, scores)
- **Manual Testing**: UX, animations, mobile devices
- **Load Testing**: Capacity planning, identify bottlenecks

## Security Best Practices

### OWASP Top 10 Mitigations
1. **Injection**: Parameterized queries, Pydantic validation
2. **Broken Authentication**: Secure session IDs, rate limiting
3. **Sensitive Data Exposure**: No PII stored, encrypted transport
4. **XML External Entities**: N/A (no XML processing)
5. **Broken Access Control**: Host-only actions validated server-side
6. **Security Misconfiguration**: Security headers, HTTPS enforced
7. **XSS**: Input sanitization, CSP headers, HTML escaping
8. **Insecure Deserialization**: Pydantic validation, no pickle
9. **Known Vulnerabilities**: Automated dependency scanning
10. **Insufficient Logging**: Comprehensive audit log, monitoring

### Compliance Considerations
- **GDPR**: No PII collected (anonymous gameplay)
- **COPPA**: Age verification not required (party game)
- **Accessibility**: WCAG 2.1 AA compliance
- **Terms of Service**: Simple ToS for public deployment

## Monitoring & Observability

### Metrics (Prometheus)
- HTTP request rate, latency, error rate
- WebSocket connection count, message rate
- Active rooms count
- Active players count
- Database connection pool usage
- Redis hit/miss rate
- Game duration statistics
- Player distribution per game

### Logs (Structured JSON)
- Request ID tracking
- Error logs with stack traces
- Audit events (room creation, game start, etc.)
- Performance logs (slow queries)
- Security events (rate limit exceeded, invalid tokens)

### Alerts
- High error rate (>1% 5xx responses)
- Database connection pool exhaustion
- Redis unavailable
- High response latency (p95 > 200ms)
- Disk space low
- SSL certificate expiring

### Dashboards (Grafana)
- Real-time player count
- Rooms by status (lobby, playing, finished)
- Game popularity (which games played most)
- Response time percentiles
- Error rate trends
- Infrastructure health

## Future Enhancements (Post-MVP)

### Phase 8: Additional Games
- Drawing game (like Pictionary)
- Word association game
- Voting/polling game
- Music quiz game
- Custom game creator framework

### Phase 9: Social Features
- Optional user accounts
- Friend system
- Private rooms (password-protected)
- Room history and replays
- Achievement system
- Global leaderboards

### Phase 10: Customization
- Custom game settings (time limits, scoring rules)
- Theme customization
- Custom trivia question packs
- Room moderator tools
- Spectator mode

### Phase 11: Advanced Features
- Tournament mode
- Team-based games
- Voice chat integration
- Video conferencing integration
- Mobile native apps (React Native)
- Desktop app (Electron)

### Phase 12: Analytics & AI
- Player behavior analytics
- Game balance tuning with ML
- Adaptive difficulty
- Personalized game recommendations
- Cheat detection with anomaly detection

## Success Metrics

### Technical KPIs
- **Uptime**: 99.9% availability
- **Performance**: p95 response time < 100ms
- **Scalability**: Support 1000 concurrent rooms
- **Test Coverage**: >80% code coverage
- **Security**: Zero critical vulnerabilities

### Product KPIs
- **Engagement**: Average game duration > 15 minutes
- **Retention**: 50% of players play multiple games
- **Growth**: Organic sharing (viral coefficient > 1)
- **User Satisfaction**: NPS score > 50
- **Accessibility**: WCAG 2.1 AA compliance

## Conclusion

This plan provides a comprehensive roadmap for building a production-ready, secure, and scalable multiplayer party game platform. The phased approach allows for iterative development while maintaining quality and security standards throughout.

Key success factors:
- Security-first design
- Comprehensive testing strategy
- Scalability from day one
- Excellent developer experience
- Focus on user experience and accessibility

Timeline: 5 weeks for MVP, 3-6 months for full feature set.
