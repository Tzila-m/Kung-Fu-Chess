import queue, threading, time, math, logging
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict

from Board import Board
from Command import Command
from Piece import Piece

# set up a module-level logger
logger = logging.getLogger(__name__)

class InvalidBoard(Exception): ...

class ServerGame:
    def __init__(self, pieces: List[Piece], board: Board):
        if not self._validate(pieces):
            raise InvalidBoard("missing kings")
        self.pieces = pieces
        self.board = board
        self.START_NS = time.monotonic_ns()
        self._time_factor = 1

        # lookup tables
        self.pos: Dict[Tuple[int, int], List[Piece]] = defaultdict(list)
        self.piece_by_id: Dict[str, Piece] = {p.id: p for p in pieces}

    def game_time_ms(self) -> int:
        return self._time_factor * (time.monotonic_ns() - self.START_NS) // 1_000_000

    def clone_board(self) -> Board:
        return self.board.clone()

    def _update_cell2piece_map(self):
        self.pos.clear()
        for p in self.pieces:
            self.pos[p.current_cell()].append(p)

    def _process_input(self, cmd: Command):
        """Process a command from a client"""
        mover = self.piece_by_id.get(cmd.piece_id)
        if not mover:
            logger.debug("Unknown piece id %s", cmd.piece_id)
            return

        mover.on_command(cmd, self.pos)

    def _resolve_collisions(self):
        self._update_cell2piece_map()
        occupied = self.pos

        for cell, plist in occupied.items():
            if len(plist) < 2:
                continue

            # Choose the piece that most recently entered the square
            winner = max(plist, key=lambda p: p.state.physics.get_start_ms())

            # Remove captured pieces
            for p in plist:
                if p is winner:
                    continue
                if p.state.can_be_captured():
                    self.pieces.remove(p)

    def _validate(self, pieces):
        """Ensure both kings present and no two pieces share a cell."""
        has_white_king = has_black_king = False
        seen_cells: dict[tuple[int, int], str] = {}
        for p in pieces:
            cell = p.current_cell()
            if cell in seen_cells:
                # Allow overlap only if piece is from opposite side
                if seen_cells[cell] == p.id[1]:
                    return False
            else:
                seen_cells[cell] = p.id[1]
            if p.id.startswith("KW"):
                has_white_king = True
            elif p.id.startswith("KB"):
                has_black_king = True
        return has_white_king and has_black_king

    def _is_win(self) -> bool:
        kings = [p for p in self.pieces if p.id.startswith(('KW', 'KB'))]
        return len(kings) < 2

    def update_pieces(self, now_ms: int):
        """Update all pieces"""
        for p in self.pieces:
            p.update(now_ms)

    def get_piece_by_id(self, piece_id: str) -> Optional[Piece]:
        """Get piece by ID"""
        return self.piece_by_id.get(piece_id)

    def get_all_pieces(self) -> List[Piece]:
        """Get all pieces"""
        return self.pieces.copy()

    def initialize(self):
        """Initialize the game"""
        start_ms = self.START_NS
        for p in self.pieces:
            p.reset(start_ms)