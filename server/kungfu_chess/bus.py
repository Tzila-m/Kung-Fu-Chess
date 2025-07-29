"""
Event Bus for Kung Fu Chess
Handles event publishing and subscription for game events
"""
import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Base event class"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }


class EventBus:
    """
    Async event bus for game events
    Supports publishing and subscribing to events
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
        
    async def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Subscribe to events of a specific type"""
        async with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to event type: {event_type}")
    
    async def unsubscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Unsubscribe from events of a specific type"""
        async with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                    logger.debug(f"Unsubscribed from event type: {event_type}")
                except ValueError:
                    logger.warning(f"Callback not found for event type: {event_type}")
    
    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers"""
        async with self._lock:
            subscribers = self._subscribers.get(event.type, [])
            
        # Call subscribers outside the lock to avoid deadlocks
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback for {event.type}: {e}")
    
    async def publish_event(self, event_type: str, data: Dict[str, Any], source: Optional[str] = None) -> None:
        """Convenience method to publish an event"""
        event = Event(
            type=event_type,
            data=data,
            timestamp=datetime.now(),
            source=source
        )
        await self.publish(event)


# Game-specific events
class GameEventTypes:
    """Constants for game event types"""
    MOVE_EXECUTED = "move_executed"
    MOVE_REJECTED = "move_rejected"
    PIECE_CAPTURED = "piece_captured"
    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    SCORE_UPDATED = "score_updated"
    SOUND_REQUEST = "sound_request"
    COOLDOWN_UPDATED = "cooldown_updated"


# Global event bus instance
event_bus = EventBus()