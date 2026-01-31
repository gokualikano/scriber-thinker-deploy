#!/bin/bash
# Start the clipboard monitor for Premiere Pro

echo "🎬 Starting Clipboard to Premiere Pro Bridge..."

# Check if Pillow is installed
if ! python3 -c "import PIL" 2>/dev/null; then
    echo "📦 Installing Pillow (required for image processing)..."
    pip3 install Pillow --user
fi

# Make the script executable
chmod +x clipboard-to-premiere.py

# Start the monitor
python3 clipboard-to-premiere.py