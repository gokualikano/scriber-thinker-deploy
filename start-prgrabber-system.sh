#!/bin/bash
# Start PRGrabber Enhanced System

echo "🎬 Starting PRGrabber Enhanced System..."
echo "========================================"
echo ""

# Check if Premiere Pro is running
if pgrep -f "Adobe Premiere Pro 2022" > /dev/null; then
    echo "✅ Adobe Premiere Pro 2022 detected"
else
    echo "⚠️  Adobe Premiere Pro 2022 not running"
    echo "💡 Start Premiere Pro first for best experience"
    echo ""
fi

echo "🌉 Starting Premiere Pro Bridge Server..."
echo "📡 Server will run on http://localhost:8590"
echo ""
echo "✨ Enhanced Features Active:"
echo "   • Browser extension → Right-click → 'Paste to Premiere Timeline'"
echo "   • Direct Cmd+V paste in Premiere Pro timeline"
echo "   • Automatic import to project panel"
echo "   • Fallback clipboard copy if needed"
echo ""
echo "🎯 Usage:"
echo "   1. Right-click any web image"
echo "   2. Select '🎬 Paste to Premiere Timeline'"
echo "   3. Switch to Premiere Pro"
echo "   4. Press Cmd+V anywhere in Premiere"
echo "   5. Image imports and gets ready for timeline!"
echo ""
echo "⚠️  Keep this running while using PRGrabber Enhanced"
echo "⚠️  Press Ctrl+C to stop"
echo ""
echo "🚀 Starting bridge server..."

# Start the Premiere Pro bridge
python3 premiere-bridge.py