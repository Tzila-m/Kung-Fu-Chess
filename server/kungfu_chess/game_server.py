"""
Game Server - Server-side wrapper for the existing Game class
Provides WebSocket interface and command queue management
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Set, Any
from collections import deque
from datetime import datetime

from .Game import Game
from .Command import Command
from .GameFactory import create_game
from .GraphicsFactory import ImgFactory

logger = logging.getLogger(__name__)


class CommandQueue:
    """Thread-safe command queue for game commands"""
    
    def __init__(self):
        self._queue = deque()
        self._lock = asyncio.Lock()
        
    async def put(self, command: Command) -> None:
        """Add command to queue"""
        async with self._lock:
            self._queue.append(command)
            logger.debug(f"Command queued: {command}")
    
    async def get(self) -> Optional[Command]:
        """Get next command from queue"""
        async with self._lock:
            if self._queue:
                return self._queue.popleft()
            return None
    
    async def size(self) -> int:
        """Get queue size"""
        async with self._lock:
            return len(self._queue)


class GameServer:
    """
    Server wrapper around the existing Game class
    Manages WebSocket connections and game state
    """
    
    def __init__(self, pieces_path: str = "pieces"):
        # Create the game using existing factory
        self.game: Game = create_game(pieces_path, ImgFactory())
        
        # Server-specific additions
        self.command_queue = CommandQueue()
        self.connected_clients: Dict[str, Any] = {}  # websocket connections
        self.player_assignments: Dict[str, str] = {}  # client_id -> "white" or "black"
        self.game_state_cache: Optional[Dict] = None
        self.last_update_time = 0
        
        # Override the game's input handling
        self._setup_server_mode()
        
    def _setup_server_mode(self):
        """Setup the game for server mode (no keyboard input)"""
        # We'll handle input through WebSocket instead of keyboard
        # The game's user_input_queue will be fed by our command queue
        # Disable keyboard input threads
        self.game.keyboard_processor = None
        self.game.keyboard_producer = None
    
    async def add_client(self, client_id: str, websocket) -> str:
        """Add a new client and assign player color"""
        # Assign color based on existing connections
        if len(self.player_assignments) == 0:
            color = "white"
        elif len(self.player_assignments) == 1:
            # Assign the opposite color
            existing_color = list(self.player_assignments.values())[0]
            color = "black" if existing_color == "white" else "white"
        else:
            # Game is full
            raise ValueError("Game is full - maximum 2 players")
        
        self.connected_clients[client_id] = websocket
        self.player_assignments[client_id] = color
        
        logger.info(f"Client {client_id} joined as {color} player")
        return color
    
    def remove_client(self, client_id: str):
        """Remove a client"""
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
        if client_id in self.player_assignments:
            color = self.player_assignments[client_id]
            del self.player_assignments[client_id]
            logger.info(f"Client {client_id} ({color}) disconnected")
    
    async def process_command(self, client_id: str, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a command from a client"""
        try:
            command_type = command_data.get("type")
            
            if command_type == "move":
                return await self._process_move_command(client_id, command_data)
            elif command_type == "get_state":
                return await self._get_game_state()
            else:
                return {"type": "error", "message": f"Unknown command type: {command_type}"}
                
        except Exception as e:
            logger.error(f"Error processing command from {client_id}: {e}")
            return {"type": "error", "message": str(e)}
    
    async def _process_move_command(self, client_id: str, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a move command"""
        if client_id not in self.player_assignments:
            return {"type": "error", "message": "Player not assigned"}
        
        player_color = self.player_assignments[client_id]
        piece_id = command_data.get("piece_id")
        move_type = command_data.get("move_type", "move")
        params = command_data.get("params", [])
        
        if not piece_id:
            return {"type": "error", "message": "Missing piece_id"}
        
        # Verify player owns this piece
        if not self._player_owns_piece(player_color, piece_id):
            return {"type": "error", "message": "You don't own this piece"}
        
        # Create command using existing Command class
        timestamp = self.game.game_time_ms()
        command = Command(timestamp, piece_id, move_type, params)
        
        # Add to command queue
        await self.command_queue.put(command)
        
        return {"type": "command_accepted", "piece_id": piece_id}
    
    def _player_owns_piece(self, player_color: str, piece_id: str) -> bool:
        """Check if player owns the piece"""
        # Piece ID format is like "PW_0" for white pawn, "KB_0" for black king
        piece_color = piece_id[1] if len(piece_id) > 1 else ""
        return (player_color == "white" and piece_color == "W") or \
               (player_color == "black" and piece_color == "B")
    
    async def _get_game_state(self) -> Dict[str, Any]:
        """Get current game state"""
        # Extract piece positions and states
        pieces_data = []
        for piece in self.game.pieces:
            piece_data = {
                "id": piece.id,
                "position": piece.current_cell(),
                "state": piece.state.__class__.__name__ if hasattr(piece.state, '__class__') else "unknown"
            }
            pieces_data.append(piece_data)
        
        game_state = {
            "type": "game_state",
            "pieces": pieces_data,
            "game_time": self.game.game_time_ms(),
            "board_size": (self.game.board.H_cells, self.game.board.W_cells),
            "is_game_over": self.game._is_win() if hasattr(self.game, '_is_win') else False
        }
        
        return game_state
    
    async def run_game_loop(self):
        """Main game loop that processes commands and updates game state"""
        logger.info("Starting game loop")
        
        # Initialize game without keyboard threads
        start_ms = self.game.START_NS
        for piece in self.game.pieces:
            piece.reset(start_ms)
        
        while True:
            try:
                # Process pending commands
                while True:
                    command = await self.command_queue.get()
                    if not command:
                        break
                    
                    # Add command to game's input queue
                    self.game.user_input_queue.put(command)
                
                # Run one iteration of the game loop
                now = self.game.game_time_ms()
                
                # Update all pieces
                for piece in self.game.pieces:
                    piece.update(now)
                
                # Update position mapping
                self.game._update_cell2piece_map()
                
                # Process any commands in the game's queue
                while not self.game.user_input_queue.empty():
                    cmd = self.game.user_input_queue.get()
                    self.game._process_input(cmd)
                
                # Resolve collisions
                self.game._resolve_collisions()
                
                # Check if we need to broadcast state update
                if now - self.last_update_time > 100:  # Update every 100ms
                    await self._broadcast_game_state()
                    self.last_update_time = now
                
                # Check for game over
                if self.game._is_win():
                    await self._broadcast_game_over()
                    break
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in game loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _broadcast_game_state(self):
        """Broadcast current game state to all clients"""
        if not self.connected_clients:
            return
        
        game_state = await self._get_game_state()
        message = json.dumps(game_state)
        
        # Send to all connected clients
        disconnected_clients = []
        for client_id, websocket in self.connected_clients.items():
            try:
                await websocket.send(message)
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.remove_client(client_id)
    
    async def _broadcast_game_over(self):
        """Broadcast game over message"""
        # Determine winner
        kings = [p for p in self.game.pieces if p.id.startswith(('KW', 'KB'))]
        if len(kings) == 1:
            winner = "White" if kings[0].id.startswith('KW') else "Black"
        else:
            winner = "Draw"
        
        message = json.dumps({
            "type": "game_over",
            "winner": winner
        })
        
        for client_id, websocket in self.connected_clients.items():
            try:
                await websocket.send(message)
            except Exception as e:
                logger.error(f"Error sending game over to client {client_id}: {e}")