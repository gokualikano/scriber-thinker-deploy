#!/bin/bash

echo "🎨 Starting ImageBoost PRO with tunnel..."

cd ~/clawd/image-boost
source venv/bin/activate

echo "📡 Starting ImageBoost PRO server..."
python3 server_improved.py &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

echo "🌐 Creating cloudflare tunnel..."
cloudflared tunnel --url http://localhost:8587 &
TUNNEL_PID=$!

# Wait for tunnel URL
sleep 5

echo ""
echo "✅ ImageBoost PRO is ready!"
echo "📍 Local: http://localhost:8587" 
echo "🌍 Remote: Check output above for trycloudflare.com URL"
echo ""
echo "🎨 NEW FEATURES:"
echo "  • Better color preservation"
echo "  • Individual download buttons"
echo "  • Gentle background removal"
echo "  • Corner-based background detection"
echo ""
echo "Press Ctrl+C to stop both server and tunnel"

# Wait for user to stop
wait