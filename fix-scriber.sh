#!/bin/bash
# Scriber Quick Fix Script

echo "🔧 FIXING SCRIBER ON NEW LAPTOP..."

# 1. Install Python dependencies
echo "📦 Installing Python packages..."
pip3 install flask flask-cors httpx pathlib

# 2. Install yt-dlp (critical for video analysis)
echo "📺 Installing yt-dlp..."
pip3 install yt-dlp

# 3. Update yt-dlp (often fixes URL parsing issues)
echo "🔄 Updating yt-dlp..."
pip3 install --upgrade yt-dlp

# 4. Check if port 8586 is available
echo "🔍 Checking port 8586..."
if lsof -i :8586; then
    echo "⚠️  Port 8586 is in use. Killing existing processes..."
    lsof -ti :8586 | xargs kill -9
    sleep 2
fi

# 5. Test yt-dlp functionality
echo "🧪 Testing yt-dlp..."
yt-dlp --version

echo "✅ Setup complete! Now run: python3 scriber/server.py"