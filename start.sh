#!/bin/bash

# Start the Executive Board Council (backend + frontend)

echo "========================================"
echo "  Executive Board Council"
echo "  German Production Company Decision Support"
echo "========================================"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "Warning: No .env file found. Copy .env.example to .env and add your OpenRouter API key."
    echo ""
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start the backend
echo "Starting backend server on http://localhost:8001..."
uv run python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start the frontend
echo "Starting frontend on http://localhost:5173..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  Application is running!"
echo "  Open http://localhost:5173 in your browser"
echo "  Press Ctrl+C to stop"
echo "========================================"
echo ""

# Wait for both processes
wait
