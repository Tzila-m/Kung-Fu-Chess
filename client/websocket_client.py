"""
WebSocket Client for Kung Fu Chess
Handles communication with the game server
"""
import asyncio
import json
import logging
import websockets
from websockets.client import WebSocketClientProtocol
from typing import Optional, Callable, Dict, Any
import threading

logger = logging.getLogger(__name__)


class GameClient:
    """WebSocket client for Kung Fu Chess"""
    
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.client_id: Optional[str] = None
        self.player_color: Optional[str] = None
        self.connected = False
        self.running = False
        
        # Callbacks
        self.on_game_state: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_game_over: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_connected: Optional[Callable[[str], None]] = None
        
        # Event loop for async operations
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.client_thread: Optional[threading.Thread] = None
        
    def set_callbacks(self, 
                     on_game_state: Optional[Callable[[Dict[str, Any]], None]] = None,
                     on_game_over: Optional[Callable[[str], None]] = None,
                     on_error: Optional[Callable[[str], None]] = None,
                     on_connected: Optional[Callable[[str], None]] = None):
        """Set callback functions for events"""
        if on_game_state:
            self.on_game_state = on_game_state
        if on_game_over:
            self.on_game_over = on_game_over
        if on_error:
            self.on_error = on_error
        if on_connected:
            self.on_connected = on_connected
    
    def start(self):
        """Start the client in a separate thread"""
        if self.running:
            return
            
        self.running = True
        self.client_thread = threading.Thread(target=self._run_client, daemon=True)
        self.client_thread.start()
    
    def stop(self):
        """Stop the client"""
        self.running = False
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._disconnect(), self.loop)
    
    def _run_client(self):
        """Run the client event loop in a separate thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._client_loop())
        except Exception as e:
            logger.error(f"Client loop error: {e}")
            if self.on_error:
                self.on_error(str(e))
        finally:
            self.loop.close()
    
    async def _client_loop(self):
        """Main client loop"""
        while self.running:
            try:
                await self._connect()
                await self._handle_messages()
            except websockets.exceptions.ConnectionClosed:
                logger.info("Connection closed by server")
                if self.on_error:
                    self.on_error("Connection closed by server")
            except Exception as e:
                logger.error(f"Connection error: {e}")
                if self.on_error:
                    self.on_error(str(e))
            
            if self.running:
                logger.info("Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)
    
    async def _connect(self):
        """Connect to the WebSocket server"""
        logger.info(f"Connecting to {self.server_url}")
        self.websocket = await websockets.connect(self.server_url)
        self.connected = True
        logger.info("Connected successfully")
    
    async def _disconnect(self):
        """Disconnect from the server"""
        if self.websocket:
            await self.websocket.close()
        self.connected = False
        self.websocket = None
    
    async def _handle_messages(self):
        """Handle incoming messages from server"""
        if not self.websocket:
            return
            
        async for message in self.websocket:
            try:
                data = json.loads(message)
                await self._process_message(data)
            except json.JSONDecodeError:
                logger.error("Received invalid JSON from server")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process a message from the server"""
        message_type = data.get("type")
        
        if message_type == "welcome":
            self.client_id = data.get("client_id")
            self.player_color = data.get("color")
            logger.info(f"Welcomed as {self.player_color} player (ID: {self.client_id})")
            if self.on_connected:
                self.on_connected(self.player_color)
                
        elif message_type == "game_state":
            if self.on_game_state:
                self.on_game_state(data)
                
        elif message_type == "game_over":
            winner = data.get("winner", "Unknown")
            logger.info(f"Game over! Winner: {winner}")
            if self.on_game_over:
                self.on_game_over(winner)
                
        elif message_type == "error":
            error_msg = data.get("message", "Unknown error")
            logger.error(f"Server error: {error_msg}")
            if self.on_error:
                self.on_error(error_msg)
                
        elif message_type == "command_accepted":
            logger.debug(f"Command accepted: {data}")
            
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    def send_move(self, piece_id: str, move_type: str = "move", params: list = None):
        """Send a move command to the server"""
        if not self.connected or not self.websocket:
            logger.warning("Not connected to server")
            return
            
        if params is None:
            params = []
        
        command = {
            "type": "move",
            "piece_id": piece_id,
            "move_type": move_type,
            "params": params
        }
        
        # Send via the event loop
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self._send_message(command), 
                self.loop
            )
    
    async def _send_message(self, message: Dict[str, Any]):
        """Send a message to the server"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
                logger.debug(f"Sent message: {message}")
            except Exception as e:
                logger.error(f"Error sending message: {e}")
    
    def request_game_state(self):
        """Request current game state from server"""
        if not self.connected:
            return
            
        command = {"type": "get_state"}
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self._send_message(command),
                self.loop
            )