"""
Kung Fu Chess - Real-time Chess Engine
=====================================

A Python implementation of Kung Fu Chess with real-time movement,
event-driven architecture, and WebSocket API support.
"""

__version__ = "2.0.0"
__author__ = "Kung Fu Chess Team"

from kungfu_chess.core.engine import ChessEngine
from kungfu_chess.bus.event_bus import EventBus
from kungfu_chess.api.server import create_app

__all__ = ["ChessEngine", "EventBus", "create_app"]