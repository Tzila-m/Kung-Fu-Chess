#!/bin/bash

# Kung Fu Chess Demo Script
# Starts the server and two clients automatically

echo "🎮 Starting Kung Fu Chess Demo"
echo "==============================="

# Function to cleanup processes on exit
cleanup() {
    echo "🛑 Stopping all processes..."
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null
    fi
    if [ ! -z "$WHITE_PID" ]; then
        kill $WHITE_PID 2>/dev/null
    fi
    if [ ! -z "$BLACK_PID" ]; then
        kill $BLACK_PID 2>/dev/null
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Install server dependencies
echo "📦 Installing server dependencies..."
cd server
python3 -m pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "❌ Failed to install server dependencies"
    exit 1
fi
cd ..

# Install client dependencies
echo "📦 Installing client dependencies..."
cd client
python3 -m pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "❌ Failed to install client dependencies"
    exit 1
fi
cd ..

# Start the server
echo "🚀 Starting server..."
cd server
python3 main.py &
SERVER_PID=$!
cd ..

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 3

# Check if server is running
if ! curl -s http://localhost:8000/healthz &> /dev/null; then
    echo "❌ Server failed to start"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo "✅ Server is running on http://localhost:8000"

# Start white client
echo "🚀 Starting white client..."
cd client
python3 white_client.py &
WHITE_PID=$!
cd ..

# Wait a moment
sleep 2

# Start black client
echo "🚀 Starting black client..."
cd client
python3 black_client.py &
BLACK_PID=$!
cd ..

echo ""
echo "🎯 Demo is running!"
echo "   - Server: http://localhost:8000"
echo "   - White client: Started"
echo "   - Black client: Started"
echo ""
echo "👆 Two chess board windows should have opened"
echo "🎮 Drag and drop pieces to make moves"
echo "🛑 Press Ctrl+C to stop all processes"
echo ""

# Wait for processes
wait