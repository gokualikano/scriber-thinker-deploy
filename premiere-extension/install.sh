#!/bin/bash
# Install Copy to Premiere Pro Browser Extension

echo "📸 Copy to Premiere Pro - Browser Extension Installer"
echo ""

# Create the download folder
DOWNLOAD_DIR="$HOME/Downloads/PremiereBridge"
if [ ! -d "$DOWNLOAD_DIR" ]; then
    mkdir -p "$DOWNLOAD_DIR"
    echo "📁 Created download folder: $DOWNLOAD_DIR"
else
    echo "📁 Download folder exists: $DOWNLOAD_DIR"
fi

# Create Desktop symlink for easy access
DESKTOP_LINK="$HOME/Desktop/PremiereBridge"
if [ ! -L "$DESKTOP_LINK" ]; then
    ln -s "$DOWNLOAD_DIR" "$DESKTOP_LINK"
    echo "🔗 Created Desktop shortcut: $DESKTOP_LINK"
else
    echo "🔗 Desktop shortcut already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Open Chrome browser"
echo "2. Go to: chrome://extensions/"
echo "3. Enable 'Developer mode' (top-right toggle)"
echo "4. Click 'Load unpacked'"
echo "5. Select this folder: $(pwd)"
echo "6. ✅ Extension installed!"
echo ""
echo "🎬 Usage:"
echo "• Right-click any image on any website"
echo "• Select '📸 Copy to Premiere Pro'"
echo "• Image downloads to ~/Downloads/PremiereBridge/"
echo "• Drag from PremiereBridge folder to Premiere timeline"
echo ""
echo "🔧 Folder locations:"
echo "• Downloads: $DOWNLOAD_DIR"
echo "• Desktop link: $DESKTOP_LINK"