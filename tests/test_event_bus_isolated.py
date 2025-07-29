"""
Isolated Tests for EventBus module
==================================

Tests EventBus functionality without importing the full chess engine.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the EventBus module directly from file to avoid package imports
import importlib.util
event_bus_path = project_root / "kungfu_chess" / "bus" / "event_bus.py"
spec = importlib.util.spec_from_file_location("event_bus", event_bus_path)
event_bus_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_bus_module)

EventBus = event_bus_module.EventBus
EventTopics = event_bus_module.EventTopics


class TestEventBusIsolated:
    """Test cases for EventBus class in isolation."""
    
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
    
    def test_clear_all(self):
        """Test clearing all topics and subscribers."""
        bus = EventBus()
        
        # Add multiple topics with subscribers
        for topic in ["topic1", "topic2", "topic3"]:
            for i in range(2):
                bus.subscribe(topic, Mock())
        
        assert len(bus.get_all_topics()) == 3
        
        # Publish some events to increase event count
        for i in range(5):
            bus.publish("topic1", {"count": i})
        
        initial_event_count = bus.get_event_count()
        assert initial_event_count == 5
        
        bus.clear_all()
        
        assert len(bus.get_all_topics()) == 0
        # Event count should NOT be reset by clear_all
        assert bus.get_event_count() == initial_event_count


class TestEventTopicsIsolated:
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