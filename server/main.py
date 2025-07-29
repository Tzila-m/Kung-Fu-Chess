"""
Main entry point for Kung Fu Chess Server
Runs the FastAPI server with uvicorn
"""
import logging
import uvicorn
from kungfu_chess.api_ws import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )