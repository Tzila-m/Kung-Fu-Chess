"""
WebSocket Server for Kung Fu Chess
==================================

FastAPI-based WebSocket server that provides real-time chess gameplay
with event-driven updates and JSON state serialization.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import asdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from ..core.engine import ChessEngine, GameState, MoveResult
from ..core.board import Board
from ..core.piece import Piece
from ..bus.event_bus import EventBus, EventTopics

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.player_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, player_id: Optional[str] = None):
        """Accept and store a WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if player_id:
            self.player_connections[player_id] = websocket
        
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, player_id: Optional[str] = None):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if player_id and player_id in self.player_connections:
            del self.player_connections[player_id]
        
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
    
    async def send_to_player(self, message: str, player_id: str):
        """Send a message to a specific player."""
        websocket = self.player_connections.get(player_id)
        if websocket:
            await self.send_personal_message(message, websocket)
    
    async def broadcast(self, message: str):
        """Send a message to all connected clients."""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


class ChessWebSocketManager:
    """Manages chess game state and WebSocket communications."""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.chess_engine: Optional[ChessEngine] = None
        self.event_bus = EventBus()
        self.game_loop_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Subscribe to chess events
        self.event_bus.subscribe(EventTopics.GAME_STARTED, self._on_game_started)
        self.event_bus.subscribe(EventTopics.GAME_ENDED, self._on_game_ended)
        self.event_bus.subscribe(EventTopics.MOVE_LOGGED, self._on_move_logged)
        self.event_bus.subscribe(EventTopics.SCORE_UPDATED, self._on_score_updated)
        self.event_bus.subscribe(EventTopics.PIECE_CAPTURED, self._on_piece_captured)
    
    def initialize_game(self, pieces: List[Piece], board: Board):
        """Initialize the chess engine with pieces and board."""
        self.chess_engine = ChessEngine(pieces, board, self.event_bus)
        logger.info("Chess game initialized")
    
    def start_game_loop(self):
        """Start the game update loop."""
        if not self.is_running and self.chess_engine:
            self.is_running = True
            self.game_loop_task = asyncio.create_task(self._game_loop())
            logger.info("Game loop started")
    
    def stop_game_loop(self):
        """Stop the game update loop."""
        self.is_running = False
        if self.game_loop_task:
            self.game_loop_task.cancel()
            logger.info("Game loop stopped")
    
    async def _game_loop(self):
        """Main game update loop."""
        try:
            while self.is_running and self.chess_engine:
                # Update game state
                self.chess_engine.update()
                
                # Broadcast current state to all clients
                await self._broadcast_game_state()
                
                # Wait before next update (60 FPS)
                await asyncio.sleep(1/60)
        
        except asyncio.CancelledError:
            logger.info("Game loop cancelled")
        except Exception as e:
            logger.error(f"Error in game loop: {e}")
    
    async def handle_client_message(self, websocket: WebSocket, message: str, player_id: Optional[str] = None):
        """Handle incoming client messages."""
        try:
            # Try to parse as JSON first
            try:
                data = json.loads(message)
                if isinstance(data, dict) and "action" in data:
                    await self._handle_json_message(websocket, data, player_id)
                    return
            except json.JSONDecodeError:
                pass
            
            # Treat as PGN-style move command
            await self._handle_move_command(websocket, message, player_id)
            
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await self.connection_manager.send_personal_message(
                json.dumps({"error": str(e)}),
                websocket
            )
    
    async def _handle_json_message(self, websocket: WebSocket, data: Dict[str, Any], player_id: Optional[str]):
        """Handle structured JSON messages."""
        action = data.get("action")
        
        if action == "start_game":
            if self.chess_engine:
                self.chess_engine.start_game()
                self.start_game_loop()
        
        elif action == "get_state":
            await self._send_game_state(websocket)
        
        elif action == "make_move":
            move_str = data.get("move", "")
            await self._handle_move_command(websocket, move_str, player_id)
        
        else:
            await self.connection_manager.send_personal_message(
                json.dumps({"error": f"Unknown action: {action}"}),
                websocket
            )
    
    async def _handle_move_command(self, websocket: WebSocket, move_str: str, player_id: Optional[str]):
        """Handle move command from client."""
        if not self.chess_engine:
            await self.connection_manager.send_personal_message(
                json.dumps({"error": "Game not initialized"}),
                websocket
            )
            return
        
        # Execute the move
        result = self.chess_engine.make_move(move_str.strip())
        
        # Send result back to client
        response = {
            "type": "move_result",
            "success": result.success,
            "move": move_str,
            "player_id": player_id
        }
        
        if not result.success:
            response["error"] = result.error_message
        
        await self.connection_manager.send_personal_message(
            json.dumps(response),
            websocket
        )
        
        # If move was successful, broadcast new state
        if result.success:
            await self._broadcast_game_state()
    
    async def _send_game_state(self, websocket: WebSocket):
        """Send current game state to a specific client."""
        if not self.chess_engine:
            return
        
        state = self.chess_engine.get_game_state()
        message = {
            "type": "game_state",
            "state": asdict(state)
        }
        
        await self.connection_manager.send_personal_message(
            json.dumps(message),
            websocket
        )
    
    async def _broadcast_game_state(self):
        """Broadcast current game state to all clients."""
        if not self.chess_engine:
            return
        
        state = self.chess_engine.get_game_state()
        message = {
            "type": "game_state",
            "state": asdict(state)
        }
        
        await self.connection_manager.broadcast(json.dumps(message))
    
    # Event handlers
    async def _on_game_started(self, event_data: Any):
        """Handle game started event."""
        message = {
            "type": "game_started",
            "data": event_data
        }
        await self.connection_manager.broadcast(json.dumps(message))
    
    async def _on_game_ended(self, event_data: Any):
        """Handle game ended event."""
        message = {
            "type": "game_ended",
            "data": event_data
        }
        await self.connection_manager.broadcast(json.dumps(message))
        self.stop_game_loop()
    
    async def _on_move_logged(self, event_data: Any):
        """Handle move logged event."""
        message = {
            "type": "move_logged",
            "data": event_data
        }
        await self.connection_manager.broadcast(json.dumps(message))
    
    async def _on_score_updated(self, event_data: Any):
        """Handle score updated event."""
        message = {
            "type": "score_updated",
            "data": event_data
        }
        await self.connection_manager.broadcast(json.dumps(message))
    
    async def _on_piece_captured(self, event_data: Any):
        """Handle piece captured event."""
        message = {
            "type": "piece_captured",
            "data": event_data
        }
        await self.connection_manager.broadcast(json.dumps(message))


