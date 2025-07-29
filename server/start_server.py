#!/usr/bin/env python3
"""
Start the Chess Server
"""
import asyncio
import sys
import logging
from chess_server import main

if __name__ == "__main__":
    print("🏰 Starting Chess Server...")
    print("Server will run on localhost:8765")
    print("Press Ctrl+C to stop the server")
    print("-" * 40)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)