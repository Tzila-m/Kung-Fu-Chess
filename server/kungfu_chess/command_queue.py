"""
Command Queue for Kung Fu Chess
Thread-safe queue for handling game commands with asyncio
"""
import asyncio
import logging
from collections import deque
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GameCommand:
    """Represents a game command"""
    pgn: str
    player_color: str
    timestamp: datetime
    client_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pgn": self.pgn,
            "player_color": self.player_color,
            "timestamp": self.timestamp.isoformat(),
            "client_id": self.client_id,
            "metadata": self.metadata or {}
        }


class CommandQueue:
    """
    Thread-safe command queue for game commands
    Uses asyncio.Lock for async safety
    """
    
    def __init__(self, max_size: int = 1000):
        self._queue = deque()
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._lock)
        
    async def enqueue(self, command: GameCommand) -> bool:
        """
        Add a command to the queue
        Returns True if successful, False if queue is full
        """
        async with self._lock:
            if len(self._queue) >= self._max_size:
                logger.warning(f"Command queue is full (size: {self._max_size})")
                return False
            
            self._queue.append(command)
            logger.debug(f"Enqueued command: {command.pgn} from {command.player_color}")
            
            # Notify waiting consumers
            self._not_empty.notify()
            return True
    
    async def enqueue_pgn(self, pgn: str, player_color: str, client_id: Optional[str] = None) -> bool:
        """
        Convenience method to enqueue a PGN command
        """
        command = GameCommand(
            pgn=pgn,
            player_color=player_color,
            timestamp=datetime.now(),
            client_id=client_id
        )
        return await self.enqueue(command)
    
    async def dequeue(self) -> Optional[GameCommand]:
        """
        Remove and return the next command from the queue
        Returns None if queue is empty
        """
        async with self._lock:
            if not self._queue:
                return None
            
            command = self._queue.popleft()
            logger.debug(f"Dequeued command: {command.pgn}")
            return command
    
    async def dequeue_blocking(self, timeout: Optional[float] = None) -> Optional[GameCommand]:
        """
        Remove and return the next command from the queue, waiting if necessary
        Returns None if timeout is reached
        """
        async with self._not_empty:
            try:
                await asyncio.wait_for(
                    self._not_empty.wait_for(lambda: len(self._queue) > 0),
                    timeout=timeout
                )
                return self._queue.popleft()
            except asyncio.TimeoutError:
                return None
    
    async def peek(self) -> Optional[GameCommand]:
        """
        Return the next command without removing it
        """
        async with self._lock:
            if not self._queue:
                return None
            return self._queue[0]
    
    async def size(self) -> int:
        """Return the current size of the queue"""
        async with self._lock:
            return len(self._queue)
    
    async def is_empty(self) -> bool:
        """Check if the queue is empty"""
        async with self._lock:
            return len(self._queue) == 0
    
    async def clear(self) -> int:
        """
        Clear all commands from the queue
        Returns the number of commands removed
        """
        async with self._lock:
            count = len(self._queue)
            self._queue.clear()
            logger.info(f"Cleared {count} commands from queue")
            return count
    
    async def get_commands_by_player(self, player_color: str) -> list[GameCommand]:
        """Get all pending commands for a specific player"""
        async with self._lock:
            return [cmd for cmd in self._queue if cmd.player_color == player_color]