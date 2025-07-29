"""
WebSocket API Module
===================

FastAPI-based WebSocket server for real-time Kung Fu Chess gameplay.
"""

from .server import create_app, ChessWebSocketManager

__all__ = ["create_app", "ChessWebSocketManager"]