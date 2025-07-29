import asyncio
import websockets
import json
import threading
import time
import logging
import pathlib
import pygame
import sys
import os
from typing import Dict, List, Optional, Tuple

# Add the KFC_Py directory to Python path  
current_dir = os.path.dirname(os.path.abspath(__file__))
kfc_py_path = os.path.join(current_dir, 'KFC_Py')
sys.path.insert(0, kfc_py_path)

from Board import Board
from img import Img
from Command import Command

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChessClient:
    def __init__(self, server_host="localhost", server_port=8765):
        self.server_host = server_host
        self.server_port = server_port
        self.websocket = None
        self.board_state = {}
        self.running = False
        
        # Pygame display settings
        self.CELL_SIZE = 64
        self.BOARD_SIZE = 8
        self.WINDOW_SIZE = (self.CELL_SIZE * self.BOARD_SIZE, self.CELL_SIZE * self.BOARD_SIZE + 100)
        
        # Chess pieces graphics
        self.piece_images = {}
        self.board_image = None
        
        # Mouse interaction
        self.selected_piece = None
        self.selected_cell = None
        self.last_click_time = 0
        
        # Board display
        self.pieces_path = pathlib.Path("pieces")
        
    def load_piece_images(self):
        """Load all chess piece sprite images"""
        piece_types = ['K', 'Q', 'R', 'B', 'N', 'P']  # King, Queen, Rook, Bishop, Knight, Pawn
        colors = ['W', 'B']  # White, Black
        
        for piece_type in piece_types:
            for color in colors:
                piece_id = f"{piece_type}{color}"
                try:
                    # Load the idle sprite for each piece
                    sprite_path = self.pieces_path / piece_id / "states" / "idle" / "sprites"
                    if sprite_path.exists():
                        png_files = list(sprite_path.glob("*.png"))
                        if png_files:
                            # Use pygame to load the image
                            image = pygame.image.load(str(png_files[0]))
                            image = pygame.transform.scale(image, (self.CELL_SIZE, self.CELL_SIZE))
                            self.piece_images[piece_id] = image
                            logger.info(f"Loaded image for {piece_id}")
                except Exception as e:
                    logger.warning(f"Could not load image for {piece_id}: {e}")
                    
    def load_board_image(self):
        """Load the chess board background"""
        try:
            board_path = self.pieces_path / "board.png"
            if board_path.exists():
                self.board_image = pygame.image.load(str(board_path))
                self.board_image = pygame.transform.scale(self.board_image, 
                                                        (self.CELL_SIZE * 8, self.CELL_SIZE * 8))
                logger.info("Loaded board image")
            else:
                # Create a simple checkered board
                self.create_simple_board()
        except Exception as e:
            logger.warning(f"Could not load board image: {e}")
            self.create_simple_board()
            
    def create_simple_board(self):
        """Create a simple checkered chess board"""
        self.board_image = pygame.Surface((self.CELL_SIZE * 8, self.CELL_SIZE * 8))
        
        for row in range(8):
            for col in range(8):
                color = (240, 217, 181) if (row + col) % 2 == 0 else (181, 136, 99)
                rect = pygame.Rect(col * self.CELL_SIZE, row * self.CELL_SIZE, 
                                 self.CELL_SIZE, self.CELL_SIZE)
                pygame.draw.rect(self.board_image, color, rect)
                
    def init_pygame(self):
        """Initialize pygame display"""
        pygame.init()
        self.screen = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.display.set_caption("Chess Client")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        # Load graphics
        self.load_board_image()
        self.load_piece_images()
        
    def pixel_to_cell(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert pixel coordinates to board cell"""
        x, y = pos
        if y >= self.CELL_SIZE * 8:  # Click below board
            return None
        col = x // self.CELL_SIZE
        row = y // self.CELL_SIZE
        if 0 <= row < 8 and 0 <= col < 8:
            return (row, col)
        return None
        
    def cell_to_pixel(self, cell: Tuple[int, int]) -> Tuple[int, int]:
        """Convert board cell to pixel coordinates"""
        row, col = cell
        return (col * self.CELL_SIZE, row * self.CELL_SIZE)
        
    def handle_mouse_click(self, pos: Tuple[int, int]):
        """Handle mouse click on the board"""
        cell = self.pixel_to_cell(pos)
        if not cell:
            return
            
        current_time = time.time()
        
        # Find piece at clicked cell
        clicked_piece = None
        for piece_data in self.board_state.get("pieces", []):
            if tuple(piece_data["position"]) == cell:
                clicked_piece = piece_data
                break
                
        if self.selected_piece is None:
            # First click - select piece
            if clicked_piece:
                self.selected_piece = clicked_piece
                self.selected_cell = cell
                logger.info(f"Selected piece {clicked_piece['id']} at {cell}")
        else:
            # Second click - move piece or deselect
            if clicked_piece and clicked_piece["id"] == self.selected_piece["id"]:
                # Clicking same piece - deselect
                self.selected_piece = None
                self.selected_cell = None
                logger.info("Deselected piece")
            else:
                # Move piece to new cell
                asyncio.create_task(self.send_move(self.selected_piece["id"], cell))
                self.selected_piece = None
                self.selected_cell = None
                
    def draw_board(self):
        """Draw the chess board and pieces"""
        # Clear screen
        self.screen.fill((50, 50, 50))
        
        # Draw board
        if self.board_image:
            self.screen.blit(self.board_image, (0, 0))
            
        # Draw pieces
        for piece_data in self.board_state.get("pieces", []):
            piece_id = piece_data["id"]
            position = tuple(piece_data["position"])
            piece_type_color = piece_id[:2]  # e.g., "KW", "PB"
            
            if piece_type_color in self.piece_images:
                pixel_pos = self.cell_to_pixel(position)
                self.screen.blit(self.piece_images[piece_type_color], pixel_pos)
                
        # Highlight selected cell
        if self.selected_cell:
            row, col = self.selected_cell
            highlight_rect = pygame.Rect(col * self.CELL_SIZE, row * self.CELL_SIZE,
                                       self.CELL_SIZE, self.CELL_SIZE)
            pygame.draw.rect(self.screen, (255, 255, 0), highlight_rect, 3)
            
        # Draw status information
        status_y = self.CELL_SIZE * 8 + 10
        pieces_count = len(self.board_state.get("pieces", []))
        status_text = f"Pieces: {pieces_count} | Connected to server"
        if self.selected_piece:
            status_text += f" | Selected: {self.selected_piece['id']}"
            
        text_surface = self.font.render(status_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, status_y))
        
        # Connection status
        conn_text = "Connected" if self.websocket else "Disconnected"
        conn_color = (0, 255, 0) if self.websocket else (255, 0, 0)
        conn_surface = self.font.render(conn_text, True, conn_color)
        self.screen.blit(conn_surface, (10, status_y + 30))
        
        pygame.display.flip()
        
    async def send_move(self, piece_id: str, target_cell: Tuple[int, int]):
        """Send move command to server"""
        if not self.websocket:
            logger.warning("Not connected to server")
            return
            
        try:
            message = {
                "type": "move",
                "data": {
                    "piece_id": piece_id,
                    "type": "move",
                    "params": [target_cell]
                }
            }
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent move: {piece_id} to {target_cell}")
        except Exception as e:
            logger.error(f"Error sending move: {e}")
            
    async def request_board_state(self):
        """Request current board state from server"""
        if not self.websocket:
            return
            
        try:
            message = {"type": "request_state"}
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error requesting board state: {e}")
            
    async def handle_server_message(self, message):
        """Handle message from server"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "board_state":
                self.board_state = data.get("data", {})
                logger.debug("Board state updated")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from server")
        except Exception as e:
            logger.error(f"Error handling server message: {e}")
            
    async def connect_to_server(self):
        """Connect to the chess server"""
        uri = f"ws://{self.server_host}:{self.server_port}"
        try:
            logger.info(f"Connecting to server at {uri}")
            self.websocket = await websockets.connect(uri)
            logger.info("Connected to server")
            
            # Request initial board state
            await self.request_board_state()
            
            # Listen for messages
            async for message in self.websocket:
                await self.handle_server_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection to server closed")
        except Exception as e:
            logger.error(f"Error connecting to server: {e}")
        finally:
            self.websocket = None
            
    def run_pygame_loop(self):
        """Run the pygame event loop"""
        self.init_pygame()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.handle_mouse_click(event.pos)
                        
            self.draw_board()
            self.clock.tick(60)  # 60 FPS
            
        pygame.quit()
        
    async def run(self):
        """Run the chess client"""
        self.running = True
        
        # Start pygame in a separate thread
        pygame_thread = threading.Thread(target=self.run_pygame_loop, daemon=True)
        pygame_thread.start()
        
        # Connect to server and handle messages
        while self.running:
            try:
                await self.connect_to_server()
                # If we get here, connection was lost
                logger.info("Attempting to reconnect...")
                await asyncio.sleep(2)
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                logger.error(f"Client error: {e}")
                await asyncio.sleep(2)
                
        logger.info("Client shutting down")

async def main():
    client = ChessClient()
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())