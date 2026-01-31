# 📹 Paste to Creators - Chrome Extension

**Right-click YouTube videos → Send directly to your desktop app!**

This Chrome extension eliminates the copy-paste step by letting you right-click any YouTube video and send it directly to your Creators Video Automation desktop app.

---

## 🚀 Quick Start

### **1. Install Chrome Extension**

1. **Open Chrome** → Go to `chrome://extensions/`
2. **Enable "Developer mode"** (toggle in top-right)
3. **Click "Load unpacked"**
4. **Select this folder:** `chrome-extension-creators/`
5. **Extension installs** with yellow icon 📹

### **2. Start Enhanced Desktop App**

```bash
cd chrome-extension-creators
python3 launch_enhanced_app.py
```

**Or integrate with existing app:**
```bash
python3 integrate_with_app.py
```

### **3. Use Extension**

1. **Go to any YouTube video** in Chrome
2. **Right-click** the video or page
3. **Select "📹 Paste to Creators"**
4. **URL automatically appears** in your desktop app!

---

## ✨ Features

### **🎯 Multiple Ways to Send Videos:**

- **Right-click menu** on YouTube links
- **Right-click menu** on current video page  
- **Keyboard shortcut:** `Ctrl+Shift+C`
- **Extension popup** → "Send Current Video"

### **🔄 Smart Communication:**

- **Local HTTP server** in desktop app
- **Instant URL transfer** (no clipboard needed)
- **Visual feedback** when URLs are received
- **Connection status** in extension popup

### **🛡️ Safe & Secure:**

- **Local communication only** (no external servers)
- **Works offline** 
- **No data collection**
- **Open source code**

---

## 🔧 Technical Details

### **How It Works:**

1. **Chrome Extension** detects YouTube pages
2. **Right-click** creates context menu
3. **HTTP POST** sends URL to `localhost:7898`
4. **Desktop app** receives URL via HTTP server
5. **URL auto-populates** in the input field

### **Communication Protocol:**

```javascript
// Extension → Desktop App
POST http://localhost:7898/paste-url
{
  "url": "https://youtube.com/watch?v=...",
  "timestamp": 1643723400000,
  "source": "chrome-extension"
}
```

### **Desktop App Integration:**

```python
# Add to your existing app
from desktop_server_addon import add_extension_support

# Enable extension support
extension_server = add_extension_support(main_window, url_text_widget)
```

---

## 📋 Installation Guide

### **Method A: One-Click Setup**

```bash
cd chrome-extension-creators
python3 integrate_with_app.py
```

### **Method B: Manual Integration**

1. **Copy `desktop_server_addon.py`** to your desktop app folder
2. **Import and integrate** in your main app:

```python
from desktop_server_addon import add_extension_support

class YourVideoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... your existing code ...
        
        # Add extension support
        self.extension_server = add_extension_support(self, self.url_text)
```

3. **Install Chrome extension** (Developer mode)
4. **Run your enhanced app**

---

## 🎮 Usage Instructions

### **For Team Members:**

1. **Install extension once** (takes 30 seconds)
2. **Right-click any YouTube video**
3. **Select "📹 Paste to Creators"**  
4. **Video appears in desktop app automatically**

### **Keyboard Shortcut:**
- **`Ctrl+Shift+C`** on any YouTube page
- **Faster than right-clicking**

### **Extension Popup:**
- **Click extension icon** in Chrome toolbar
- **Shows connection status** 
- **"Send Current Video" button**
- **Quick connection test**

---

## 🔍 Troubleshooting

### **"🔴 Desktop app not running"**
- **Start the desktop app first**
- **Check it's the enhanced version** with extension support
- **Verify port 7898** is not blocked

### **"Failed to fetch video info"**
- **Check internet connection**
- **Try different YouTube URL**
- **Desktop app logs** show specific errors

### **Extension not working:**
- **Reload extension** in `chrome://extensions/`
- **Check Developer mode** is enabled
- **Try refreshing** YouTube page

### **Context menu not appearing:**
- **Make sure** you're on a YouTube page
- **Right-click directly** on video or page
- **Extension icon** should be active

---

## 🚀 Advanced Features

### **Custom Port:**
```python
# Change default port in desktop app
extension_server = ExtensionServer(port=9999)
```

### **Multiple Apps:**
- **Run multiple instances** on different ports
- **Extension supports** port configuration
- **Each app** gets its own extension connection

### **API Endpoints:**
- **`GET /ping`** → Connection test
- **`POST /paste-url`** → Send video URL
- **CORS enabled** for Chrome extension access

---

## 📝 File Structure

```
chrome-extension-creators/
├── 📄 manifest.json          # Extension configuration
├── 🔧 background.js           # Context menu & communication  
├── 📱 content.js              # YouTube page integration
├── 🎨 popup.html              # Extension popup interface
├── ⚙️ popup.js                # Popup functionality
├── 🖼️ icon16.png, icon48.png  # Extension icons
├── 🐍 desktop_server_addon.py # HTTP server for desktop app
├── 🔗 integrate_with_app.py   # Integration helper
├── 🚀 launch_enhanced_app.py  # Enhanced app launcher  
└── 📖 README.md               # This file
```

---

## 🎯 Benefits

### **⏰ Time Savings:**
- **No more copy-paste** between browser and app
- **Right-click → Done** (2-second workflow)
- **Batch processing** multiple videos faster

### **👥 Team Efficiency:**
- **Same workflow** for everyone
- **No training needed** (intuitive right-click)
- **Works with any YouTube URL**

### **🔄 Better UX:**
- **Visual feedback** when URLs are sent
- **Connection status** always visible
- **Keyboard shortcuts** for power users

---

## 💡 Usage Tips

1. **Keep desktop app running** while browsing YouTube
2. **Use keyboard shortcut** `Ctrl+Shift+C` for speed
3. **Check extension popup** if connection issues
4. **Green highlight** on video = URL sent successfully
5. **Multiple URLs** can be sent quickly (batch mode)

---

**🎉 Enjoy faster YouTube video automation!** 

No more copying URLs manually - just right-click and go! 🚀