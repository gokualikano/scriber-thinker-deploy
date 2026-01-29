#!/bin/bash
# One-click installer for team members
# Run this on a fresh Mac to set everything up

set -e

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   CREATORS VIDEO AUTOMATION - TEAM INSTALLER           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This installer is for macOS only"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📍 Installing to: ~/Documents/VideoAutomation"
echo ""

# Create installation directory
INSTALL_DIR="$HOME/Documents/VideoAutomation"
mkdir -p "$INSTALL_DIR"

# Install Homebrew if needed
if ! command -v brew &> /dev/null; then
    echo "🍺 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add brew to path for Apple Silicon
    if [[ $(uname -m) == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo "✅ Homebrew already installed"
fi

# Install Python3
if ! command -v python3 &> /dev/null; then
    echo "🐍 Installing Python3..."
    brew install python3
else
    echo "✅ Python3 already installed"
fi

# Install yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo "📥 Installing yt-dlp..."
    brew install yt-dlp
else
    echo "✅ yt-dlp already installed"
    echo "   Updating to latest version..."
    brew upgrade yt-dlp 2>/dev/null || true
fi

# Install PyQt5
echo "🎨 Installing PyQt5..."
pip3 install --quiet --upgrade PyQt5

# Copy application files
echo "📁 Copying application files..."
cp "$SCRIPT_DIR/video_app_v2.py" "$INSTALL_DIR/video_app.py"
cp "$SCRIPT_DIR/process_timeline.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/automate_videos.py" "$INSTALL_DIR/"

if [ -f "$SCRIPT_DIR/logo.png" ]; then
    cp "$SCRIPT_DIR/logo.png" "$INSTALL_DIR/"
fi

if [ -f "$SCRIPT_DIR/logo.icns" ]; then
    cp "$SCRIPT_DIR/logo.icns" "$INSTALL_DIR/"
fi

# Create launch script
cat > "$INSTALL_DIR/launch.command" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:$PATH"
python3 video_app.py
EOF
chmod +x "$INSTALL_DIR/launch.command"

# Create desktop shortcut (Automator app)
echo "🖥️  Creating desktop app..."
APP_PATH="$HOME/Desktop/Creators Video Automation.app"
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Copy icon if exists
if [ -f "$INSTALL_DIR/logo.icns" ]; then
    cp "$INSTALL_DIR/logo.icns" "$APP_PATH/Contents/Resources/AppIcon.icns"
fi

# Create Info.plist
cat > "$APP_PATH/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.creators.videoautomation</string>
    <key>CFBundleName</key>
    <string>Creators Video Automation</string>
    <key>CFBundleVersion</key>
    <string>2.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
</dict>
</plist>
EOF

# Create launcher
cat > "$APP_PATH/Contents/MacOS/launch" << EOF
#!/bin/bash
export PATH="/opt/homebrew/bin:/usr/local/bin:\$PATH"
cd "$INSTALL_DIR"
/opt/homebrew/bin/python3 video_app.py 2>/dev/null || /usr/local/bin/python3 video_app.py 2>/dev/null || python3 video_app.py
EOF
chmod +x "$APP_PATH/Contents/MacOS/launch"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   ✅ INSTALLATION COMPLETE!                            ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📍 App location: $APP_PATH"
echo "📁 Files location: $INSTALL_DIR"
echo ""
echo "To launch the app:"
echo "  • Double-click 'Creators Video Automation' on your Desktop"
echo "  • Or run: open \"$APP_PATH\""
echo ""
echo "If the app doesn't open on first try:"
echo "  1. Right-click the app"
echo "  2. Select 'Open'"
echo "  3. Click 'Open' in the dialog"
echo ""
read -p "Press Enter to launch the app now..."

open "$APP_PATH"
