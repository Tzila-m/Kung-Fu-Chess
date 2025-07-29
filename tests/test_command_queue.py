"""
Tests for the Command Queue
"""
import pytest
import asyncio
from datetime import datetime
from server.kungfu_chess.command_queue import CommandQueue, GameCommand


class TestCommandQueue:
    """Test cases for the command queue"""
    
    @pytest.fixture
    def queue(self):
        """Create a command queue for testing"""
        return CommandQueue(max_size=10)
    
    @pytest.fixture
    def sample_command(self):
        """Create a sample command for testing"""
        return GameCommand(
            pgn="Pe2e4",
            player_color="white",
            timestamp=datetime.now(),
            client_id="test_client"
        )
    
    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self, queue, sample_command):
        """Test basic enqueue and dequeue operations"""
        # Queue should be empty initially
        assert await queue.is_empty()
        assert await queue.size() == 0
        
        # Enqueue a command
        success = await queue.enqueue(sample_command)
        assert success
        assert not await queue.is_empty()
        assert await queue.size() == 1
        
        # Dequeue the command
        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.pgn == sample_command.pgn
        assert dequeued.player_color == sample_command.player_color
        
        # Queue should be empty again
        assert await queue.is_empty()
        assert await queue.size() == 0
    
    @pytest.mark.asyncio
    async def test_enqueue_pgn_convenience(self, queue):
        """Test the convenience method for enqueueing PGN"""
        success = await queue.enqueue_pgn("Qd1d5", "black", "client123")
        assert success
        
        command = await queue.dequeue()
        assert command.pgn == "Qd1d5"
        assert command.player_color == "black"
        assert command.client_id == "client123"
    
    @pytest.mark.asyncio
    async def test_queue_order_fifo(self, queue):
        """Test that queue follows FIFO order"""
        commands = []
        for i in range(5):
            cmd = GameCommand(f"P{i}2{i}4", "white", datetime.now())
            commands.append(cmd)
            await queue.enqueue(cmd)
        
        # Dequeue should return commands in same order
        for i in range(5):
            dequeued = await queue.dequeue()
            assert dequeued.pgn == commands[i].pgn
    
    @pytest.mark.asyncio
    async def test_queue_max_size(self):
        """Test queue maximum size enforcement"""
        small_queue = CommandQueue(max_size=2)
        
        # Fill the queue to capacity
        cmd1 = GameCommand("Pe2e4", "white", datetime.now())
        cmd2 = GameCommand("Pe7e5", "black", datetime.now())
        cmd3 = GameCommand("Pd2d4", "white", datetime.now())
        
        assert await small_queue.enqueue(cmd1)
        assert await small_queue.enqueue(cmd2)
        assert await small_queue.size() == 2
        
        # Third command should be rejected
        assert not await small_queue.enqueue(cmd3)
        assert await small_queue.size() == 2
    
    @pytest.mark.asyncio
    async def test_peek(self, queue, sample_command):
        """Test peek functionality"""
        # Peek on empty queue
        peeked = await queue.peek()
        assert peeked is None
        
        # Add command and peek
        await queue.enqueue(sample_command)
        peeked = await queue.peek()
        assert peeked is not None
        assert peeked.pgn == sample_command.pgn
        
        # Queue should still have the command
        assert await queue.size() == 1
        
        # Dequeue should return the same command
        dequeued = await queue.dequeue()
        assert dequeued.pgn == sample_command.pgn
    
    @pytest.mark.asyncio
    async def test_clear(self, queue):
        """Test queue clear functionality"""
        # Add multiple commands
        for i in range(5):
            cmd = GameCommand(f"P{i}2{i}4", "white", datetime.now())
            await queue.enqueue(cmd)
        
        assert await queue.size() == 5
        
        # Clear the queue
        cleared_count = await queue.clear()
        assert cleared_count == 5
        assert await queue.is_empty()
        assert await queue.size() == 0
    
    @pytest.mark.asyncio
    async def test_get_commands_by_player(self, queue):
        """Test filtering commands by player"""
        # Add commands for both players
        white_cmd1 = GameCommand("Pe2e4", "white", datetime.now())
        black_cmd1 = GameCommand("Pe7e5", "black", datetime.now())
        white_cmd2 = GameCommand("Pd2d4", "white", datetime.now())
        
        await queue.enqueue(white_cmd1)
        await queue.enqueue(black_cmd1)
        await queue.enqueue(white_cmd2)
        
        # Get white player commands
        white_commands = await queue.get_commands_by_player("white")
        assert len(white_commands) == 2
        assert all(cmd.player_color == "white" for cmd in white_commands)
        
        # Get black player commands
        black_commands = await queue.get_commands_by_player("black")
        assert len(black_commands) == 1
        assert black_commands[0].player_color == "black"
    
    @pytest.mark.asyncio
    async def test_dequeue_blocking_timeout(self, queue):
        """Test blocking dequeue with timeout"""
        # Should return None immediately on empty queue with timeout
        start_time = asyncio.get_event_loop().time()
        result = await queue.dequeue_blocking(timeout=0.1)
        end_time = asyncio.get_event_loop().time()
        
        assert result is None
        assert (end_time - start_time) >= 0.1
    
    def test_command_to_dict(self, sample_command):
        """Test command serialization"""
        cmd_dict = sample_command.to_dict()
        
        assert cmd_dict['pgn'] == sample_command.pgn
        assert cmd_dict['player_color'] == sample_command.player_color
        assert cmd_dict['client_id'] == sample_command.client_id
        assert 'timestamp' in cmd_dict