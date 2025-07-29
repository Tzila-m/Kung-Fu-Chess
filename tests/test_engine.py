"""
Tests for the Kung Fu Chess Engine
"""
import pytest
import pytest_asyncio
import asyncio
from server.kungfu_chess.engine import ChessEngine, create_initial_pieces, InvalidMove


class TestChessEngine:
    """Test cases for the chess engine"""
    
    @pytest_asyncio.fixture
    async def engine(self):
        """Create a chess engine for testing"""
        engine = ChessEngine()
        initial_pieces = create_initial_pieces()
        await engine.initialize_game(initial_pieces)
        return engine
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test that the engine initializes correctly"""
        assert len(engine.pieces) == 32  # Standard chess pieces
        assert not engine.is_game_over()
        assert engine.get_winner() is None
    
    @pytest.mark.asyncio
    async def test_valid_pawn_move(self, engine):
        """Test a valid pawn move"""
        # Move white pawn from e2 to e4
        is_legal = await engine.is_legal_move("Pe2e4", "white")
        assert is_legal
        
        # Execute the move
        game_state = await engine.execute_move("Pe2e4", "white")
        assert game_state is not None
        assert len(game_state.pieces) == 32  # No captures
    
    @pytest.mark.asyncio
    async def test_invalid_move_empty_square(self, engine):
        """Test moving from an empty square"""
        is_legal = await engine.is_legal_move("Pe4e5", "white")
        assert not is_legal
    
    @pytest.mark.asyncio
    async def test_invalid_move_opponent_piece(self, engine):
        """Test trying to move opponent's piece"""
        is_legal = await engine.is_legal_move("Pe7e5", "white")
        assert not is_legal
    
    @pytest.mark.asyncio
    async def test_capture_move(self, engine):
        """Test capturing an opponent's piece"""
        # Move white pawn to position for capture
        await engine.execute_move("Pe2e4", "white")
        # Move black pawn to capturable position
        await engine.execute_move("Pd7d5", "black")
        
        # Capture
        initial_piece_count = len(engine.pieces)
        game_state = await engine.execute_move("Pe4d5", "white")
        
        # Should have one less piece after capture
        assert len(game_state.pieces) < initial_piece_count
    
    @pytest.mark.asyncio
    async def test_invalid_pgn_format(self, engine):
        """Test invalid PGN format"""
        is_legal = await engine.is_legal_move("invalid", "white")
        assert not is_legal
    
    @pytest.mark.asyncio
    async def test_position_conversion(self, engine):
        """Test position conversion methods"""
        # Test valid positions
        assert engine._is_valid_position("e2")
        assert engine._is_valid_position("a1")
        assert engine._is_valid_position("h8")
        
        # Test invalid positions
        assert not engine._is_valid_position("i9")
        assert not engine._is_valid_position("z0")
        assert not engine._is_valid_position("e")
        
        # Test coordinate conversion
        coords = engine._pos_to_coords("e2")
        assert coords == (6, 4)  # e2 in array coordinates
        
        pos = engine._coords_to_pos(6, 4)
        assert pos == "e2"


def test_initial_pieces_creation():
    """Test creation of initial piece setup"""
    pieces = create_initial_pieces()
    assert len(pieces) == 32
    
    # Count pieces by type
    piece_counts = {}
    for piece in pieces:
        piece_type = piece['type']
        piece_counts[piece_type] = piece_counts.get(piece_type, 0) + 1
    
    # Check standard chess piece counts
    assert piece_counts['P'] == 16  # 8 pawns per side
    assert piece_counts['R'] == 4   # 2 rooks per side
    assert piece_counts['N'] == 4   # 2 knights per side
    assert piece_counts['B'] == 4   # 2 bishops per side
    assert piece_counts['Q'] == 2   # 1 queen per side
    assert piece_counts['K'] == 2   # 1 king per side