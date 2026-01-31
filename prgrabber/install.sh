#!/bin/bash
# PRGrabber Installer

echo "🎬 PRGrabber - Premiere Pro Image Grabber"
echo "========================================="
echo ""

# Create downloads folder
DOWNLOAD_DIR="$HOME/Downloads/PRGrabber"
mkdir -p "$DOWNLOAD_DIR"
echo "📁 Created download folder: $DOWNLOAD_DIR"

# Create Desktop shortcut
DESKTOP_LINK="$HOME/Desktop/PRGrabber"
if [ ! -L "$DESKTOP_LINK" ] && [ ! -d "$DESKTOP_LINK" ]; then
    ln -s "$DOWNLOAD_DIR" "$DESKTOP_LINK"
    echo "🔗 Created Desktop shortcut: $DESKTOP_LINK"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next: Install browser extension"
echo "1. Open Chrome: chrome://extensions/"
echo "2. Enable 'Developer mode'"
echo "3. Click 'Load unpacked'"
echo "4. Select: $(pwd)"
echo ""
echo "🎯 Usage:"
echo "• Right-click any web image"
echo "• Select '🎬 Grab for Premiere Pro'"
echo "• Downloads folder opens"
echo "• Drag image to Premiere timeline"
echo ""
echo "🎬 Ready to grab images for Premiere Pro!"