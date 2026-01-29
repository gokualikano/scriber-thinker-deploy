#!/bin/bash
# Build script for Creators Video Automation .dmg

set -e

echo "=========================================="
echo "  Creators Video Automation - Build DMG"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

APP_NAME="Creators Video Automation"
VERSION="2.0"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist "*.dmg" "${APP_NAME}.app"

# Check for required tools
echo "🔍 Checking requirements..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install with: brew install python3"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found"
    exit 1
fi

# Setup virtual environment
echo "📦 Setting up build environment..."
if [ ! -d "buildenv" ]; then
    python3 -m venv buildenv
fi
source buildenv/bin/activate

# Install requirements in venv
pip install --quiet --upgrade pip
pip install --quiet pyinstaller pyqt5

# Create the app bundle using PyInstaller
echo "🔨 Building application..."

pyinstaller --noconfirm --clean \
    --name "${APP_NAME}" \
    --windowed \
    --onedir \
    --icon "logo.icns" \
    --add-data "logo.png:." \
    --add-data "process_timeline.py:." \
    --add-data "automate_videos.py:." \
    --hidden-import "PyQt5.sip" \
    --collect-all "PyQt5" \
    --osx-bundle-identifier "com.creators.videoautomation" \
    video_app_v2.py

# Check if build succeeded
if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo "❌ Build failed - app bundle not created"
    exit 1
fi

echo "✅ App bundle created"

# Create DMG
echo "📀 Creating DMG..."

# Create a temporary folder for DMG contents
DMG_DIR="dist/dmg_contents"
mkdir -p "$DMG_DIR"

# Copy app to DMG folder
cp -R "dist/${APP_NAME}.app" "$DMG_DIR/"

# Create Applications symlink
ln -s /Applications "$DMG_DIR/Applications"

# Create README
cat > "$DMG_DIR/README.txt" << 'EOF'
Creators Video Automation v2.0
==============================

INSTALLATION:
1. Drag "Creators Video Automation.app" to the Applications folder
2. On first run, right-click > Open (to bypass Gatekeeper)

REQUIREMENTS:
- macOS 10.14 or later
- yt-dlp (install with: brew install yt-dlp)

If yt-dlp is not installed, run this in Terminal:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install yt-dlp

USAGE:
1. Open the app
2. Paste YouTube URLs (one per line)
3. Click Download
4. Videos saved to premiere_videos folder

For XML processing:
1. Export Premiere timeline as "Final Cut Pro XML"
2. Drop the file into the app
3. Click Process

Support: [Your contact info here]
EOF

# Check if create-dmg is available, otherwise use hdiutil
if command -v create-dmg &> /dev/null; then
    echo "Using create-dmg..."
    create-dmg \
        --volname "${APP_NAME}" \
        --volicon "logo.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "${APP_NAME}.app" 150 180 \
        --hide-extension "${APP_NAME}.app" \
        --app-drop-link 450 180 \
        "${APP_NAME}_v${VERSION}.dmg" \
        "$DMG_DIR"
else
    echo "Using hdiutil..."
    DMG_PATH="${APP_NAME}_v${VERSION}.dmg"
    hdiutil create -volname "${APP_NAME}" \
        -srcfolder "$DMG_DIR" \
        -ov -format UDZO \
        "$DMG_PATH"
fi

# Cleanup
rm -rf "$DMG_DIR"

echo ""
echo "=========================================="
echo "✅ BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "DMG file: ${APP_NAME}_v${VERSION}.dmg"
echo ""
echo "To distribute:"
echo "1. Share the .dmg file with your team"
echo "2. They drag app to Applications"
echo "3. They need to install yt-dlp: brew install yt-dlp"
echo ""
