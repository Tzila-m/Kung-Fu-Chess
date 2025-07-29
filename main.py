#!/usr/bin/env python3
"""
Kung Fu Chess WebSocket Server
==============================

Main entry point for running the Kung Fu Chess WebSocket server.
"""

import logging
import uvicorn
from pathlib import Path

from kungfu_chess.api.server import create_app, get_chess_manager
from kungfu_chess.core.board import Board
from kungfu_chess.core.piece import Piece


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_sample_game():
    """Create a sample game setup for testing."""
    # This is a simplified setup - in a real implementation,
    # you would use the proper piece factory and game setup
    pieces = []
    
    # Create a basic 8x8 board
    try:
        from kungfu_chess.core.img import Img
        img = Img(640, 640)  # 8x8 board, 80x80 pixels per cell
        board = Board(
            cell_H_pix=80,
            cell_W_pix=80,
            W_cells=8,
            H_cells=8,
            img=img,
            cell_H_m=1.0,
            cell_W_m=1.0
        )
    except Exception as e:
        logger.warning(f"Could not create board with graphics: {e}")
        # Create a minimal board for API testing
        board = Board(
            cell_H_pix=80,
            cell_W_pix=80,
            W_cells=8,
            H_cells=8,
            img=None,  # No graphics
            cell_H_m=1.0,
            cell_W_m=1.0
        )
    
    return pieces, board


def main():
    """Main function to run the server."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Kung Fu Chess WebSocket Server...")
    
    # Create the FastAPI app
    app = create_app()
    
    # Initialize a sample game
    try:
        pieces, board = create_sample_game()
        chess_manager = get_chess_manager()
        chess_manager.initialize_game(pieces, board)
        logger.info("Sample game initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize sample game: {e}")
        logger.info("Server will run without initial game setup")
    
    # Run the server
    logger.info("Server starting on http://localhost:8000")
    logger.info("WebSocket endpoint: ws://localhost:8000/ws")
    logger.info("Player-specific endpoint: ws://localhost:8000/ws/{player_id}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    main()