#!/usr/bin/env python3
"""
WebSocket Server for Kung Fu Chess
Uses the existing game engine with client/server architecture
"""
import asyncio
import json
import logging
import websockets
from websockets.server import WebSocketServerProtocol
from typing import Set
import uuid

from kungfu_chess.game_server import GameServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KungFuChessServer:
    """Main WebSocket server for Kung Fu Chess"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.game_server = GameServer()
        self.running = False
        
    async def register_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new client connections"""
        client_id = str(uuid.uuid4())
        logger.info(f"New client connecting: {client_id}")
        
        try:
            # Add client to game
            color = await self.game_server.add_client(client_id, websocket)
            
            # Send welcome message
            welcome_msg = {
                "type": "welcome",
                "client_id": client_id,
                "color": color
            }
            await websocket.send(json.dumps(welcome_msg))
            
            # Send initial game state
            game_state = await self.game_server._get_game_state()
            await websocket.send(json.dumps(game_state))
            
            # Handle client messages
            await self.handle_client_messages(client_id, websocket)
            
        except ValueError as e:
            # Game is full
            error_msg = {"type": "error", "message": str(e)}
            await websocket.send(json.dumps(error_msg))
            await websocket.close()
            
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
            
        finally:
            # Clean up
            self.game_server.remove_client(client_id)
            logger.info(f"Client {client_id} disconnected")
    
    async def handle_client_messages(self, client_id: str, websocket: WebSocketServerProtocol):
        """Handle messages from a specific client"""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.debug(f"Received from {client_id}: {data}")
                    
                    # Process command
                    response = await self.game_server.process_command(client_id, data)
                    
                    # Send response back to client
                    if response:
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError:
                    error_msg = {"type": "error", "message": "Invalid JSON"}
                    await websocket.send(json.dumps(error_msg))
                    
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
                    error_msg = {"type": "error", "message": str(e)}
                    await websocket.send(json.dumps(error_msg))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} connection closed")
        except Exception as e:
            logger.error(f"Error in client message handler for {client_id}: {e}")
    
    async def start_server(self):
        """Start the WebSocket server and game loop"""
        logger.info(f"Starting Kung Fu Chess server on {self.host}:{self.port}")
        
        # Start the game loop
        game_task = asyncio.create_task(self.game_server.run_game_loop())
        
        # Start the WebSocket server
        server = await websockets.serve(
            self.register_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        self.running = True
        logger.info("Server started successfully!")
        logger.info("Waiting for clients to connect...")
        
        try:
            # Keep the server running
            await asyncio.gather(
                server.wait_closed(),
                game_task
            )
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.running = False
            server.close()
            await server.wait_closed()
            logger.info("Server stopped")


async def main():
    """Main entry point"""
    server = KungFuChessServer()
    await server.start_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server startup error: {e}")
        exit(1)