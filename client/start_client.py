#!/usr/bin/env python3
"""
Start the Chess Client
"""
import asyncio
import sys
import logging
from chess_client import main

if __name__ == "__main__":
    print("🎮 Starting Chess Client...")
    print("Connecting to server at localhost:8765")
    print("Click on pieces to select and move them")
    print("Close the window to exit")
    print("-" * 40)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Client stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Client error: {e}")
        sys.exit(1)