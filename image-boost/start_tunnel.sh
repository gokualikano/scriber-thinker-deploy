#!/bin/bash

echo "🚀 Starting ImageBoost with Cloudflare tunnel..."

# Start the server in background
cd ~/clawd/image-boost
source venv/bin/activate

echo "📡 Starting ImageBoost server..."
python3 server_bulk.py &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

echo "🌐 Creating cloudflare tunnel..."
cloudflared tunnel --url http://localhost:8587 &
TUNNEL_PID=$!

# Wait for tunnel URL
sleep 5

echo ""
echo "✅ ImageBoost is ready!"
echo "📍 Local: http://localhost:8587" 
echo "🌍 Remote: Check output above for trycloudflare.com URL"
echo ""
echo "Press Ctrl+C to stop both server and tunnel"

# Wait for user to stop
wait