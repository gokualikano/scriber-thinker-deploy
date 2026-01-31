#!/bin/bash
# Install Enhanced Copy to Premiere Pro System

echo "🚀 Enhanced Copy to Premiere Pro - Complete Installation"
echo ""

# Create directories
BRIDGE_DIR="$HOME/Desktop/PremiereBridge"
DOWNLOADS_DIR="$HOME/Downloads/PremiereBridge"

echo "📁 Setting up directories..."
mkdir -p "$BRIDGE_DIR"
mkdir -p "$DOWNLOADS_DIR"

# Create Desktop symlink if it doesn't exist
if [ ! -L "$HOME/Desktop/PremiereBridge" ] && [ ! -d "$HOME/Desktop/PremiereBridge" ]; then
    ln -s "$DOWNLOADS_DIR" "$HOME/Desktop/PremiereBridge"
    echo "🔗 Created Desktop shortcut"
fi

# Update manifest to enhanced version
echo "🔧 Updating extension to enhanced version..."
cp premiere-extension/manifest-enhanced.json premiere-extension/manifest.json
echo "✅ Extension updated to Enhanced v2.0"

# Make scripts executable
chmod +x start-premiere-bridge.sh
chmod +x premiere-extension/install.sh

echo ""
echo "🎯 INSTALLATION COMPLETE!"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. INSTALL BROWSER EXTENSION:"
echo "   • Open Chrome → chrome://extensions/"
echo "   • Enable 'Developer mode'"
echo "   • Click 'Load unpacked'"
echo "   • Select: $(pwd)/premiere-extension/"
echo ""
echo "2. START BRIDGE SERVER:"
echo "   • Run: ./start-premiere-bridge.sh"
echo "   • Keep it running while using extension"
echo ""
echo "3. ENHANCED WORKFLOW:"
echo "   • Right-click any web image"
echo "   • Select '📸 Copy to Premiere Pro'"
echo "   • Switch to Premiere Pro"
echo "   • Press Cmd+V in timeline → Image pastes directly!"
echo ""
echo "✨ FEATURES:"
echo "   ✅ Right-click context menu on any image"
echo "   ✅ Direct Cmd+V paste in Premiere Pro timeline"
echo "   ✅ Works with Google Images, Pinterest, any website"
echo "   ✅ Smart filename with timestamps"
echo "   ✅ Visual notifications when copying"
echo "   ✅ Fallback mode if bridge server is offline"
echo ""
echo "🔧 Folders:"
echo "   • Bridge: $BRIDGE_DIR"
echo "   • Downloads: $DOWNLOADS_DIR"
echo ""
echo "Ready to revolutionize your Premiere Pro workflow! 🎬"