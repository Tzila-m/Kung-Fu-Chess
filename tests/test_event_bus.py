"""
Tests for EventBus module
=========================

Comprehensive tests for the Pub/Sub event bus functionality.
"""

import pytest
from unittest.mock import Mock, call
import time

from kungfu_chess.bus.event_bus import EventBus, EventTopics


class TestEventBus:
    """Test cases for EventBus class."""
    
    def test_init(self):
        """Test EventBus initialization."""
        bus = EventBus()
        assert bus._event_count == 0
        assert len(bus._subscribers) == 0
        assert bus.get_all_topics() == []
    
    def test_subscribe_valid(self):
        """Test valid subscription to a topic."""
        bus = EventBus()
        callback = Mock()
        
        bus.subscribe("test_topic", callback)
        
        assert bus.get_subscribers_count("test_topic") == 1
        assert "test_topic" in bus.get_all_topics()
    
    def test_subscribe_invalid_topic(self):
        """Test subscription with invalid topic."""
        bus = EventBus()
        callback = Mock()
        
        with pytest.raises(ValueError, match="Topic must be a non-empty string"):
            bus.subscribe("", callback)
        
        with pytest.raises(ValueError, match="Topic must be a non-empty string"):
            bus.subscribe(None, callback)
        
        with pytest.raises(ValueError, match="Topic must be a non-empty string"):
            bus.subscribe(123, callback)
    
    def test_subscribe_invalid_callback(self):
        """Test subscription with invalid callback."""
        bus = EventBus()
        
        with pytest.raises(ValueError, match="Callback must be callable"):
            bus.subscribe("test_topic", "not_callable")
        
        with pytest.raises(ValueError, match="Callback must be callable"):
            bus.subscribe("test_topic", None)
        
        with pytest.raises(ValueError, match="Callback must be callable"):
            bus.subscribe("test_topic", 123)
    
    def test_publish_valid(self):
        """Test valid event publishing."""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()
        
        bus.subscribe("test_topic", callback1)
        bus.subscribe("test_topic", callback2)
        
        payload = {"data": "test"}
        bus.publish("test_topic", payload)
        
        callback1.assert_called_once_with(payload)
        callback2.assert_called_once_with(payload)
        assert bus.get_event_count() == 1
    
    def test_publish_no_subscribers(self):
        """Test publishing to topic with no subscribers."""
        bus = EventBus()
        
        # Should not raise any errors
        bus.publish("nonexistent_topic", {"data": "test"})
        assert bus.get_event_count() == 1
    
    def test_publish_invalid_topic(self):
        """Test publishing with invalid topic."""
        bus = EventBus()
        
        with pytest.raises(ValueError, match="Topic must be a non-empty string"):
            bus.publish("", {"data": "test"})
        
        with pytest.raises(ValueError, match="Topic must be a non-empty string"):
            bus.publish(None, {"data": "test"})
    
    def test_publish_callback_exception(self):
        """Test publishing when callback raises exception."""
        bus = EventBus()
        
        good_callback = Mock()
        bad_callback = Mock(side_effect=Exception("Test exception"))
        
        bus.subscribe("test_topic", good_callback)
        bus.subscribe("test_topic", bad_callback)
        
        payload = {"data": "test"}
        bus.publish("test_topic", payload)  # Should not raise
        
        # Good callback should still be called
        good_callback.assert_called_once_with(payload)
        bad_callback.assert_called_once_with(payload)
    
    def test_unsubscribe_valid(self):
        """Test valid unsubscription."""
        bus = EventBus()
        callback = Mock()
        
        bus.subscribe("test_topic", callback)
        assert bus.get_subscribers_count("test_topic") == 1
        
        result = bus.unsubscribe("test_topic", callback)
        assert result is True
        assert bus.get_subscribers_count("test_topic") == 0
        assert "test_topic" not in bus.get_all_topics()
    
    def test_unsubscribe_nonexistent_topic(self):
        """Test unsubscribing from nonexistent topic."""
        bus = EventBus()
        callback = Mock()
        
        result = bus.unsubscribe("nonexistent_topic", callback)
        assert result is False
    
    def test_unsubscribe_nonexistent_callback(self):
        """Test unsubscribing nonexistent callback."""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()
        
        bus.subscribe("test_topic", callback1)
        
        result = bus.unsubscribe("test_topic", callback2)
        assert result is False
        assert bus.get_subscribers_count("test_topic") == 1
    
    def test_multiple_subscribers_same_topic(self):
        """Test multiple subscribers to the same topic."""
        bus = EventBus()
        callbacks = [Mock() for _ in range(3)]
        
        for callback in callbacks:
            bus.subscribe("test_topic", callback)
        
        assert bus.get_subscribers_count("test_topic") == 3
        
        payload = {"data": "test"}
        bus.publish("test_topic", payload)
        
        for callback in callbacks:
            callback.assert_called_once_with(payload)
    
    def test_multiple_topics(self):
        """Test multiple topics with different subscribers."""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        bus.subscribe("topic1", callback1)
        bus.subscribe("topic2", callback2)
        bus.subscribe("topic1", callback3)  # Same topic as callback1
        
        assert bus.get_subscribers_count("topic1") == 2
        assert bus.get_subscribers_count("topic2") == 1
        assert set(bus.get_all_topics()) == {"topic1", "topic2"}
        
        # Publish to topic1
        bus.publish("topic1", {"data": "test1"})
        callback1.assert_called_once_with({"data": "test1"})
        callback3.assert_called_once_with({"data": "test1"})
        callback2.assert_not_called()
        
        # Publish to topic2
        bus.publish("topic2", {"data": "test2"})
        callback2.assert_called_once_with({"data": "test2"})
    
    def test_clear_topic(self):
        """Test clearing all subscribers from a topic."""
        bus = EventBus()
        callbacks = [Mock() for _ in range(3)]
        
        for callback in callbacks:
            bus.subscribe("test_topic", callback)
        
        assert bus.get_subscribers_count("test_topic") == 3
        
        removed_count = bus.clear_topic("test_topic")
        assert removed_count == 3
        assert bus.get_subscribers_count("test_topic") == 0
        assert "test_topic" not in bus.get_all_topics()
    
    def test_clear_nonexistent_topic(self):
        """Test clearing nonexistent topic."""
        bus = EventBus()
        
        removed_count = bus.clear_topic("nonexistent_topic")
        assert removed_count == 0
    
    def test_clear_all(self):
        """Test clearing all topics and subscribers."""
        bus = EventBus()
        
        # Add multiple topics with subscribers
        for topic in ["topic1", "topic2", "topic3"]:
            for i in range(2):
                bus.subscribe(topic, Mock())
        
        assert len(bus.get_all_topics()) == 3
        assert sum(bus.get_subscribers_count(topic) for topic in bus.get_all_topics()) == 6
        
        bus.clear_all()
        
        assert len(bus.get_all_topics()) == 0
        # Event count should NOT be reset by clear_all - it tracks total events ever published
    
    def test_event_count(self):
        """Test event count tracking."""
        bus = EventBus()
        callback = Mock()
        bus.subscribe("test_topic", callback)
        
        assert bus.get_event_count() == 0
        
        for i in range(5):
            bus.publish("test_topic", {"count": i})
        
        assert bus.get_event_count() == 5
    
    def test_concurrent_modification_during_publish(self):
        """Test that concurrent modifications during publish don't cause issues."""
        bus = EventBus()
        
        # Callback that unsubscribes itself
        def self_unsubscribing_callback(payload):
            bus.unsubscribe("test_topic", self_unsubscribing_callback)
        
        normal_callback = Mock()
        
        bus.subscribe("test_topic", self_unsubscribing_callback)
        bus.subscribe("test_topic", normal_callback)
        
        # This should not raise any errors
        bus.publish("test_topic", {"data": "test"})
        
        # Normal callback should still be called
        normal_callback.assert_called_once_with({"data": "test"})
        
        # Self-unsubscribing callback should have removed itself
        assert bus.get_subscribers_count("test_topic") == 1


