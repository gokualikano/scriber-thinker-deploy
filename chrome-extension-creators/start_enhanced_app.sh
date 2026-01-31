#!/bin/bash

echo "🚀 Starting Enhanced Creators Video Automation..."
echo "🔌 With Chrome Extension Support"
echo "================================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# Check if desktop app exists
if [ ! -f "../VideoAutomation/VideoAutomation/video_app_v2.py" ]; then
    echo "❌ Desktop app not found at expected location:"
    echo "   ../VideoAutomation/VideoAutomation/video_app_v2.py"
    echo ""
    echo "📝 Please ensure your desktop app is in the correct location"
    exit 1
fi

echo "✅ Desktop app found"
echo "✅ Starting enhanced app with HTTP server..."
echo ""

# Start the enhanced app
python3 creators_app_enhanced.py

echo ""
echo "👋 Enhanced app closed"