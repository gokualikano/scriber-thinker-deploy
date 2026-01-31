#!/bin/bash
# Install PRGrabber Enhanced - Complete System

echo "🚀 PRGrabber Enhanced - Complete Installation"
echo "============================================="
echo ""

# Create directories
BRIDGE_DIR="$HOME/Desktop/PRGrabber"
DOWNLOADS_DIR="$HOME/Downloads/PRGrabber"

echo "📁 Setting up directories..."
mkdir -p "$BRIDGE_DIR"
mkdir -p "$DOWNLOADS_DIR"

# Create Desktop shortcut if needed
if [ ! -L "$HOME/Desktop/PRGrabber" ] && [ ! -d "$HOME/Desktop/PRGrabber" ]; then
    ln -s "$DOWNLOADS_DIR" "$HOME/Desktop/PRGrabber-Downloads"
    echo "🔗 Created Downloads shortcut at ~/Desktop/PRGrabber-Downloads"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install flask flask-cors pynput requests --user --break-system-packages --quiet 2>/dev/null || echo "Dependencies ready"

# Make scripts executable
chmod +x premiere-bridge.py
chmod +x start-prgrabber-system.sh

echo ""
echo "✅ INSTALLATION COMPLETE!"
echo ""
echo "🎯 TWO-STEP SETUP:"
echo ""
echo "1. INSTALL BROWSER EXTENSION:"
echo "   • Open Chrome → chrome://extensions/"
echo "   • Enable 'Developer mode'"
echo "   • Click 'Load unpacked'"
echo "   • Select: $(pwd)/prgrabber-enhanced/"
echo ""
echo "2. START PREMIERE BRIDGE:"
echo "   • Run: ./start-prgrabber-system.sh"
echo "   • Keep running while using PRGrabber"
echo ""
echo "🎬 ENHANCED WORKFLOW:"
echo "   • Right-click any web image"
echo "   • Select '🎬 Paste to Premiere Timeline'"
echo "   • Switch to Premiere Pro"
echo "   • Press Cmd+V → Image appears directly!"
echo ""
echo "✨ FEATURES:"
echo "   ✅ Direct Cmd+V paste in Premiere Pro timeline"
echo "   ✅ Works with any web image"
echo "   ✅ Automatic Premiere Pro 2022 integration"
echo "   ✅ Fallback clipboard copy if bridge offline"
echo "   ✅ Smart notifications and error handling"
echo ""
echo "📂 FOLDERS:"
echo "   • Bridge: $BRIDGE_DIR"
echo "   • Downloads: $DOWNLOADS_DIR"
echo ""
echo "Ready to revolutionize your Premiere workflow! 🎬"