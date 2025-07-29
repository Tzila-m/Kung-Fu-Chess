"""
WebSocket Client for Kung Fu Chess
Handles communication with the game server
"""
import asyncio
import json
import logging
from typing import AsyncIterator, Dict, Any, Optional, Callable
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


class WSClient:
    """
    WebSocket client for communicating with the Kung Fu Chess server
    """
    
    def __init__(self, server_url: str, color: str):
        self.server_url = server_url
        self.color = color
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        self._event_handlers: Dict[str, Callable] = {}
        self._running = False
        
    async def connect(self) -> bool:
        """
        Connect to the WebSocket server
        Returns True if successful, False otherwise
        """
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            logger.info(f"Connected to server as {self.color} player")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the server"""
        self._running = False
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        self.connected = False
        logger.info("Disconnected from server")
    
    async def send_command(self, pgn: str) -> None:
        """
        Send a move command to the server
        
        Args:
            pgn: The move in PGN notation (e.g., "Qe2e5")
        """
        if not self.connected or not self.websocket:
            logger.error("Not connected to server")
            return
        
        message = {
            "type": "command",
            "pgn": pgn
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent command: {pgn}")
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            self.connected = False
    
    async def send_ping(self) -> None:
        """Send a ping to the server"""
        if not self.connected or not self.websocket:
            return
        
        try:
            await self.websocket.send(json.dumps({"type": "ping"}))
        except Exception as e:
            logger.error(f"Failed to send ping: {e}")
            self.connected = False
    
    def register_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Register an event handler for specific message types
        
        Args:
            event_type: The message type to handle (e.g., "execute", "error")
            handler: Function to call when this event is received
        """
        self._event_handlers[event_type] = handler
    
    async def events(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Async generator that yields events from the server
        
        Yields:
            Dict containing the event data
        """
        if not self.connected or not self.websocket:
            logger.error("Not connected to server")
            return
        
        self._running = True
        
        try:
            while self._running and not self.websocket.closed:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=30.0  # 30 second timeout
                    )
                    
                    try:
                        event = json.loads(message)
                        logger.debug(f"Received event: {event.get('type', 'unknown')}")
                        
                        # Call registered handler if available
                        event_type = event.get('type')
                        if event_type in self._event_handlers:
                            try:
                                self._event_handlers[event_type](event)
                            except Exception as e:
                                logger.error(f"Error in event handler for {event_type}: {e}")
                        
                        yield event
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message: {e}")
                        continue
                
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await self.send_ping()
                    continue
                
                except ConnectionClosed:
                    logger.info("Server connection closed")
                    break
                    
                except WebSocketException as e:
                    logger.error(f"WebSocket error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in event loop: {e}")
        finally:
            self.connected = False
            self._running = False
    
    async def listen_for_events(self, event_callback: Callable[[Dict[str, Any]], None]):
        """
        Listen for events and call the callback for each one
        
        Args:
            event_callback: Function to call for each received event
        """
        async for event in self.events():
            try:
                event_callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    def is_connected(self) -> bool:
        """Check if the client is connected"""
        return self.connected and self.websocket and not self.websocket.closed


# Convenience function to create a client
def create_client(server_url: str = "ws://localhost:8000/ws", color: str = "white") -> WSClient:
    """
    Create a new WSClient instance
    
    Args:
        server_url: WebSocket server URL
        color: Player color ("white" or "black")
    
    Returns:
        WSClient instance
    """
    return WSClient(server_url, color)