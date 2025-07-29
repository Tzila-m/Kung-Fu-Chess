# Chess Client-Server System 🏰♟️

A real-time multiplayer chess game with visual clients that synchronize moves through a central server.

## 📁 Project Structure

```
project/
├── server/                 # Chess Server
│   ├── KFC_Py/            # Game logic classes
│   ├── pieces/            # Chess piece sprites and data
│   ├── chess_server.py    # Main server application
│   ├── start_server.py    # Server startup script
│   └── requirements.txt   # Server dependencies
├── client/                 # Chess Client
│   ├── KFC_Py/            # Game logic classes (client copy)
│   ├── pieces/            # Chess piece sprites and data
│   ├── chess_client.py    # Main client application
│   ├── start_client.py    # Client startup script
│   └── requirements.txt   # Client dependencies
└── CTD25_Solutions/       # Original source code
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Install Server Dependencies:**
```bash
cd server
pip install -r requirements.txt
```

2. **Install Client Dependencies:**
```bash
cd client
pip install -r requirements.txt
```

### Running the System

#### 1. Start the Server
```bash
cd server
python start_server.py
```
The server will start on `localhost:8765` and display:
- Connected clients count
- Game state updates
- Move commands from clients

#### 2. Start Client(s)
Open new terminal windows for each client:

**Client 1:**
```bash
cd client
python start_client.py
```

**Client 2:**
```bash
cd client
python start_client.py
```

You can run multiple clients simultaneously - they will all show the same synchronized chess board!

## 🎮 How to Play

### Visual Interface
- **Chess Board**: Standard 8x8 chess board with pieces
- **Status Bar**: Shows piece count and connection status
- **Piece Selection**: Yellow highlight shows selected piece

### Controls
1. **Select Piece**: Left-click on any chess piece
2. **Move Piece**: Left-click on destination square
3. **Deselect**: Click the same piece again
4. **Close**: Close the window to exit

### Game Features
- ✅ Real-time synchronization across all clients
- ✅ Visual piece movements and animations
- ✅ Standard chess piece starting positions
- ✅ Command queuing system
- ✅ Automatic reconnection
- ✅ Multiple client support

## 🏗️ Architecture

### Server Components
- **WebSocket Server**: Handles client connections
- **Game Engine**: Processes chess moves and rules
- **Command Queue**: Queues moves from multiple clients
- **State Manager**: Maintains synchronized game state
- **Broadcasting**: Sends updates to all connected clients

### Client Components
- **Pygame Display**: Visual chess board and pieces
- **WebSocket Client**: Communicates with server
- **Mouse Handler**: Captures piece selection and moves
- **State Synchronizer**: Updates display from server data

### Communication Protocol

**Move Command (Client → Server):**
```json
{
  "type": "move",
  "data": {
    "piece_id": "PW_7_0",
    "type": "move", 
    "params": [[6, 0]]
  }
}
```

**Board State (Server → Client):**
```json
{
  "type": "board_state",
  "data": {
    "pieces": [
      {
        "id": "KW_7_4",
        "position": [7, 4],
        "type": "K",
        "color": "W",
        "state": "idle"
      }
    ],
    "board_size": [8, 8],
    "timestamp": 1640995200000
  }
}
```

## 🎯 Key Features

### Real-time Synchronization
- All connected clients see moves instantly
- Server maintains authoritative game state
- Automatic conflict resolution

### Visual Experience
- Animated chess pieces with sprites
- Chess piece images for all piece types
- Intuitive click-to-move interface
- Real-time connection status

### Network Architecture
- WebSocket-based communication
- Command queue for move processing
- Broadcast updates to all clients
- Robust error handling and reconnection

## 🔧 Technical Details

### Chess Pieces
The system includes full sprite sets for all chess pieces:
- **King (K)**, **Queen (Q)**, **Rook (R)**, **Bishop (B)**, **Knight (N)**, **Pawn (P)**
- **White (W)** and **Black (B)** colors
- Multiple animation states (idle, move, jump, etc.)

### Game Logic
- Based on the original KFC_Py chess engine
- Proper chess move validation
- Collision detection and piece capture
- State machine for piece behaviors

### Performance
- 60 FPS client rendering
- 10 Hz server state broadcasting
- Efficient sprite loading and caching
- Threaded game loop for smooth performance

## 🐛 Troubleshooting

### Server Won't Start
- Check if port 8765 is available
- Verify all dependencies are installed
- Ensure pieces directory exists in server folder

### Client Won't Connect
- Make sure server is running first
- Check firewall settings
- Verify server address is correct

### Missing Piece Graphics
- Ensure pieces directory is copied to client folder
- Check PNG files exist in pieces/*/states/idle/sprites/
- Verify file permissions

### Poor Performance
- Close unnecessary applications
- Reduce number of connected clients
- Check system resources (CPU/Memory)

## 📈 Future Enhancements

- [ ] Chess rule validation
- [ ] Player authentication
- [ ] Game recording and replay
- [ ] Tournament mode
- [ ] Sound effects
- [ ] Network play over internet
- [ ] AI opponents

## 🤝 Contributing

This project is based on the CTD25 chess engine. To contribute:

1. Make changes to the original code in `CTD25_Solutions/`
2. Copy updates to both `server/` and `client/` directories
3. Test with multiple clients
4. Document any new features

## 📝 License

Based on the original CTD25_Solutions chess project.