class TestEventTopics:
    """Test cases for EventTopics constants."""
    
    def test_event_topics_constants(self):
        """Test that all required event topics are defined."""
        assert hasattr(EventTopics, 'SCORE_UPDATED')
        assert hasattr(EventTopics, 'MOVE_LOGGED')
        assert hasattr(EventTopics, 'SOUND_REQUEST')
        assert hasattr(EventTopics, 'GAME_STARTED')
        assert hasattr(EventTopics, 'GAME_ENDED')
        assert hasattr(EventTopics, 'PIECE_MOVED')
        assert hasattr(EventTopics, 'PIECE_CAPTURED')
        assert hasattr(EventTopics, 'COLLISION_DETECTED')
        
        # Check that they're strings
        assert isinstance(EventTopics.SCORE_UPDATED, str)
        assert isinstance(EventTopics.MOVE_LOGGED, str)
        assert isinstance(EventTopics.SOUND_REQUEST, str)
        assert isinstance(EventTopics.GAME_STARTED, str)
        assert isinstance(EventTopics.GAME_ENDED, str)
        assert isinstance(EventTopics.PIECE_MOVED, str)
        assert isinstance(EventTopics.PIECE_CAPTURED, str)
        assert isinstance(EventTopics.COLLISION_DETECTED, str)
        
        # Check that they have expected values
        assert EventTopics.SCORE_UPDATED == "score_updated"
        assert EventTopics.MOVE_LOGGED == "move_logged"
        assert EventTopics.SOUND_REQUEST == "sound_request"
        assert EventTopics.GAME_STARTED == "game_started"
        assert EventTopics.GAME_ENDED == "game_ended"