#!/bin/bash
# Start the Premiere Pro Bridge System

echo "🎬 Starting Premiere Pro Enhanced Bridge System..."
echo ""

# Install required Python packages
echo "📦 Checking Python dependencies..."
pip3 install flask flask-cors pynput requests --user --break-system-packages --quiet 2>/dev/null || echo "Dependencies already available"

# Start the bridge server
echo "🌉 Starting Premiere Pro Bridge Server..."
echo "📡 Server will run on http://localhost:8589"
echo ""
echo "✨ Enhanced Features Active:"
echo "   • Right-click any web image → 'Copy to Premiere Pro'"
echo "   • Switch to Premiere Pro → Press Cmd+V to paste!"
echo "   • Works with browser extension + local bridge"
echo ""
echo "⚠️  Keep this running while using the extension"
echo "⚠️  Press Ctrl+C to stop"
echo ""

# Run the bridge server
python3 premiere-bridge-server.py