# Global chess manager instance
chess_manager = ChessWebSocketManager()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Kung Fu Chess WebSocket API",
        description="Real-time chess gameplay with WebSocket support",
        version="2.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """Main WebSocket endpoint for chess gameplay."""
        await chess_manager.connection_manager.connect(websocket)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                
                # Handle the message
                await chess_manager.handle_client_message(websocket, data)
        
        except WebSocketDisconnect:
            chess_manager.connection_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            chess_manager.connection_manager.disconnect(websocket)
    
    @app.websocket("/ws/{player_id}")
    async def websocket_player_endpoint(websocket: WebSocket, player_id: str):
        """WebSocket endpoint for specific players."""
        await chess_manager.connection_manager.connect(websocket, player_id)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                
                # Handle the message with player context
                await chess_manager.handle_client_message(websocket, data, player_id)
        
        except WebSocketDisconnect:
            chess_manager.connection_manager.disconnect(websocket, player_id)
        except Exception as e:
            logger.error(f"WebSocket error for player {player_id}: {e}")
            chess_manager.connection_manager.disconnect(websocket, player_id)
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Kung Fu Chess WebSocket API",
            "version": "2.0.0",
            "websocket_endpoint": "/ws",
            "player_endpoint": "/ws/{player_id}"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "active_connections": len(chess_manager.connection_manager.active_connections),
            "game_running": chess_manager.is_running
        }
    
    return app


def get_chess_manager() -> ChessWebSocketManager:
    """Get the global chess manager instance."""
    return chess_manager