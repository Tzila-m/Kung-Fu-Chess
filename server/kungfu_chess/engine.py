"""
Kung Fu Chess Engine - Server Side
Adapted from the original Game.py for WebSocket/async architecture
"""
import asyncio
import time
import logging
from typing import List, Dict, Tuple, Optional, Set, Any
from collections import defaultdict
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """Serializable game state"""
    pieces: List[Dict[str, Any]]
    board_size: Tuple[int, int] = (8, 8)
    winner: Optional[str] = None
    game_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class InvalidMove(Exception):
    """Raised when an invalid move is attempted"""
    pass


class ChessEngine:
    """
    Main chess engine for Kung Fu Chess
    Handles game logic, validation, and state management
    """
    
    def __init__(self):
        self.pieces: List[Any] = []  # Will be populated with piece objects
        self.board_size = (8, 8)
        self.START_NS = time.monotonic_ns()
        self._time_factor = 1
        
        # Position tracking
        self.pos: Dict[Tuple[int, int], List[Any]] = defaultdict(list)
        self.piece_by_id: Dict[str, Any] = {}
        
        # Game state
        self._winner: Optional[str] = None
        self._game_over = False
        
        # Thread safety
        self._lock = asyncio.Lock()
    
    def game_time_ms(self) -> int:
        """Get current game time in milliseconds"""
        return self._time_factor * (time.monotonic_ns() - self.START_NS) // 1_000_000
    
    async def initialize_game(self, pieces_data: List[Dict[str, Any]]) -> None:
        """Initialize the game with piece data"""
        async with self._lock:
            # For now, we'll store piece data as dicts
            # In a full implementation, we'd recreate Piece objects
            self.pieces = pieces_data
            self.piece_by_id = {p['id']: p for p in pieces_data}
            self._update_position_map()
            logger.info(f"Game initialized with {len(self.pieces)} pieces")
    
    def _update_position_map(self) -> None:
        """Update the position mapping for collision detection"""
        self.pos.clear()
        for piece in self.pieces:
            if 'position' in piece:
                row, col = piece['position']
                self.pos[(row, col)].append(piece)
    
    async def is_legal_move(self, pgn: str, player_color: str) -> bool:
        """
        Check if a move is legal
        For now, basic validation - can be expanded with full chess rules
        """
        async with self._lock:
            try:
                # Parse PGN (simplified - just piece movement for now)
                # Format expected: "Qe2e5" (piece type + from + to)
                if len(pgn) < 5:
                    return False
                
                piece_type = pgn[0]
                from_pos = pgn[1:3]
                to_pos = pgn[3:5]
                
                # Basic validation
                if not self._is_valid_position(from_pos) or not self._is_valid_position(to_pos):
                    return False
                
                # Check if piece exists at from position and belongs to player
                from_row, from_col = self._pos_to_coords(from_pos)
                pieces_at_from = self.pos.get((from_row, from_col), [])
                
                target_piece = None
                for piece in pieces_at_from:
                    if piece['id'].startswith(piece_type) and piece['id'][1] == player_color[0].upper():
                        target_piece = piece
                        break
                
                if not target_piece:
                    logger.debug(f"No {piece_type} piece found at {from_pos} for player {player_color}")
                    return False
                
                # For now, allow all moves (Kung Fu Chess allows simultaneous moves)
                return True
                
            except Exception as e:
                logger.error(f"Error validating move {pgn}: {e}")
                return False
    
    def _is_valid_position(self, pos: str) -> bool:
        """Check if a position string is valid (e.g., 'e2')"""
        if len(pos) != 2:
            return False
        col = pos[0].lower()
        row = pos[1]
        return 'a' <= col <= 'h' and '1' <= row <= '8'
    
    def _pos_to_coords(self, pos: str) -> Tuple[int, int]:
        """Convert chess position (e.g., 'e2') to board coordinates"""
        col = ord(pos[0].lower()) - ord('a')
        row = 8 - int(pos[1])  # Chess rows are 1-8, array is 0-7
        return row, col
    
    def _coords_to_pos(self, row: int, col: int) -> str:
        """Convert board coordinates to chess position"""
        col_char = chr(ord('a') + col)
        row_char = str(8 - row)
        return col_char + row_char
    
    async def execute_move(self, pgn: str, player_color: str) -> GameState:
        """
        Execute a move and return the new game state
        """
        async with self._lock:
            if not await self.is_legal_move(pgn, player_color):
                raise InvalidMove(f"Illegal move: {pgn}")
            
            try:
                # Parse move
                piece_type = pgn[0]
                from_pos = pgn[1:3]
                to_pos = pgn[3:5]
                
                from_row, from_col = self._pos_to_coords(from_pos)
                to_row, to_col = self._pos_to_coords(to_pos)
                
                # Find and move the piece
                pieces_at_from = self.pos.get((from_row, from_col), [])
                target_piece = None
                
                for piece in pieces_at_from:
                    if piece['id'].startswith(piece_type) and piece['id'][1] == player_color[0].upper():
                        target_piece = piece
                        break
                
                if target_piece:
                    # Update piece position
                    target_piece['position'] = (to_row, to_col)
                    
                    # Handle captures (remove opponent pieces at destination)
                    pieces_at_dest = self.pos.get((to_row, to_col), [])
                    for piece in pieces_at_dest[:]:  # Copy list to avoid modification during iteration
                        if piece['id'][1] != player_color[0].upper():  # Different color
                            self.pieces.remove(piece)
                            if piece['id'] in self.piece_by_id:
                                del self.piece_by_id[piece['id']]
                            logger.info(f"Captured piece {piece['id']}")
                    
                    # Update position mapping
                    self._update_position_map()
                    
                    # Check for game over
                    await self._check_game_over()
                    
                    logger.info(f"Executed move: {pgn}")
                
                return await self.get_game_state()
                
            except Exception as e:
                logger.error(f"Error executing move {pgn}: {e}")
                raise InvalidMove(f"Failed to execute move: {pgn}")
    
    async def _check_game_over(self) -> None:
        """Check if the game is over (no kings left for one side)"""
        white_king = False
        black_king = False
        
        for piece in self.pieces:
            if piece['id'].startswith('KW'):
                white_king = True
            elif piece['id'].startswith('KB'):
                black_king = True
        
        if not white_king:
            self._winner = "Black"
            self._game_over = True
        elif not black_king:
            self._winner = "White"
            self._game_over = True
    
    async def get_game_state(self) -> GameState:
        """Get current game state"""
        async with self._lock:
            return GameState(
                pieces=[piece.copy() for piece in self.pieces],
                board_size=self.board_size,
                winner=self._winner,
                game_time_ms=self.game_time_ms()
            )
    
    def is_game_over(self) -> bool:
        """Check if the game is over"""
        return self._game_over
    
    def get_winner(self) -> Optional[str]:
        """Get the winner if game is over"""
        return self._winner


