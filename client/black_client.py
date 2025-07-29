#!/usr/bin/env python3
"""
Kung Fu Chess - Black Player Client
GUI application for the black player
"""
import sys
import asyncio
import logging
from typing import Dict, Any
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QThread, Signal, QObject
import qasync

from network import create_client
from ui.board_widget import ChessGameWidget

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GameClient(QObject):
    """
    Main game client that handles networking and GUI coordination
    """
    
    # Signals for communication with GUI thread
    status_updated = Signal(str)
    board_updated = Signal(list)
    player_assigned = Signal(str)
    game_time_updated = Signal(int)
    error_occurred = Signal(str)
    
    def __init__(self, server_url: str = "ws://localhost:8000/ws"):
        super().__init__()
        self.server_url = server_url
        self.ws_client = None
        self.running = False
        
    async def start(self):
        """Start the client and connect to server"""
        self.running = True
        
        # Create WebSocket client
        self.ws_client = create_client(self.server_url, "black")
        
        # Try to connect
        self.status_updated.emit("Connecting to server...")
        if not await self.ws_client.connect():
            self.error_occurred.emit("Failed to connect to server")
            return False
        
        self.status_updated.emit("Connected to server")
        
        # Start listening for events
        asyncio.create_task(self.listen_for_events())
        return True
    
    async def stop(self):
        """Stop the client and disconnect"""
        self.running = False
        if self.ws_client:
            await self.ws_client.disconnect()
    
    async def send_move(self, pgn: str):
        """Send a move to the server"""
        if self.ws_client and self.ws_client.is_connected():
            await self.ws_client.send_command(pgn)
        else:
            self.error_occurred.emit("Not connected to server")
    
    async def listen_for_events(self):
        """Listen for events from the server"""
        if not self.ws_client:
            return
        
        try:
            async for event in self.ws_client.events():
                if not self.running:
                    break
                
                await self.handle_event(event)
                
        except Exception as e:
            logger.error(f"Error in event listener: {e}")
            self.error_occurred.emit(f"Connection error: {e}")
    
    async def handle_event(self, event: Dict[str, Any]):
        """Handle events from the server"""
        event_type = event.get('type')
        
        if event_type == "player_assigned":
            color = event.get('color', 'black')
            self.player_assigned.emit(color)
            self.status_updated.emit(f"Assigned as {color} player")
            
        elif event_type == "game_state":
            state = event.get('state', {})
            pieces = state.get('pieces', [])
            self.board_updated.emit(pieces)
            
            game_time = state.get('game_time_ms', 0)
            self.game_time_updated.emit(game_time)
            
            if state.get('winner'):
                winner = state.get('winner')
                self.status_updated.emit(f"Game Over - {winner} wins!")
            else:
                self.status_updated.emit("Game in progress")
                
        elif event_type == "execute":
            # Move was executed successfully
            board_state = event.get('board', {})
            pieces = board_state.get('pieces', [])
            self.board_updated.emit(pieces)
            
            game_time = board_state.get('game_time_ms', 0)
            self.game_time_updated.emit(game_time)
            
            pgn = event.get('pgn', '')
            player = event.get('player', '')
            logger.info(f"Move executed: {pgn} by {player}")
            
        elif event_type == "error":
            message = event.get('message', 'Unknown error')
            self.error_occurred.emit(message)
            logger.error(f"Server error: {message}")
            
        elif event_type == "game_over":
            winner = event.get('winner', 'Unknown')
            self.status_updated.emit(f"Game Over - {winner} wins!")
            
        elif event_type == "pong":
            # Keepalive response
            pass
            
        else:
            logger.debug(f"Unhandled event type: {event_type}")


class ChessClientApp:
    """Main application class"""
    
    def __init__(self):
        self.app = None
        self.game_widget = None
        self.game_client = None
        
    async def run(self):
        """Run the application"""
        # Create Qt application
        self.app = QApplication(sys.argv)
        
        # Create game widget for black player
        self.game_widget = ChessGameWidget("black")
        self.game_widget.show()
        
        # Create game client
        self.game_client = GameClient()
        
        # Connect signals
        self.game_client.status_updated.connect(self.game_widget.update_status)
        self.game_client.board_updated.connect(self.game_widget.update_board_state)
        self.game_client.player_assigned.connect(self.game_widget.update_player_info)
        self.game_client.game_time_updated.connect(self.game_widget.update_game_time)
        self.game_client.error_occurred.connect(self.show_error)
        
        # Connect move requests from GUI to client
        self.game_widget.move_requested.connect(
            lambda pgn: asyncio.create_task(self.game_client.send_move(pgn))
        )
        
        # Start the game client
        if not await self.game_client.start():
            self.show_error("Failed to start game client")
            return 1
        
        # Set up cleanup
        self.app.aboutToQuit.connect(
            lambda: asyncio.create_task(self.game_client.stop())
        )
        
        # Run the Qt event loop
        await qasync.QEventLoop(self.app).run_forever()
        return 0
    
    def show_error(self, message: str):
        """Show error message to user"""
        if self.game_widget:
            QMessageBox.critical(self.game_widget, "Error", message)
        logger.error(message)


async def main():
    """Main entry point"""
    logger.info("Starting Kung Fu Chess Black Client")
    
    app = ChessClientApp()
    return await app.run()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)