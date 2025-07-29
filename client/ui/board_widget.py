"""
Chess Board Widget for Kung Fu Chess Client
PySide6-based GUI component with drag and drop support
"""
import sys
import os
import logging
from typing import Dict, Tuple, Optional, Callable, Any, List
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QRect, QPoint
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPixmap, 
    QFont, QMouseEvent, QPaintEvent
)

logger = logging.getLogger(__name__)


class ChessBoardWidget(QWidget):
    """
    Chess board widget with drag and drop functionality
    """
    
    # Signals
    move_requested = Signal(str)  # Emits PGN move string
    
    def __init__(self, player_color: str = "white", parent=None):
        super().__init__(parent)
        self.player_color = player_color.lower()
        self.board_size = 8
        self.cell_size = 80
        self.pieces_data: List[Dict[str, Any]] = []
        
        # Drag and drop state
        self.dragging = False
        self.drag_piece = None
        self.drag_start_pos = None
        self.drag_start_cell = None
        self.drag_offset = QPoint(0, 0)
        
        # Selection state
        self.selected_cell = None
        
        # Piece images
        self.piece_images: Dict[str, QPixmap] = {}
        
        self.setFixedSize(
            self.cell_size * self.board_size + 40,  # +40 for margins
            self.cell_size * self.board_size + 40
        )
        
        self.setMouseTracking(True)
        self.load_piece_images()
        
        # Initialize empty board
        self.init_board()
    
    def load_piece_images(self):
        """Load piece images from assets directory"""
        assets_dir = Path(__file__).parent / "assets"
        
        # Mapping from piece type to directory name
        piece_dirs = {
            'PW': 'PW', 'PB': 'PB',  # Pawns
            'RW': 'RW', 'RB': 'RB',  # Rooks
            'NW': 'NW', 'NB': 'NB',  # Knights
            'BW': 'BW', 'BB': 'BB',  # Bishops
            'QW': 'QW', 'QB': 'QB',  # Queens
            'KW': 'KW', 'KB': 'KB'   # Kings
        }
        
        for piece_code, dir_name in piece_dirs.items():
            piece_dir = assets_dir / dir_name
            if piece_dir.exists():
                # Look for PNG files in the directory
                for img_file in piece_dir.glob("*.png"):
                    pixmap = QPixmap(str(img_file))
                    if not pixmap.isNull():
                        # Scale the image to fit the cell
                        scaled_pixmap = pixmap.scaled(
                            self.cell_size - 10, self.cell_size - 10,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.piece_images[piece_code] = scaled_pixmap
                        logger.debug(f"Loaded image for {piece_code}")
                        break
        
        logger.info(f"Loaded {len(self.piece_images)} piece images")
    
    def init_board(self):
        """Initialize the board with starting pieces"""
        # This will be updated when we receive game state from server
        pass
    
    def update_board_state(self, pieces_data: List[Dict[str, Any]]):
        """Update the board with new piece positions"""
        self.pieces_data = pieces_data
        self.update()
    
    def get_cell_from_pos(self, pos: QPoint) -> Optional[Tuple[int, int]]:
        """Convert pixel position to board cell coordinates"""
        margin = 20
        x = pos.x() - margin
        y = pos.y() - margin
        
        if x < 0 or y < 0:
            return None
        
        col = x // self.cell_size
        row = y // self.cell_size
        
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            return (row, col)
        return None
    
    def get_pos_from_cell(self, row: int, col: int) -> QPoint:
        """Convert board cell to pixel position"""
        margin = 20
        x = col * self.cell_size + margin
        y = row * self.cell_size + margin
        return QPoint(x, y)
    
    def get_piece_at_cell(self, row: int, col: int) -> Optional[Dict[str, Any]]:
        """Get piece at specific cell"""
        for piece in self.pieces_data:
            piece_row, piece_col = piece.get('position', (-1, -1))
            if piece_row == row and piece_col == col:
                return piece
        return None
    
    def coords_to_chess_notation(self, row: int, col: int) -> str:
        """Convert board coordinates to chess notation (e.g., e2)"""
        # Flip row if we're playing as black
        if self.player_color == "black":
            row = 7 - row
            col = 7 - col
        
        file = chr(ord('a') + col)
        rank = str(8 - row)
        return file + rank
    
    def chess_notation_to_coords(self, notation: str) -> Tuple[int, int]:
        """Convert chess notation to board coordinates"""
        col = ord(notation[0]) - ord('a')
        row = 8 - int(notation[1])
        
        # Flip if we're playing as black
        if self.player_color == "black":
            row = 7 - row
            col = 7 - col
        
        return row, col
    
    def can_move_piece(self, piece: Dict[str, Any]) -> bool:
        """Check if the current player can move this piece"""
        piece_color = piece.get('color', '').lower()
        return piece_color == self.player_color[0].lower()
    
    def paintEvent(self, event: QPaintEvent):
        """Paint the chess board and pieces"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw board
        self.draw_board(painter)
        
        # Draw pieces (except the one being dragged)
        self.draw_pieces(painter)
        
        # Draw dragged piece last (on top)
        if self.dragging and self.drag_piece:
            self.draw_dragged_piece(painter)
    
    def draw_board(self, painter: QPainter):
        """Draw the chess board squares"""
        margin = 20
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                x = margin + col * self.cell_size
                y = margin + row * self.cell_size
                
                # Alternate colors
                is_light = (row + col) % 2 == 0
                color = QColor(240, 217, 181) if is_light else QColor(181, 136, 99)
                
                # Highlight selected cell
                if self.selected_cell == (row, col):
                    color = QColor(255, 255, 0, 128)  # Yellow highlight
                
                painter.fillRect(x, y, self.cell_size, self.cell_size, color)
                
                # Draw border
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawRect(x, y, self.cell_size, self.cell_size)
        
        # Draw coordinates
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        font = QFont("Arial", 10)
        painter.setFont(font)
        
        for i in range(self.board_size):
            # Files (a-h)
            file_char = chr(ord('a') + i)
            if self.player_color == "black":
                file_char = chr(ord('h') - i)
            painter.drawText(
                margin + i * self.cell_size + self.cell_size // 2 - 5,
                margin - 5,
                file_char
            )
            
            # Ranks (1-8)
            rank_num = str(8 - i)
            if self.player_color == "black":
                rank_num = str(i + 1)
            painter.drawText(
                5,
                margin + i * self.cell_size + self.cell_size // 2 + 5,
                rank_num
            )
    
    def draw_pieces(self, painter: QPainter):
        """Draw all pieces on the board"""
        margin = 20
        
        for piece in self.pieces_data:
            # Skip the piece being dragged
            if self.dragging and piece == self.drag_piece:
                continue
            
            row, col = piece.get('position', (-1, -1))
            if row < 0 or col < 0:
                continue
            
            # Get piece image
            piece_type = piece.get('type', '')
            piece_color = piece.get('color', '')
            piece_key = f"{piece_type}{piece_color}"
            
            if piece_key in self.piece_images:
                x = margin + col * self.cell_size + 5
                y = margin + row * self.cell_size + 5
                painter.drawPixmap(x, y, self.piece_images[piece_key])
    
    def draw_dragged_piece(self, painter: QPainter):
        """Draw the piece being dragged"""
        if not self.drag_piece:
            return
        
        piece_type = self.drag_piece.get('type', '')
        piece_color = self.drag_piece.get('color', '')
        piece_key = f"{piece_type}{piece_color}"
        
        if piece_key in self.piece_images:
            mouse_pos = self.mapFromGlobal(self.cursor().pos())
            x = mouse_pos.x() - self.cell_size // 2
            y = mouse_pos.y() - self.cell_size // 2
            painter.drawPixmap(x, y, self.piece_images[piece_key])
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events"""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        
        cell = self.get_cell_from_pos(event.pos())
        if not cell:
            return
        
        row, col = cell
        piece = self.get_piece_at_cell(row, col)
        
        if piece and self.can_move_piece(piece):
            # Start dragging
            self.dragging = True
            self.drag_piece = piece
            self.drag_start_pos = event.pos()
            self.drag_start_cell = (row, col)
            self.selected_cell = (row, col)
            self.update()
        else:
            # Clear selection
            self.selected_cell = None
            self.update()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events"""
        if self.dragging:
            self.update()  # Redraw to show piece following cursor
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if not self.dragging or event.button() != Qt.MouseButton.LeftButton:
            return
        
        target_cell = self.get_cell_from_pos(event.pos())
        
        if target_cell and target_cell != self.drag_start_cell:
            # Valid drop - create move
            start_row, start_col = self.drag_start_cell
            end_row, end_col = target_cell
            
            start_notation = self.coords_to_chess_notation(start_row, start_col)
            end_notation = self.coords_to_chess_notation(end_row, end_col)
            
            piece_type = self.drag_piece.get('type', 'P')
            pgn_move = f"{piece_type}{start_notation}{end_notation}"
            
            logger.info(f"Move requested: {pgn_move}")
            self.move_requested.emit(pgn_move)
        
        # End dragging
        self.dragging = False
        self.drag_piece = None
        self.drag_start_pos = None
        self.drag_start_cell = None
        self.selected_cell = None
        self.update()


class GameInfoWidget(QWidget):
    """Widget to display game information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Connecting...")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.status_label)
        
        self.player_label = QLabel("Player: Unknown")
        layout.addWidget(self.player_label)
        
        self.game_time_label = QLabel("Game Time: 00:00")
        layout.addWidget(self.game_time_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def update_status(self, status: str):
        self.status_label.setText(status)
    
    def update_player_info(self, color: str):
        self.player_label.setText(f"Player: {color.title()}")
    
    def update_game_time(self, time_ms: int):
        seconds = time_ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        self.game_time_label.setText(f"Game Time: {minutes:02d}:{seconds:02d}")


class ChessGameWidget(QWidget):
    """Main game widget combining board and info"""
    
    # Signals
    move_requested = Signal(str)
    
    def __init__(self, player_color: str = "white", parent=None):
        super().__init__(parent)
        self.player_color = player_color
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        
        # Chess board
        self.board = ChessBoardWidget(self.player_color)
        self.board.move_requested.connect(self.move_requested.emit)
        layout.addWidget(self.board)
        
        # Game info
        self.info = GameInfoWidget()
        layout.addWidget(self.info)
        
        self.setLayout(layout)
        
        # Set window properties
        self.setWindowTitle(f"Kung Fu Chess - {self.player_color.title()} Player")
        self.setMinimumSize(800, 600)
    
    def update_board_state(self, pieces_data: List[Dict[str, Any]]):
        """Update the board with new game state"""
        self.board.update_board_state(pieces_data)
    
    def update_status(self, status: str):
        """Update the game status"""
        self.info.update_status(status)
    
    def update_player_info(self, color: str):
        """Update player information"""
        self.info.update_player_info(color)
    
    def update_game_time(self, time_ms: int):
        """Update game time display"""
        self.info.update_game_time(time_ms)