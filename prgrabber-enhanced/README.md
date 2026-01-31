# 🎬 PRGrabber Enhanced

**Direct paste from web images to Premiere Pro timeline with Cmd+V!**

## What's New in Enhanced
- ⚡ **Direct Cmd+V paste** in Premiere Pro timeline
- 🎯 **Auto-import** to Premiere Pro project
- 📋 **Clipboard fallback** when bridge is offline
- 🔄 **Two paste modes**: Timeline paste + Download backup

## Installation

### 1. Browser Extension
1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select this `prgrabber-enhanced` folder

### 2. Premiere Bridge Service
Run from the main folder:
```bash
./start-prgrabber-system.sh
```
Keep this running while using PRGrabber.

## Usage

### Enhanced Mode (Bridge Online)
1. Right-click any web image
2. Select "🎬 Paste to Premiere Timeline"
3. Switch to Premiere Pro
4. Press **Cmd+V** → Image imports directly!

### Fallback Mode (Bridge Offline)
1. Right-click any web image
2. Select "📁 Download for Premiere"
3. Downloads folder opens
4. Drag to Premiere timeline

## Two Right-Click Options
- **🎬 Paste to Premiere Timeline** - Direct paste with Cmd+V
- **📁 Download for Premiere** - Traditional download method

## Technical Details
- **Bridge Service**: Local HTTP server on port 8590
- **Premiere Integration**: AppleScript automation for Premiere Pro 2022
- **Clipboard Support**: Canvas-based image conversion for browsers
- **Fallback**: Automatic download if bridge unavailable

## Workflow Comparison

| Mode | Steps | Speed |
|------|-------|-------|
| **Enhanced** | Right-click → Cmd+V in Premiere | ⚡ 2 steps |
| **Download** | Right-click → Drag from folder | 📁 3 steps |
| **Traditional** | Save As → Navigate → Import → Drag | 😴 6+ steps |

---

**Revolutionary Premiere Pro workflow - from any web image to timeline in 2 steps!**