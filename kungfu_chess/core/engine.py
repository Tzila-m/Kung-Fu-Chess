"""
Enhanced Chess Engine with Event Bus Integration
================================================

Extended version of the original Game class with EventBus integration
for pub/sub event handling and external API compatibility.
"""

import logging
import time
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

from .game import Game
from .board import Board
from .piece import Piece
from ..bus.event_bus import EventBus, EventTopics

logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """Represents the current state of the game for serialization."""
    fen: str
    cooldowns: Dict[str, float]
    scores: Dict[str, int]
    game_time_ms: int
    is_game_over: bool
    winner: Optional[str] = None


@dataclass
class MoveResult:
    """Result of a move attempt."""
    success: bool
    piece_id: str
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    captured_piece: Optional[str] = None
    error_message: Optional[str] = None


class ChessEngine:
    """
    Enhanced chess engine with EventBus integration.
    
    Extends the original Game class functionality with:
    - Event-driven architecture via EventBus
    - WebSocket-compatible API
    - Move validation and state management
    - Score tracking and game lifecycle events
    """
    
    def __init__(self, pieces: List[Piece], board: Board, event_bus: Optional[EventBus] = None):
        """
        Initialize the chess engine.
        
        Args:
            pieces: List of chess pieces
            board: Game board
            event_bus: Event bus for pub/sub messaging (created if None)
        """
        self.game = Game(pieces, board)
        self.event_bus = event_bus or EventBus()
        self.scores = {"white": 0, "black": 0}
        self.move_history: List[Dict[str, Any]] = []
        self.is_game_over = False
        self.winner: Optional[str] = None
        
        # Subscribe to internal events
        self._setup_event_subscriptions()
        
        logger.info("ChessEngine initialized with EventBus integration")
    
    def _setup_event_subscriptions(self) -> None:
        """Set up internal event subscriptions."""
        self.event_bus.subscribe(EventTopics.PIECE_CAPTURED, self._on_piece_captured)
        self.event_bus.subscribe(EventTopics.GAME_ENDED, self._on_game_ended)
    
    def start_game(self) -> None:
        """Start the game and publish game_started event."""
        self.is_game_over = False
        self.winner = None
        self.scores = {"white": 0, "black": 0}
        self.move_history.clear()
        
        # Publish game started event
        self.event_bus.publish(EventTopics.GAME_STARTED, {
            "timestamp": time.time(),
            "players": ["white", "black"]
        })
        
        logger.info("Game started")
    
    def make_move(self, move_str: str) -> MoveResult:
        """
        Make a move from PGN-style string.
        
        Args:
            move_str: Move string in format like "WQe2e5" (piece_id + from + to)
            
        Returns:
            MoveResult with success status and details
        """
        try:
            # Parse move string (simplified PGN-like format)
            if len(move_str) < 6:
                return MoveResult(
                    success=False,
                    piece_id="",
                    from_pos=(0, 0),
                    to_pos=(0, 0),
                    error_message="Invalid move format"
                )
            
            piece_id = move_str[:2]  # e.g., "WQ"
            from_square = move_str[2:4]  # e.g., "e2"
            to_square = move_str[4:6]    # e.g., "e5"
            
            from_pos = self._square_to_pos(from_square)
            to_pos = self._square_to_pos(to_square)
            
            # Validate piece exists
            piece = self.game.piece_by_id.get(piece_id)
            if not piece:
                return MoveResult(
                    success=False,
                    piece_id=piece_id,
                    from_pos=from_pos,
                    to_pos=to_pos,
                    error_message=f"Piece {piece_id} not found"
                )
            
            # Check if piece can move (cooldown, etc.)
            if not self._can_piece_move(piece):
                return MoveResult(
                    success=False,
                    piece_id=piece_id,
                    from_pos=from_pos,
                    to_pos=to_pos,
                    error_message=f"Piece {piece_id} cannot move (cooldown or other constraint)"
                )
            
            # Attempt the move
            success = self._execute_move(piece, from_pos, to_pos)
            
            if success:
                # Log the move
                move_data = {
                    "piece_id": piece_id,
                    "from": from_square,
                    "to": to_square,
                    "timestamp": time.time(),
                    "game_time_ms": self.game.game_time_ms()
                }
                self.move_history.append(move_data)
                
                # Publish events
                self.event_bus.publish(EventTopics.MOVE_LOGGED, move_data)
                self.event_bus.publish(EventTopics.PIECE_MOVED, {
                    "piece_id": piece_id,
                    "from_pos": from_pos,
                    "to_pos": to_pos
                })
                
                return MoveResult(
                    success=True,
                    piece_id=piece_id,
                    from_pos=from_pos,
                    to_pos=to_pos
                )
            else:
                return MoveResult(
                    success=False,
                    piece_id=piece_id,
                    from_pos=from_pos,
                    to_pos=to_pos,
                    error_message="Move validation failed"
                )
                
        except Exception as e:
            logger.error(f"Error making move {move_str}: {e}")
            return MoveResult(
                success=False,
                piece_id="",
                from_pos=(0, 0),
                to_pos=(0, 0),
                error_message=str(e)
            )
    
    def get_game_state(self) -> GameState:
        """
        Get current game state for serialization.
        
        Returns:
            GameState object with current game information
        """
        # Generate simplified FEN-like representation
        fen = self._generate_fen()
        
        # Get piece cooldowns
        cooldowns = self._get_piece_cooldowns()
        
        return GameState(
            fen=fen,
            cooldowns=cooldowns,
            scores=self.scores.copy(),
            game_time_ms=self.game.game_time_ms(),
            is_game_over=self.is_game_over,
            winner=self.winner
        )
    
    def update(self) -> None:
        """Update game state (should be called regularly)."""
        if self.is_game_over:
            return
            
        # Update all pieces
        now = self.game.game_time_ms()
        for piece in self.game.pieces:
            piece.update(now)
        
        # Update position mappings
        self.game._update_cell2piece_map()
        
        # Resolve collisions
        self.game._resolve_collisions()
        
        # Check for game end
        if self.game._is_win():
            self._end_game()
    
    def _square_to_pos(self, square: str) -> Tuple[int, int]:
        """Convert chess square notation (e.g., 'e4') to (row, col)."""
        if len(square) != 2:
            raise ValueError(f"Invalid square format: {square}")
        
        col = ord(square[0].lower()) - ord('a')
        row = int(square[1]) - 1
        
        # Convert to board coordinates (might need adjustment based on board orientation)
        return (7 - row, col)  # Flip row for standard chess board
    
    def _pos_to_square(self, pos: Tuple[int, int]) -> str:
        """Convert (row, col) to chess square notation."""
        row, col = pos
        file = chr(ord('a') + col)
        rank = str(8 - row)  # Flip row for standard chess board
        return f"{file}{rank}"
    
    def _can_piece_move(self, piece: Piece) -> bool:
        """Check if a piece can currently move."""
        # This would check cooldowns, piece state, etc.
        # For now, simplified check
        return piece.state.can_capture()  # Reusing existing state check
    
    def _execute_move(self, piece: Piece, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        """Execute a piece move."""
        # This is a simplified implementation
        # In the real implementation, this would interact with the piece's movement system
        current_pos = piece.current_cell()
        
        if current_pos != from_pos:
            return False
        
        # For now, just update the piece position directly
        # In the full implementation, this would use the physics system
        try:
            # Set piece to target position (simplified)
            piece.state.physics.pos_m = self.game.board.cell_to_m(to_pos)
            return True
        except Exception as e:
            logger.error(f"Failed to execute move: {e}")
            return False
    
    def _generate_fen(self) -> str:
        """Generate a simplified FEN-like string representing board state."""
        # This is a simplified FEN generation
        # In a full implementation, this would create proper FEN notation
        pieces_data = []
        for piece in self.game.pieces:
            pos = piece.current_cell()
            pieces_data.append(f"{piece.id}:{self._pos_to_square(pos)}")
        
        return "|".join(pieces_data)
    
    def _get_piece_cooldowns(self) -> Dict[str, float]:
        """Get current cooldown times for all pieces."""
        cooldowns = {}
        current_time = self.game.game_time_ms()
        
        for piece in self.game.pieces:
            # This would calculate actual cooldown based on piece state
            # For now, return 0 (no cooldown)
            cooldowns[piece.id] = 0.0
        
        return cooldowns
    
    def _on_piece_captured(self, event_data: Any) -> None:
        """Handle piece captured event."""
        captured_piece = event_data.get("piece_id", "")
        capturing_piece = event_data.get("capturing_piece", "")
        
        # Update scores
        if captured_piece.endswith("W"):  # White piece captured
            self.scores["black"] += 1
        elif captured_piece.endswith("B"):  # Black piece captured
            self.scores["white"] += 1
        
        # Publish score update
        self.event_bus.publish(EventTopics.SCORE_UPDATED, self.scores.copy())
        
        logger.info(f"Piece {captured_piece} captured by {capturing_piece}")
    
    def _on_game_ended(self, event_data: Any) -> None:
        """Handle game ended event."""
        self.winner = event_data.get("winner")
        self.is_game_over = True
        logger.info(f"Game ended. Winner: {self.winner}")
    
    def _end_game(self) -> None:
        """End the current game."""
        # Determine winner based on remaining pieces
        kings = [p for p in self.game.pieces if p.id.startswith(('KW', 'KB'))]
        
        if len(kings) == 1:
            winner_color = "white" if kings[0].id.startswith('KW') else "black"
        else:
            winner_color = None
        
        self.winner = winner_color
        self.is_game_over = True
        
        # Publish game ended event
        self.event_bus.publish(EventTopics.GAME_ENDED, {
            "winner": winner_color,
            "timestamp": time.time(),
            "final_scores": self.scores.copy(),
            "total_moves": len(self.move_history)
        })
        
        logger.info(f"Game ended. Winner: {winner_color}")
    
    def get_event_bus(self) -> EventBus:
        """Get the event bus instance."""
        return self.event_bus