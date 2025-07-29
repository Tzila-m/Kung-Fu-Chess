#!/usr/bin/env python3
"""
Run the Chess Client with proper path setup
"""
import sys
import os
import asyncio

# Add the KFC_Py directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
kfc_py_path = os.path.join(current_dir, 'KFC_Py')
sys.path.insert(0, kfc_py_path)

# Now import and run the client
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