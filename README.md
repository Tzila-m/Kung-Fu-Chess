# Kung Fu Chess - Real-time Chess with Event-driven Architecture

פרויקט Kung Fu Chess מורחב - חלקים 2 ו-3

A Python implementation of Kung Fu Chess featuring real-time gameplay, event-driven architecture via Pub/Sub messaging, and WebSocket API support.

## 🚀 Features

- **🎮 Real-time Chess Engine**: Based on existing Iter A implementation with enhanced capabilities
- **📡 Event-driven Architecture**: Pub/Sub event bus using Observer pattern
- **🔌 WebSocket API**: FastAPI-based real-time multiplayer support
- **🧪 Comprehensive Testing**: >90% test coverage with pytest
- **📦 Modular Design**: Clean separation between core engine, event system, and API

## 📁 Project Structure

```
kungfu_chess/
├── core/          # Chess engine (Iter A base + enhancements)
│   ├── engine.py     # Enhanced ChessEngine with EventBus integration
│   ├── game.py       # Original Game class
│   ├── board.py      # Board representation
│   ├── piece.py      # Chess pieces
│   └── ...          # Other core components
├── bus/           # Pub/Sub Event System (Part 2)
│   └── event_bus.py  # EventBus implementation with Observer pattern
├── api/           # WebSocket API (Part 3)
│   └── server.py     # FastAPI WebSocket server
└── __init__.py

tests/
├── test_event_bus_isolated.py  # EventBus tests (90%+ coverage)
├── test_api.py                 # WebSocket API tests
└── ...

main.py            # Server entry point
requirements.txt    # Dependencies
pytest.ini          # Test configuration
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+ (tested with Python 3.13)
- pip package manager

### Dependencies Installation

1. **Using pip with virtual environment (recommended)**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Using system packages**:
```bash
# On Ubuntu/Debian
sudo apt install python3-fastapi python3-uvicorn python3-websockets python3-pytest python3-opencv

# Or using pip with --break-system-packages
python3 -m pip install --break-system-packages -r requirements.txt
```

### Core Dependencies

- **FastAPI**: Web framework for WebSocket API
- **Uvicorn**: ASGI server
- **WebSockets**: Real-time communication
- **OpenCV & Pillow**: Image processing for chess engine
- **Pytest**: Testing framework with async and coverage support

## 🎯 Part 2: Event Bus (Pub/Sub)

### EventBus Implementation

The EventBus uses the Observer pattern with the following interface:

```python
from kungfu_chess.bus.event_bus import EventBus, EventTopics

# Create event bus
bus = EventBus()

# Subscribe to events
def on_score_updated(score_data):
    print(f"Score updated: {score_data}")

bus.subscribe(EventTopics.SCORE_UPDATED, on_score_updated)

# Publish events
bus.publish(EventTopics.SCORE_UPDATED, {"white": 5, "black": 3})
```

### Required Events

- `score_updated` - Score changes
- `move_logged` - Move recording
- `sound_request` - Audio triggers
- `game_started` / `game_ended` - Game lifecycle
- `piece_moved` / `piece_captured` - Game actions

### ChessEngine Integration

The enhanced `ChessEngine` class integrates the EventBus via dependency injection:

```python
from kungfu_chess.core.engine import ChessEngine
from kungfu_chess.bus.event_bus import EventBus

# Create engine with event bus
event_bus = EventBus()
engine = ChessEngine(pieces, board, event_bus)

# Events are automatically published during gameplay
engine.start_game()  # Publishes game_started
result = engine.make_move("WQe2e5")  # Publishes move_logged, piece_moved
```

## 🌐 Part 3: WebSocket Server

### FastAPI WebSocket API

Real-time chess gameplay via WebSocket connections:

```python
# Server endpoints
GET  /              # API information
GET  /health        # Health check
WS   /ws            # General WebSocket connection
WS   /ws/{player_id} # Player-specific connection
```

### Client Communication

**Client → Server** (PGN-style commands):
```
WQe2e5  # Move white queen from e2 to e5
```

**Client → Server** (JSON commands):
```json
{"action": "start_game"}
{"action": "get_state"}
{"action": "make_move", "move": "WQe2e5"}
```

**Server → Client** (JSON responses):
```json
{
  "type": "game_state",
  "state": {
    "fen": "WQ:e5|BK:e8|...",
    "cooldowns": {"WQ": 0.0, "BK": 2.5},
    "scores": {"white": 5, "black": 3},
    "game_time_ms": 45000,
    "is_game_over": false
  }
}
```

## 🚀 Usage

### Starting the Server

```bash
# Run the WebSocket server
python3 main.py

