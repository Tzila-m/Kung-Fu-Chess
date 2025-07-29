"""
FastAPI WebSocket API for Kung Fu Chess
Handles client connections and real-time game communication
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .engine import ChessEngine, create_initial_pieces, InvalidMove
from .command_queue import CommandQueue
from .bus import event_bus, GameEventTypes, Event

logger = logging.getLogger(__name__)

app = FastAPI(title="Kung Fu Chess Server", version="1.0.0")

# Global game state
chess_engine = ChessEngine()
command_queue = CommandQueue()
connected_clients: Dict[str, WebSocket] = {}
player_colors: Dict[str, str] = {}  # client_id -> color


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.player_assignments: Dict[str, str] = {}  # client_id -> color
        
    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Assign player color (first comes first served)
        if len(self.player_assignments) == 0:
            color = "white"
        elif len(self.player_assignments) == 1 and "white" in self.player_assignments.values():
            color = "black"
        elif len(self.player_assignments) == 1 and "black" in self.player_assignments.values():
            color = "white"
        else:
            # Game is full
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Game is full"
            }))
            await websocket.close()
            return False
        
        self.active_connections[client_id] = websocket
        self.player_assignments[client_id] = color
        
        logger.info(f"Client {client_id} connected as {color} player")
        
        # Notify about player joining
        await event_bus.publish_event(
            GameEventTypes.PLAYER_JOINED,
            {"client_id": client_id, "color": color}
        )
        
        # Send initial game state
        await self.send_personal_message(client_id, {
            "type": "player_assigned",
            "color": color
        })
        
        # Send current game state
        game_state = await chess_engine.get_game_state()
        await self.send_personal_message(client_id, {
            "type": "game_state",
            "state": game_state.to_dict()
        })
        
        return True
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        color = self.player_assignments.pop(client_id, None)
        if color:
            logger.info(f"Client {client_id} ({color}) disconnected")
            
            # Notify about player leaving
            asyncio.create_task(event_bus.publish_event(
                GameEventTypes.PLAYER_LEFT,
                {"client_id": client_id, "color": color}
            ))
    
    async def send_personal_message(self, client_id: str, message: dict):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict, exclude: Optional[str] = None):
        """Broadcast a message to all connected clients"""
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            if exclude and client_id == exclude:
                continue
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    def get_player_color(self, client_id: str) -> Optional[str]:
        """Get the player color for a client"""
        return self.player_assignments.get(client_id)


# Global connection manager
manager = ConnectionManager()


async def process_commands():
    """Background task to process commands from the queue"""
    while True:
        try:
            command = await command_queue.dequeue_blocking(timeout=1.0)
            if command is None:
                continue
            
            try:
                # Execute the move
                game_state = await chess_engine.execute_move(command.pgn, command.player_color)
                
                # Broadcast successful execution
                await manager.broadcast({
                    "type": "execute",
                    "pgn": command.pgn,
                    "player": command.player_color,
                    "board": game_state.to_dict()
                })
                
                # Publish event
                await event_bus.publish_event(
                    GameEventTypes.MOVE_EXECUTED,
                    {
                        "pgn": command.pgn,
                        "player_color": command.player_color,
                        "game_state": game_state.to_dict()
                    }
                )
                
                # Check for game over
                if chess_engine.is_game_over():
                    winner = chess_engine.get_winner()
                    await manager.broadcast({
                        "type": "game_over",
                        "winner": winner
                    })
                    
                    await event_bus.publish_event(
                        GameEventTypes.GAME_ENDED,
                        {"winner": winner}
                    )
                
            except InvalidMove as e:
                # Send error to the client who made the invalid move
                if command.client_id:
                    await manager.send_personal_message(command.client_id, {
                        "type": "error",
                        "message": str(e)
                    })
                
                await event_bus.publish_event(
                    GameEventTypes.MOVE_REJECTED,
                    {
                        "pgn": command.pgn,
                        "player_color": command.player_color,
                        "reason": str(e)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")


# Start command processing task
@app.on_event("startup")
async def startup_event():
    """Initialize the game and start background tasks"""
    # Initialize chess engine with starting pieces
    initial_pieces = create_initial_pieces()
    await chess_engine.initialize_game(initial_pieces)
    
    # Start command processing
    asyncio.create_task(process_commands())
    
    # Publish game started event
    await event_bus.publish_event(GameEventTypes.GAME_STARTED, {})
    
    logger.info("Kung Fu Chess server started")


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({"status": "ok", "service": "kung-fu-chess"})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for client connections"""
    client_id = f"client_{id(websocket)}"
    
    if not await manager.connect(websocket, client_id):
        return
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "command":
                pgn = message.get("pgn", "").strip()
                if not pgn:
                    await manager.send_personal_message(client_id, {
                        "type": "error",
                        "message": "Empty PGN command"
                    })
                    continue
                
                player_color = manager.get_player_color(client_id)
                if not player_color:
                    await manager.send_personal_message(client_id, {
                        "type": "error",
                        "message": "Player color not assigned"
                    })
                    continue
                
                # Validate and enqueue command
                if await chess_engine.is_legal_move(pgn, player_color):
                    success = await command_queue.enqueue_pgn(pgn, player_color, client_id)
                    if not success:
                        await manager.send_personal_message(client_id, {
                            "type": "error",
                            "message": "Command queue is full"
                        })
                else:
                    await manager.send_personal_message(client_id, {
                        "type": "error",
                        "message": "Illegal move"
                    })
            
            elif message.get("type") == "ping":
                await manager.send_personal_message(client_id, {
                    "type": "pong"
                })
            
            else:
                await manager.send_personal_message(client_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message.get('type')}"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)