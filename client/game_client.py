"""
Kung Fu Chess GUI Client
Uses the existing graphics system with WebSocket communication
"""
import logging
import time
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any, Optional, List, Tuple
import threading

from websocket_client import GameClient
from ui.Board import Board
from ui.img import Img
from ui.Graphics import Graphics
from ui.GraphicsFactory import ImgFactory

logger = logging.getLogger(__name__)


class ChessGUIClient:
    """GUI client for Kung Fu Chess using existing graphics system"""
    
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.client = GameClient(server_url)
        self.player_color: Optional[str] = None
        self.pieces_data: List[Dict[str, Any]] = []
        self.board_size = (8, 8)
        
        # Graphics setup
        self.cell_size = 64
        self.img_factory = ImgFactory()
        self.board: Optional[Board] = None
        self.piece_graphics: Dict[str, Graphics] = {}
        
        # Tkinter setup
        self.root = tk.Tk()
        self.canvas: Optional[tk.Canvas] = None
        self.setup_gui()
        
        # Game state
        self.selected_piece: Optional[str] = None
        self.running = True
        
        # Setup client callbacks
        self.client.set_callbacks(
            on_game_state=self.on_game_state,
            on_game_over=self.on_game_over,
            on_error=self.on_error,
            on_connected=self.on_connected
        )
    
    def setup_gui(self):
        """Setup the GUI window and canvas"""
        self.root.title("Kung Fu Chess")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create canvas for the game board
        canvas_size = self.cell_size * 8
        self.canvas = tk.Canvas(
            self.root,
            width=canvas_size,
            height=canvas_size,
            bg='white'
        )
        self.canvas.pack(padx=10, pady=10)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # Status label
        self.status_label = tk.Label(self.root, text="Connecting...", font=("Arial", 12))
        self.status_label.pack(pady=5)
        
        # Player info label
        self.player_label = tk.Label(self.root, text="", font=("Arial", 10))
        self.player_label.pack()
        
        # Setup board
        self.setup_board()
    
    def setup_board(self):
        """Setup the game board"""
        board_img = Img()
        # Create a simple board background
        board_img.img = self.create_board_image()
        
        self.board = Board(
            cell_H_pix=self.cell_size,
            cell_W_pix=self.cell_size,
            W_cells=8,
            H_cells=8,
            img=board_img
        )
        
        self.draw_board()
    
    def create_board_image(self):
        """Create a simple chess board image"""
        import numpy as np
        
        # Create checkerboard pattern
        size = self.cell_size * 8
        board = np.zeros((size, size, 3), dtype=np.uint8)
        
        light_color = [240, 217, 181]
        dark_color = [181, 136, 99]
        
        for row in range(8):
            for col in range(8):
                y1 = row * self.cell_size
                y2 = (row + 1) * self.cell_size
                x1 = col * self.cell_size
                x2 = (col + 1) * self.cell_size
                
                # Alternate colors
                if (row + col) % 2 == 0:
                    board[y1:y2, x1:x2] = light_color
                else:
                    board[y1:y2, x1:x2] = dark_color
        
        return board
    
    def draw_board(self):
        """Draw the chess board"""
        if not self.canvas:
            return
            
        self.canvas.delete("all")
        
        # Draw board squares
        for row in range(8):
            for col in range(8):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                # Alternate colors
                if (row + col) % 2 == 0:
                    color = "#F0D9B5"  # Light
                else:
                    color = "#B58863"  # Dark
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
        
        # Draw pieces
        self.draw_pieces()
        
        # Draw coordinates
        self.draw_coordinates()
    
    def draw_coordinates(self):
        """Draw board coordinates"""
        if not self.canvas:
            return
            
        # Files (a-h)
        for i in range(8):
            file_char = chr(ord('a') + i)
            x = i * self.cell_size + self.cell_size // 2
            y = 8 * self.cell_size + 10
            self.canvas.create_text(x, y, text=file_char, font=("Arial", 10))
        
        # Ranks (1-8)
        for i in range(8):
            rank_char = str(8 - i)
            x = -15
            y = i * self.cell_size + self.cell_size // 2
            self.canvas.create_text(x, y, text=rank_char, font=("Arial", 10))
    
    def draw_pieces(self):
        """Draw all pieces on the board"""
        if not self.canvas or not self.pieces_data:
            return
        
        for piece_data in self.pieces_data:
            self.draw_piece(piece_data)
    
    def draw_piece(self, piece_data: Dict[str, Any]):
        """Draw a single piece"""
        if not self.canvas:
            return
            
        piece_id = piece_data.get("id", "")
        position = piece_data.get("position", (0, 0))
        
        if not piece_id or not position:
            return
        
        row, col = position
        x = col * self.cell_size + self.cell_size // 2
        y = row * self.cell_size + self.cell_size // 2
        
        # Simple text representation for now
        # In a full implementation, you would load piece images
        piece_symbol = self.get_piece_symbol(piece_id)
        
        # Color based on piece
        color = "white" if piece_id[1] == 'W' else "black"
        outline = "black" if color == "white" else "white"
        
        # Highlight selected piece
        if piece_id == self.selected_piece:
            outline = "red"
        
        self.canvas.create_text(
            x, y, 
            text=piece_symbol, 
            font=("Arial", 20, "bold"),
            fill=color,
            outline=outline,
            tags=piece_id
        )
    
    def get_piece_symbol(self, piece_id: str) -> str:
        """Get Unicode symbol for piece"""
        piece_type = piece_id[0]
        is_white = piece_id[1] == 'W'
        
        symbols = {
            'K': '♔' if is_white else '♚',  # King
            'Q': '♕' if is_white else '♛',  # Queen
            'R': '♖' if is_white else '♜',  # Rook
            'B': '♗' if is_white else '♝',  # Bishop
            'N': '♘' if is_white else '♞',  # Knight
            'P': '♙' if is_white else '♟',  # Pawn
        }
        
        return symbols.get(piece_type, '?')
    
    def cell_from_coords(self, x: int, y: int) -> Tuple[int, int]:
        """Convert canvas coordinates to board cell"""
        col = x // self.cell_size
        row = y // self.cell_size
        return row, col
    
    def coords_from_cell(self, row: int, col: int) -> Tuple[int, int]:
        """Convert board cell to canvas coordinates"""
        x = col * self.cell_size + self.cell_size // 2
        y = row * self.cell_size + self.cell_size // 2
        return x, y
    
    def get_piece_at_cell(self, row: int, col: int) -> Optional[Dict[str, Any]]:
        """Get piece at specific cell"""
        for piece in self.pieces_data:
            piece_row, piece_col = piece.get("position", (-1, -1))
            if piece_row == row and piece_col == col:
                return piece
        return None
    
    def can_move_piece(self, piece_data: Dict[str, Any]) -> bool:
        """Check if current player can move this piece"""
        if not self.player_color or not piece_data:
            return False
            
        piece_id = piece_data.get("id", "")
        piece_color = piece_id[1] if len(piece_id) > 1 else ""
        
        return (self.player_color == "white" and piece_color == "W") or \
               (self.player_color == "black" and piece_color == "B")
    
    # Mouse event handlers
    def on_click(self, event):
        """Handle mouse click"""
        row, col = self.cell_from_coords(event.x, event.y)
        if not (0 <= row < 8 and 0 <= col < 8):
            return
        
        piece = self.get_piece_at_cell(row, col)
        
        if piece and self.can_move_piece(piece):
            self.selected_piece = piece["id"]
            self.draw_board()  # Redraw to show selection
        else:
            self.selected_piece = None
            self.draw_board()
    
    def on_drag(self, event):
        """Handle mouse drag"""
        # For now, just visual feedback
        pass
    
    def on_release(self, event):
        """Handle mouse release"""
        if not self.selected_piece:
            return
        
        target_row, target_col = self.cell_from_coords(event.x, event.y)
        if not (0 <= target_row < 8 and 0 <= target_col < 8):
            return
        
        # Find selected piece current position
        selected_piece_data = None
        for piece in self.pieces_data:
            if piece["id"] == self.selected_piece:
                selected_piece_data = piece
                break
        
        if not selected_piece_data:
            return
        
        current_row, current_col = selected_piece_data["position"]
        
        # Don't move to same position
        if (target_row, target_col) == (current_row, current_col):
            self.selected_piece = None
            self.draw_board()
            return
        
        # Send move to server
        move_params = [
            f"{chr(ord('a') + current_col)}{8 - current_row}",  # from position
            f"{chr(ord('a') + target_col)}{8 - target_row}"     # to position
        ]
        
        self.client.send_move(self.selected_piece, "move", move_params)
        
        self.selected_piece = None
        self.draw_board()
    
    # Client callbacks
    def on_connected(self, player_color: str):
        """Called when connected to server"""
        self.player_color = player_color
        self.root.after(0, lambda: self.player_label.config(
            text=f"Playing as: {player_color.title()}",
            fg="blue" if player_color == "white" else "red"
        ))
        self.root.after(0, lambda: self.status_label.config(text="Connected - Waiting for game..."))
    
    def on_game_state(self, game_state: Dict[str, Any]):
        """Called when game state is received"""
        self.pieces_data = game_state.get("pieces", [])
        self.board_size = game_state.get("board_size", (8, 8))
        
        # Update GUI in main thread
        self.root.after(0, self.draw_board)
        self.root.after(0, lambda: self.status_label.config(text="Game in progress"))
    
    def on_game_over(self, winner: str):
        """Called when game is over"""
        self.root.after(0, lambda: messagebox.showinfo("Game Over", f"{winner} wins!"))
        self.root.after(0, lambda: self.status_label.config(text=f"Game Over - {winner} wins!"))
    
    def on_error(self, error_msg: str):
        """Called when an error occurs"""
        self.root.after(0, lambda: self.status_label.config(text=f"Error: {error_msg}"))
        logger.error(f"Client error: {error_msg}")
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.client.stop()
        self.root.destroy()
    
    def run(self):
        """Start the client and GUI"""
        logger.info("Starting Kung Fu Chess client")
        
        # Start WebSocket client
        self.client.start()
        
        # Start GUI main loop
        self.root.mainloop()


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    client = ChessGUIClient()
    client.run()


if __name__ == "__main__":
    main()