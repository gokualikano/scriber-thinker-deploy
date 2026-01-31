#!/bin/bash
# Simple Clipboard Bridge for Premiere Pro

echo "🎬 Starting Premiere Pro Clipboard Bridge..."
echo "📋 Copy images from anywhere - they'll auto-save to ~/Desktop/PremiereBridge/"
echo "🎯 Then just drag from the Bridge folder into your Premiere timeline!"
echo ""

# Install pynput if needed
pip3 install pynput --user --break-system-packages --quiet 2>/dev/null || echo "pynput already available"

# Run the clipboard bridge
python3 premiere-clipboard-paste.py