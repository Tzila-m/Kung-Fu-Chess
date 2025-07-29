import asyncio
import websockets
import json
import queue
import threading
import time
import logging
import pathlib
from typing import Dict, List, Set
import sys
import os

# Add the KFC_Py directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
kfc_py_path = os.path.join(current_dir, 'KFC_Py')
sys.path.insert(0, kfc_py_path)

from ServerGameFactory import create_server_game
from GraphicsFactory import ImgFactory
from Command import Command
from ServerGame import ServerGame

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChessServer:
    def __init__(self):
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.game = None
        self.command_queue = queue.Queue()
        self.game_state_lock = threading.Lock()
        self.running = False
        
    async def register_client(self, websocket):
        """Register a new client connection"""
        self.connected_clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.connected_clients)}")
        
        # Send current game state to new client
        if self.game:
            board_state = self.get_board_state()
            await websocket.send(json.dumps({
                "type": "board_state",
                "data": board_state
            }))
            
    async def unregister_client(self, websocket):
        """Remove a client connection"""
        self.connected_clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.connected_clients)}")
        
    async def handle_client_message(self, websocket, message):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "move":
                # Add move command to queue
                move_data = data.get("data")
                command = Command(
                    timestamp=int(time.time() * 1000),
                    piece_id=move_data.get("piece_id"),
                    type=move_data.get("type", "move"),
                    params=move_data.get("params", [])
                )
                self.command_queue.put(command)
                logger.info(f"Move command queued: {move_data}")
                
            elif message_type == "request_state":
                # Send current board state
                board_state = self.get_board_state()
                await websocket.send(json.dumps({
                    "type": "board_state",
                    "data": board_state
                }))
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from client")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            
    def get_board_state(self):
        """Get current board state for clients"""
        if not self.game:
            return {}
            
        with self.game_state_lock:
            # Update positions
            self.game._update_cell2piece_map()
            
            pieces_data = []
            for piece in self.game.pieces:
                cell = piece.current_cell()
                pieces_data.append({
                    "id": piece.id,
                    "position": cell,
                    "type": piece.id[0],  # First letter is piece type
                    "color": piece.id[1], # Second letter is color
                    "state": piece.state.name if piece.state else "idle"
                })
                
            return {
                "pieces": pieces_data,
                "board_size": (self.game.board.H_cells, self.game.board.W_cells),
                "timestamp": int(time.time() * 1000)
            }
            
    async def broadcast_game_state(self):
        """Broadcast current game state to all connected clients"""
        if not self.connected_clients:
            return
            
        board_state = self.get_board_state()
        message = json.dumps({
            "type": "board_state",
            "data": board_state
        })
        
        # Send to all clients
        disconnected = set()
        for client in self.connected_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(client)
                
        # Remove disconnected clients
        for client in disconnected:
            self.connected_clients.discard(client)
            
    def process_command_queue(self):
        """Process commands from the queue in game thread"""
        while not self.command_queue.empty():
            try:
                command = self.command_queue.get_nowait()
                with self.game_state_lock:
                    self.game._process_input(command)
                logger.info(f"Processed command: {command}")
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                
    def game_loop(self):
        """Main game loop running in separate thread"""
        logger.info("Game loop started")
        
        while self.running:
            try:
                with self.game_state_lock:
                    now = self.game.game_time_ms()
                    
                    # Update all pieces
                    self.game.update_pieces(now)
                    
                    # Process queued commands
                    self.process_command_queue()
                    
                    # Handle collisions
                    self.game._resolve_collisions()
                    
                # Small delay to prevent excessive CPU usage
                time.sleep(0.016)  # ~60 FPS
                
            except Exception as e:
                logger.error(f"Error in game loop: {e}")
                time.sleep(0.1)
                
    def start_game(self):
        """Initialize and start the chess game"""
        try:
            pieces_path = pathlib.Path("pieces")
            self.game = create_server_game(pieces_path, ImgFactory())
            self.game.initialize()
            logger.info("Chess game initialized")
            
            # Start game loop in separate thread
            self.running = True
            self.game_thread = threading.Thread(target=self.game_loop, daemon=True)
            self.game_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start game: {e}")
            raise
            
    async def client_handler(self, websocket, path):
        """Handle individual client connections"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
            
    async def broadcast_loop(self):
        """Periodically broadcast game state to clients"""
        while True:
            try:
                await self.broadcast_game_state()
                await asyncio.sleep(0.1)  # Broadcast 10 times per second
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)
                
    async def start_server(self, host="localhost", port=8765):
        """Start the WebSocket server"""
        logger.info(f"Starting chess server on {host}:{port}")
        
        # Start game
        self.start_game()
        
        # Start broadcast loop
        asyncio.create_task(self.broadcast_loop())
        
        # Start WebSocket server
        async with websockets.serve(self.client_handler, host, port):
            logger.info("Chess server running...")
            await asyncio.Future()  # Run forever
            
    def stop(self):
        """Stop the server"""
        self.running = False
        logger.info("Chess server stopped")

async def main():
    server = ChessServer()
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    finally:
        server.stop()

if __name__ == "__main__":
    asyncio.run(main())