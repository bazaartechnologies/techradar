#!/bin/bash

# Tech Radar Startup Script

echo "🚀 Starting Tech Radar..."
echo ""

# Find an available port
PORT=8000
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
    PORT=$((PORT+1))
done

echo "📡 Starting server on port $PORT..."
echo "🌐 Open your browser to: http://localhost:$PORT"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start server
python3 -m http.server $PORT