def create_initial_pieces() -> List[Dict[str, Any]]:
    """Create initial chess piece setup"""
    pieces = []
    
    # Black pieces (top)
    back_rank_b = ['RB', 'NB', 'BB', 'KB', 'QB', 'BB', 'NB', 'RB']
    for col, piece_type in enumerate(back_rank_b):
        pieces.append({
            'id': f"{piece_type}_{col}",
            'type': piece_type[0],
            'color': 'B',
            'position': (0, col),
            'cooldown': 0
        })
    
    # Black pawns
    for col in range(8):
        pieces.append({
            'id': f"PB_{col}",
            'type': 'P',
            'color': 'B',
            'position': (1, col),
            'cooldown': 0
        })
    
    # White pawns
    for col in range(8):
        pieces.append({
            'id': f"PW_{col}",
            'type': 'P',
            'color': 'W',
            'position': (6, col),
            'cooldown': 0
        })
    
    # White pieces (bottom)
    back_rank_w = ['RW', 'NW', 'BW', 'KW', 'QW', 'BW', 'NW', 'RW']
    for col, piece_type in enumerate(back_rank_w):
        pieces.append({
            'id': f"{piece_type}_{col}",
            'type': piece_type[0],
            'color': 'W',
            'position': (7, col),
            'cooldown': 0
        })
    
    return pieces