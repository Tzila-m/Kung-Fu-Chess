"""
Event Bus Implementation
========================

A simple pub/sub event bus using the Observer pattern.
Supports topic-based subscriptions and event publishing.
"""

import logging
from typing import Any, Callable, Dict, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventBus:
    """
    A simple event bus implementation using the Observer pattern.
    
    Allows components to subscribe to topics and publish events.
    Events are delivered synchronously to all subscribers.
    """
    
    def __init__(self) -> None:
        """Initialize the event bus with empty subscription registry."""
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = defaultdict(list)
        self._event_count = 0
        
    def subscribe(self, topic: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to a topic with a callback function.
        
        Args:
            topic: The topic name to subscribe to
            callback: Function to call when topic events are published.
                     Must accept a single argument (the event payload).
        
        Raises:
            ValueError: If topic is empty or callback is not callable
        """
        if not topic or not isinstance(topic, str):
            raise ValueError("Topic must be a non-empty string")
        
        if not callable(callback):
            raise ValueError("Callback must be callable")
            
        self._subscribers[topic].append(callback)
        logger.debug(f"Subscribed to topic '{topic}'. Total subscribers: {len(self._subscribers[topic])}")
    
    def unsubscribe(self, topic: str, callback: Callable[[Any], None]) -> bool:
        """
        Unsubscribe a callback from a topic.
        
        Args:
            topic: The topic name to unsubscribe from
            callback: The callback function to remove
            
        Returns:
            True if callback was found and removed, False otherwise
        """
        if topic not in self._subscribers:
            return False
            
        try:
            self._subscribers[topic].remove(callback)
            logger.debug(f"Unsubscribed from topic '{topic}'. Remaining subscribers: {len(self._subscribers[topic])}")
            
            # Clean up empty topic lists
            if not self._subscribers[topic]:
                del self._subscribers[topic]
            
            return True
        except ValueError:
            return False
    
    def publish(self, topic: str, payload: Any) -> None:
        """
        Publish an event to all subscribers of a topic.
        
        Args:
            topic: The topic name to publish to
            payload: The event data to send to subscribers
            
        Raises:
            ValueError: If topic is empty
        """
        if not topic or not isinstance(topic, str):
            raise ValueError("Topic must be a non-empty string")
            
        self._event_count += 1
        subscribers = self._subscribers.get(topic, [])
        
        logger.debug(f"Publishing to topic '{topic}' with {len(subscribers)} subscribers")
        
        # Deliver to all subscribers
        for callback in subscribers[:]:  # Copy list to handle concurrent modifications
            try:
                callback(payload)
            except Exception as e:
                logger.error(f"Error in subscriber callback for topic '{topic}': {e}")
                # Continue with other subscribers even if one fails
    
    def get_subscribers_count(self, topic: str) -> int:
        """
        Get the number of subscribers for a topic.
        
        Args:
            topic: The topic name
            
        Returns:
            Number of subscribers for the topic
        """
        return len(self._subscribers.get(topic, []))
    
    def get_all_topics(self) -> List[str]:
        """
        Get all currently subscribed topics.
        
        Returns:
            List of topic names that have at least one subscriber
        """
        return list(self._subscribers.keys())
    
    def clear_topic(self, topic: str) -> int:
        """
        Remove all subscribers from a topic.
        
        Args:
            topic: The topic name to clear
            
        Returns:
            Number of subscribers that were removed
        """
        if topic not in self._subscribers:
            return 0
            
        count = len(self._subscribers[topic])
        del self._subscribers[topic]
        logger.debug(f"Cleared topic '{topic}', removed {count} subscribers")
        return count
    
    def clear_all(self) -> None:
        """Remove all subscribers from all topics."""
        topic_count = len(self._subscribers)
        subscriber_count = sum(len(subs) for subs in self._subscribers.values())
        
        self._subscribers.clear()
        logger.debug(f"Cleared all topics ({topic_count} topics, {subscriber_count} total subscribers)")
    
    def get_event_count(self) -> int:
        """Get the total number of events published since creation."""
        return self._event_count


# Standard event topics for Kung Fu Chess
class EventTopics:
    """Standard event topic names for Kung Fu Chess."""
    
    SCORE_UPDATED = "score_updated"
    MOVE_LOGGED = "move_logged"
    SOUND_REQUEST = "sound_request"
    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"
    PIECE_MOVED = "piece_moved"
    PIECE_CAPTURED = "piece_captured"
    COLLISION_DETECTED = "collision_detected"