#!/usr/bin/env python3
"""
Simple Kung Fu Chess Client for testing without GUI
"""
import asyncio
import json
import logging
import websockets
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleClient:
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket: Optional = None
        self.player_color: Optional[str] = None
        self.client_id: Optional[str] = None
        
    async def connect(self):
        """Connect to the server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            logger.info(f"Connected to {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def listen(self):
        """Listen for messages from server"""
        if not self.websocket:
            return
            
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
    
    async def handle_message(self, data):
        """Handle incoming messages"""
        msg_type = data.get("type")
        
        if msg_type == "welcome":
            self.client_id = data.get("client_id")
            self.player_color = data.get("color")
            logger.info(f"Welcomed as {self.player_color} player (ID: {self.client_id})")
            
        elif msg_type == "game_state":
            pieces = data.get("pieces", [])
            game_time = data.get("game_time", 0)
            logger.info(f"Game state received: {len(pieces)} pieces, time: {game_time}ms")
            
            # Print piece positions
            for piece in pieces[:5]:  # Show first 5 pieces
                piece_id = piece.get("id", "?")
                pos = piece.get("position", (0, 0))
                logger.info(f"  {piece_id}: {pos}")
            
        elif msg_type == "game_over":
            winner = data.get("winner", "Unknown")
            logger.info(f"🎉 Game Over! Winner: {winner}")
            
        elif msg_type == "error":
            error_msg = data.get("message", "Unknown error")
            logger.error(f"❌ Server error: {error_msg}")
            
        elif msg_type == "command_accepted":
            piece_id = data.get("piece_id", "")
            logger.info(f"✅ Move accepted for piece {piece_id}")
            
        else:
            logger.warning(f"Unknown message type: {msg_type}")
    
    async def send_move(self, piece_id: str, move_type: str = "move", params: list = None):
        """Send a move command"""
        if not self.websocket:
            logger.warning("Not connected")
            return
            
        if params is None:
            params = []
        
        command = {
            "type": "move",
            "piece_id": piece_id,
            "move_type": move_type,
            "params": params
        }
        
        try:
            await self.websocket.send(json.dumps(command))
            logger.info(f"📤 Sent move: {piece_id} {move_type} {params}")
        except Exception as e:
            logger.error(f"Error sending move: {e}")
    
    async def run(self):
        """Main client loop"""
        if not await self.connect():
            return 1
        
        # Start listening for messages
        listen_task = asyncio.create_task(self.listen())
        
        # Wait a moment for initial game state
        await asyncio.sleep(2)
        
        # Send some test moves if we're connected
        if self.player_color:
            logger.info(f"🎮 Starting test moves for {self.player_color} player...")
            
            # Try to move a pawn (common piece)
            if self.player_color == "white":
                # Move white pawn from e2 to e4
                await self.send_move("PW_4", "move", ["e2", "e4"])
                await asyncio.sleep(1)
                await self.send_move("PW_4", "move", ["e4", "e5"])
            else:
                # Move black pawn from e7 to e5
                await self.send_move("PB_4", "move", ["e7", "e5"])
                await asyncio.sleep(1)
                await self.send_move("PB_4", "move", ["e5", "e4"])
        
        # Wait for more messages
        try:
            await asyncio.wait_for(listen_task, timeout=10)
        except asyncio.TimeoutError:
            logger.info("Test completed - closing connection")
        
        if self.websocket:
            await self.websocket.close()
        
        return 0


async def main():
    client = SimpleClient()
    result = await client.run()
    return result


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(result)
    except KeyboardInterrupt:
        logger.info("Client interrupted by user")
    except Exception as e:
        logger.error(f"Client error: {e}")
        exit(1)