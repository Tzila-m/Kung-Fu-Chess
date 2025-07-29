"""
Tests for WebSocket API module
==============================

Comprehensive tests for the FastAPI WebSocket server functionality.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import asdict

from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from kungfu_chess.api.server import (
    create_app, ConnectionManager, ChessWebSocketManager,
    get_chess_manager
)
from kungfu_chess.bus.event_bus import EventBus, EventTopics
from kungfu_chess.core.engine import ChessEngine, GameState, MoveResult


class TestConnectionManager:
    """Test cases for ConnectionManager class."""
    
    def test_init(self):
        """Test ConnectionManager initialization."""
        manager = ConnectionManager()
        assert manager.active_connections == []
        assert manager.player_connections == {}
    
    @pytest.mark.asyncio
    async def test_connect_without_player_id(self):
        """Test connecting a WebSocket without player ID."""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)
        
        await manager.connect(websocket)
        
        websocket.accept.assert_called_once()
        assert websocket in manager.active_connections
        assert len(manager.player_connections) == 0
    
    @pytest.mark.asyncio
    async def test_connect_with_player_id(self):
        """Test connecting a WebSocket with player ID."""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)
        player_id = "player1"
        
        await manager.connect(websocket, player_id)
        
        websocket.accept.assert_called_once()
        assert websocket in manager.active_connections
        assert manager.player_connections[player_id] == websocket
    
    def test_disconnect_without_player_id(self):
        """Test disconnecting a WebSocket without player ID."""
        manager = ConnectionManager()
        websocket = Mock(spec=WebSocket)
        manager.active_connections = [websocket]
        
        manager.disconnect(websocket)
        
        assert websocket not in manager.active_connections
    
    def test_disconnect_with_player_id(self):
        """Test disconnecting a WebSocket with player ID."""
        manager = ConnectionManager()
        websocket = Mock(spec=WebSocket)
        player_id = "player1"
        
        manager.active_connections = [websocket]
        manager.player_connections = {player_id: websocket}
        
        manager.disconnect(websocket, player_id)
        
        assert websocket not in manager.active_connections
        assert player_id not in manager.player_connections
    
    def test_disconnect_nonexistent_connection(self):
        """Test disconnecting a nonexistent connection."""
        manager = ConnectionManager()
        websocket = Mock(spec=WebSocket)
        
        # Should not raise any errors
        manager.disconnect(websocket)
        manager.disconnect(websocket, "nonexistent_player")
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending a personal message."""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)
        message = "test message"
        
        await manager.send_personal_message(message, websocket)
        
        websocket.send_text.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_personal_message_error(self):
        """Test sending a personal message with error."""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)
        websocket.send_text.side_effect = Exception("Send error")
        
        # Should not raise exception
        await manager.send_personal_message("test", websocket)
    
    @pytest.mark.asyncio
    async def test_send_to_player(self):
        """Test sending a message to a specific player."""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)
        player_id = "player1"
        message = "test message"
        
        manager.player_connections[player_id] = websocket
        
        await manager.send_to_player(message, player_id)
        
        websocket.send_text.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_to_nonexistent_player(self):
        """Test sending a message to nonexistent player."""
        manager = ConnectionManager()
        
        # Should not raise any errors
        await manager.send_to_player("test", "nonexistent_player")
    
    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting a message to all connections."""
        manager = ConnectionManager()
        websockets = [AsyncMock(spec=WebSocket) for _ in range(3)]
        manager.active_connections = websockets.copy()
        message = "broadcast message"
        
        await manager.broadcast(message)
        
        for websocket in websockets:
            websocket.send_text.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_with_error(self):
        """Test broadcasting with some connections failing."""
        manager = ConnectionManager()
        good_websocket = AsyncMock(spec=WebSocket)
        bad_websocket = AsyncMock(spec=WebSocket)
        bad_websocket.send_text.side_effect = Exception("Send error")
        
        manager.active_connections = [good_websocket, bad_websocket]
        
        await manager.broadcast("test message")
        
        # Good connection should receive message
        good_websocket.send_text.assert_called_once_with("test message")
        bad_websocket.send_text.assert_called_once_with("test message")
        
        # Bad connection should be removed
        assert bad_websocket not in manager.active_connections
        assert good_websocket in manager.active_connections


class TestChessWebSocketManager:
    """Test cases for ChessWebSocketManager class."""
    
    def test_init(self):
        """Test ChessWebSocketManager initialization."""
        manager = ChessWebSocketManager()
        
        assert isinstance(manager.connection_manager, ConnectionManager)
        assert manager.chess_engine is None
        assert isinstance(manager.event_bus, EventBus)
        assert manager.game_loop_task is None
        assert manager.is_running is False
    
    def test_initialize_game(self):
        """Test game initialization."""
        manager = ChessWebSocketManager()
        pieces = []
        board = Mock()
        
        manager.initialize_game(pieces, board)
        
        assert manager.chess_engine is not None
        assert isinstance(manager.chess_engine, ChessEngine)
    
    def test_start_game_loop(self):
        """Test starting the game loop."""
        manager = ChessWebSocketManager()
        manager.chess_engine = Mock(spec=ChessEngine)
        
        with patch('asyncio.create_task') as mock_create_task:
            manager.start_game_loop()
            
            assert manager.is_running is True
            mock_create_task.assert_called_once()
    
    def test_start_game_loop_without_engine(self):
        """Test starting game loop without engine."""
        manager = ChessWebSocketManager()
        
        manager.start_game_loop()
        
        assert manager.is_running is False
        assert manager.game_loop_task is None
    
    def test_stop_game_loop(self):
        """Test stopping the game loop."""
        manager = ChessWebSocketManager()
        manager.is_running = True
        manager.game_loop_task = Mock()
        
        manager.stop_game_loop()
        
        assert manager.is_running is False
        manager.game_loop_task.cancel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_json_message_start_game(self):
        """Test handling JSON start_game message."""
        manager = ChessWebSocketManager()
        manager.chess_engine = Mock(spec=ChessEngine)
        websocket = AsyncMock(spec=WebSocket)
        
        with patch.object(manager, 'start_game_loop') as mock_start:
            await manager._handle_json_message(
                websocket,
                {"action": "start_game"},
                "player1"
            )
            
            manager.chess_engine.start_game.assert_called_once()
            mock_start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_json_message_get_state(self):
        """Test handling JSON get_state message."""
        manager = ChessWebSocketManager()
        websocket = AsyncMock(spec=WebSocket)
        
        with patch.object(manager, '_send_game_state') as mock_send:
            await manager._handle_json_message(
                websocket,
                {"action": "get_state"},
                "player1"
            )
            
            mock_send.assert_called_once_with(websocket)
    
    @pytest.mark.asyncio
    async def test_handle_json_message_make_move(self):
        """Test handling JSON make_move message."""
        manager = ChessWebSocketManager()
        websocket = AsyncMock(spec=WebSocket)
        
        with patch.object(manager, '_handle_move_command') as mock_handle:
            await manager._handle_json_message(
                websocket,
                {"action": "make_move", "move": "WQe2e5"},
                "player1"
            )
            
            mock_handle.assert_called_once_with(websocket, "WQe2e5", "player1")
    
    @pytest.mark.asyncio
    async def test_handle_json_message_unknown_action(self):
        """Test handling JSON message with unknown action."""
        manager = ChessWebSocketManager()
        websocket = AsyncMock(spec=WebSocket)
        
        await manager._handle_json_message(
            websocket,
            {"action": "unknown_action"},
            "player1"
        )
        
        # Should send error message
        websocket.send_text.assert_called_once()
        sent_data = json.loads(websocket.send_text.call_args[0][0])
        assert "error" in sent_data
        assert "Unknown action" in sent_data["error"]
    
    @pytest.mark.asyncio
    async def test_handle_move_command_success(self):
        """Test handling successful move command."""
        manager = ChessWebSocketManager()
        manager.chess_engine = Mock(spec=ChessEngine)
        websocket = AsyncMock(spec=WebSocket)
        
        # Mock successful move
        move_result = MoveResult(
            success=True,
            piece_id="WQ",
            from_pos=(1, 4),
            to_pos=(4, 4)
        )
        manager.chess_engine.make_move.return_value = move_result
        
        with patch.object(manager, '_broadcast_game_state') as mock_broadcast:
            await manager._handle_move_command(websocket, "WQe2e5", "player1")
            
            manager.chess_engine.make_move.assert_called_once_with("WQe2e5")
            websocket.send_text.assert_called_once()
            mock_broadcast.assert_called_once()
            
            # Check response format
            sent_data = json.loads(websocket.send_text.call_args[0][0])
            assert sent_data["type"] == "move_result"
            assert sent_data["success"] is True
            assert sent_data["move"] == "WQe2e5"
            assert sent_data["player_id"] == "player1"
    
    @pytest.mark.asyncio
    async def test_handle_move_command_failure(self):
        """Test handling failed move command."""
        manager = ChessWebSocketManager()
        manager.chess_engine = Mock(spec=ChessEngine)
        websocket = AsyncMock(spec=WebSocket)
        
        # Mock failed move
        move_result = MoveResult(
            success=False,
            piece_id="WQ",
            from_pos=(1, 4),
            to_pos=(4, 4),
            error_message="Invalid move"
        )
        manager.chess_engine.make_move.return_value = move_result
        
        with patch.object(manager, '_broadcast_game_state') as mock_broadcast:
            await manager._handle_move_command(websocket, "WQe2e5", "player1")
            
            manager.chess_engine.make_move.assert_called_once_with("WQe2e5")
            websocket.send_text.assert_called_once()
            mock_broadcast.assert_not_called()
            
            # Check response format
            sent_data = json.loads(websocket.send_text.call_args[0][0])
            assert sent_data["type"] == "move_result"
            assert sent_data["success"] is False
            assert sent_data["error"] == "Invalid move"
    
    @pytest.mark.asyncio
    async def test_handle_move_command_no_engine(self):
        """Test handling move command without chess engine."""
        manager = ChessWebSocketManager()
        websocket = AsyncMock(spec=WebSocket)
        
        await manager._handle_move_command(websocket, "WQe2e5", "player1")
        
        websocket.send_text.assert_called_once()
        sent_data = json.loads(websocket.send_text.call_args[0][0])
        assert "error" in sent_data
        assert "not initialized" in sent_data["error"]


class TestFastAPIApp:
    """Test cases for the FastAPI application."""
    
    def test_create_app(self):
        """Test creating the FastAPI app."""
        app = create_app()
        
        assert app.title == "Kung Fu Chess WebSocket API"
        assert app.version == "2.0.0"
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Kung Fu Chess WebSocket API"
        assert data["version"] == "2.0.0"
        assert "websocket_endpoint" in data
        assert "player_endpoint" in data
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_connections" in data
        assert "game_running" in data
    
    def test_get_chess_manager(self):
        """Test getting the global chess manager."""
        manager = get_chess_manager()
        
        assert isinstance(manager, ChessWebSocketManager)
        
        # Should return the same instance
        manager2 = get_chess_manager()
        assert manager is manager2


# Integration test for WebSocket functionality
@pytest.mark.asyncio
async def test_websocket_integration():
    """Integration test simulating two players."""
    # This would be a more complex test that sets up actual WebSocket connections
    # and simulates a game between two players
    
    # Create the app and chess manager
    app = create_app()
    chess_manager = get_chess_manager()
    
    # Mock pieces and board for testing
    pieces = []
    board = Mock()
    
    # Initialize the game
    chess_manager.initialize_game(pieces, board)
    
    # Verify the game is initialized
    assert chess_manager.chess_engine is not None
    
    # Start the game
    chess_manager.chess_engine.start_game()
    
    # Verify game started
    assert chess_manager.chess_engine.is_game_over is False