#!/usr/bin/env python3
"""
Run the Chess Server with proper path setup
"""
import sys
import os
import asyncio

# Add the KFC_Py directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
kfc_py_path = os.path.join(current_dir, 'KFC_Py')
sys.path.insert(0, kfc_py_path)

# Now import and run the server
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