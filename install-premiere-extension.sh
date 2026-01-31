#!/bin/bash
# Install PRGrabber Premiere Pro Extension

echo "🎬 Installing PRGrabber Premiere Pro Extension"
echo "=============================================="
echo ""

# Determine CEP extensions directory
CEP_DIR=""

# macOS paths
if [[ "$OSTYPE" == "darwin"* ]]; then
    CEP_DIR="$HOME/Library/Application Support/Adobe/CEP/extensions"
fi

# Create extensions directory if it doesn't exist
if [ ! -d "$CEP_DIR" ]; then
    mkdir -p "$CEP_DIR"
    echo "📁 Created CEP extensions directory: $CEP_DIR"
fi

# Extension source and target
SOURCE_DIR="$(pwd)/premiere-extension"
TARGET_DIR="$CEP_DIR/com.prgrabber.premiere"

# Remove existing installation
if [ -d "$TARGET_DIR" ]; then
    rm -rf "$TARGET_DIR"
    echo "🗑️  Removed existing extension"
fi

# Copy extension files
cp -R "$SOURCE_DIR" "$TARGET_DIR"
echo "📋 Extension copied to: $TARGET_DIR"

# Set permissions
chmod -R 755 "$TARGET_DIR"

# Enable debug mode (allows unsigned extensions)
DEBUG_FILE="$HOME/Library/Preferences/com.adobe.CSXS.9.plist"
if [ -f "$DEBUG_FILE" ]; then
    defaults write com.adobe.CSXS.9 PlayerDebugMode 1
    echo "🔧 Debug mode enabled"
else
    defaults write com.adobe.CSXS.9 PlayerDebugMode 1
    echo "🔧 Created preferences and enabled debug mode"
fi

# Also try CSXS.8 and CSXS.10 for different versions
defaults write com.adobe.CSXS.8 PlayerDebugMode 1 2>/dev/null || true
defaults write com.adobe.CSXS.10 PlayerDebugMode 1 2>/dev/null || true

echo ""
echo "✅ INSTALLATION COMPLETE!"
echo ""
echo "📋 Next Steps:"
echo "1. Restart Adobe Premiere Pro"
echo "2. Go to Window → Extensions → PRGrabber"
echo "3. Paste image URLs directly into the panel"
echo "4. Click 'Import to Timeline' for direct import!"
echo ""
echo "🎯 Usage:"
echo "• Copy image URLs from any website"
echo "• Paste into PRGrabber panel in Premiere"
echo "• Images import directly to your timeline!"
echo ""
echo "📁 Extension Location: $TARGET_DIR"
echo ""
echo "🎬 Ready to grab images directly in Premiere Pro!"