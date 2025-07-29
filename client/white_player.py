#!/usr/bin/env python3
"""
Kung Fu Chess - White Player Client
"""
import logging
import sys
import os

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_client import ChessGUIClient


def main():
    """Main entry point for white player"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - White Player - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Kung Fu Chess - White Player")
    
    # Create client with specific title for white player
    client = ChessGUIClient()
    client.root.title("Kung Fu Chess - White Player")
    client.root.configure(bg='#f0f0f0')
    
    # Run the client
    client.run()


if __name__ == "__main__":
    main()