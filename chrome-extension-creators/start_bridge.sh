#!/bin/bash

echo "🌉 Starting Creators Bridge Service..."
echo "🔗 Connects Chrome Extension → Your .dmg Desktop App"
echo "=============================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

echo "✅ Python 3 found"
echo "🚀 Starting bridge service..."
echo ""
echo "💡 Instructions:"
echo "  1. Start your Creators Video Automation.app first"
echo "  2. Keep this bridge service running"
echo "  3. Use Chrome extension normally"
echo ""

# Start the bridge service
python3 creators_bridge.py