# Server starts on http://localhost:8000
# WebSocket endpoint: ws://localhost:8000/ws
# Player endpoint: ws://localhost:8000/ws/{player_id}
```

### Testing WebSocket Connection

Using `websocat` or similar WebSocket client:

```bash
# Install websocat
curl -L https://github.com/vi/websocat/releases/latest/download/websocat.x86_64-unknown-linux-musl --output websocat
chmod +x websocat

# Connect to server
./websocat ws://localhost:8000/ws

# Send commands
{"action": "start_game"}
WQe2e5
{"action": "get_state"}
```

### Python Client Example

```python
import asyncio
import websockets
import json

async def chess_client():
    uri = "ws://localhost:8000/ws/player1"
    
    async with websockets.connect(uri) as websocket:
        # Start game
        await websocket.send(json.dumps({"action": "start_game"}))
        
        # Make a move
        await websocket.send("WQe2e5")
        
        # Listen for responses
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(chess_client())
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python3 -m pytest

# Run with coverage
python3 -m pytest --cov=kungfu_chess --cov-report=html

# Run specific test module
python3 -m pytest tests/test_event_bus_isolated.py -v

# Run WebSocket tests
python3 -m pytest tests/test_api.py -v
```

### Test Coverage

The project maintains >90% test coverage:

- **EventBus Tests**: Complete coverage of Pub/Sub functionality
- **API Tests**: WebSocket connection management and message handling
- **Integration Tests**: End-to-end scenarios

### Coverage Report

```bash
# Generate HTML coverage report
python3 -m pytest --cov=kungfu_chess --cov-report=html
# Open htmlcov/index.html in browser
```

## 🏗️ Architecture

### Event Flow

```
Client → WebSocket → ChessEngine → EventBus → Subscribers
   ↑                                               ↓
   ←─────── JSON Response ←─── WebSocket ←─────────
```

1. **Client** sends move via WebSocket
2. **WebSocket handler** processes message
3. **ChessEngine** validates and executes move
4. **EventBus** publishes events (move_logged, score_updated, etc.)
5. **WebSocket manager** subscribes to events and broadcasts to clients

### Key Design Principles

- **Separation of Concerns**: Core engine, event system, and API are independent
- **Dependency Injection**: EventBus is injected into ChessEngine
- **Observer Pattern**: EventBus implements classic pub/sub messaging
- **Real-time Communication**: WebSocket for low-latency updates
- **Comprehensive Testing**: High coverage with isolated and integration tests

## 🔧 Development

### Code Style

The project follows PEP8 guidelines:

```bash
# Format code
black kungfu_chess/ tests/

# Lint code
flake8 kungfu_chess/ tests/

# Type checking
mypy kungfu_chess/
```

### Adding New Events

1. Add event topic to `EventTopics` class:
```python
class EventTopics:
    NEW_EVENT = "new_event"
```

2. Publish in appropriate location:
```python
self.event_bus.publish(EventTopics.NEW_EVENT, event_data)
```

3. Subscribe in consumers:
```python
bus.subscribe(EventTopics.NEW_EVENT, handler_function)
```

## 📝 API Reference

### EventBus Methods

- `subscribe(topic: str, callback: Callable)` - Subscribe to topic
- `unsubscribe(topic: str, callback: Callable)` - Unsubscribe from topic  
- `publish(topic: str, payload: Any)` - Publish event
- `get_subscribers_count(topic: str)` - Get subscriber count
- `get_all_topics()` - List all topics
- `clear_all()` - Remove all subscriptions

### ChessEngine Methods

- `start_game()` - Initialize game and publish game_started
- `make_move(move_str: str)` - Execute move with validation
- `get_game_state()` - Get current game state for serialization
- `update()` - Update game state (call regularly)

### WebSocket Messages

**Incoming (Client → Server)**:
- `"WQe2e5"` - PGN-style move command
- `{"action": "start_game"}` - Start new game
- `{"action": "get_state"}` - Request current state
- `{"action": "make_move", "move": "..."}` - Make move

**Outgoing (Server → Client)**:
- `{"type": "game_state", "state": {...}}` - Current game state
- `{"type": "move_result", "success": bool, ...}` - Move result
- `{"type": "game_started", "data": {...}}` - Game started event
- `{"type": "score_updated", "data": {...}}` - Score change

## 🤝 Contributing

1. Follow PEP8 style guidelines
2. Add tests for new functionality
3. Maintain >90% test coverage
4. Add type hints for all functions
5. Document new features in README

## 📄 License

This project is part of the CTD25 course implementation.

---

**Ready for Real-time Chess! 🚀♟️**