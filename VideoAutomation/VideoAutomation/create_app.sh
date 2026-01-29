#!/bin/bash
# Create Mac App Bundle for Creators Video Automation

APP_NAME="Creators Video Automation"
APP_DIR="${APP_NAME}.app"

echo "Creating Mac app bundle: ${APP_NAME}"

# Remove old app if exists
if [ -d "$APP_DIR" ]; then
    echo "Removing old app..."
    rm -rf "$APP_DIR"
fi

# Create app structure
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Creators Video Automation</string>
    <key>CFBundleDisplayName</key>
    <string>Creators Video Automation</string>
    <key>CFBundleIdentifier</key>
    <string>com.creators.videoautomation</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>launch.sh</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create launch script
cat > "$APP_DIR/Contents/MacOS/launch.sh" << 'EOF'
#!/bin/bash
# Get the Resources directory
RESOURCES_DIR="$(dirname "$0")/../Resources"

# Create working directory in user's Documents
WORK_DIR="$HOME/Documents/VideoAutomation"
mkdir -p "$WORK_DIR"

# Copy scripts if they don't exist or are outdated
cp -f "$RESOURCES_DIR/video_app.py" "$WORK_DIR/"
cp -f "$RESOURCES_DIR/automate_videos.py" "$WORK_DIR/"
cp -f "$RESOURCES_DIR/process_timeline.py" "$WORK_DIR/"

# Change to working directory and run
cd "$WORK_DIR"
python3 video_app.py
EOF

chmod +x "$APP_DIR/Contents/MacOS/launch.sh"

# Copy Python scripts to Resources
cp video_app.py "$APP_DIR/Contents/Resources/"
cp automate_videos.py "$APP_DIR/Contents/Resources/"
cp process_timeline.py "$APP_DIR/Contents/Resources/"

echo "✅ App created successfully!"
echo ""
echo "The app is at: ${APP_DIR}"
echo ""
echo "To use:"
echo "1. Drag '${APP_NAME}.app' to Applications folder"
echo "2. Double-click to open"
echo ""
echo "Note: On first launch, Mac may ask for permission."
echo "Go to System Settings → Privacy & Security if blocked."