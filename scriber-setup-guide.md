# 🛠️ SCRIBER SETUP GUIDE - OTHER LAPTOP

## 🚨 QUICK FIX (Run This First):

```bash
# Run the auto-fix script
./fix-scriber.sh

# Then start Scriber
cd scriber
python3 server.py
```

Access at: **http://localhost:8586**

---

## 🔍 COMMON ISSUES & FIXES:

### ❌ Issue 1: "yt-dlp not found"
```bash
pip3 install yt-dlp
# OR if using conda:
conda install yt-dlp
```

### ❌ Issue 2: "Module not found" (Flask, httpx, etc.)
```bash
pip3 install flask flask-cors httpx pathlib
```

### ❌ Issue 3: "Port already in use"
```bash
# Kill existing processes
lsof -ti :8586 | xargs kill -9

# Or change port in server.py (line 315):
app.run(host='0.0.0.0', port=8587, debug=True)
```

### ❌ Issue 4: "YouTube extraction failed"
```bash
# Update yt-dlp to latest version
pip3 install --upgrade yt-dlp

# Test with a simple video
yt-dlp --dump-json "https://youtu.be/dQw4w9WgXcQ"
```

### ❌ Issue 5: "Claude API errors" (500 errors)
The API key is hardcoded. Should work, but if not:
1. Check internet connection
2. API might be rate limited
3. Check Claude API status

---

## 📋 MANUAL INSTALLATION STEPS:

### Step 1: Check Python
```bash
python3 --version  # Should be 3.8+
```

### Step 2: Install Dependencies
```bash
cd scriber
pip3 install -r requirements.txt  # If exists
# OR install manually:
pip3 install flask flask-cors httpx yt-dlp
```

### Step 3: Test yt-dlp
```bash
yt-dlp --version
yt-dlp --dump-json "https://youtu.be/test" | head
```

### Step 4: Start Server
```bash
python3 server.py
```

### Step 5: Test in Browser
Visit: http://localhost:8586

---

## 🚀 WHAT SCRIBER DOES:

- **Extracts** YouTube transcripts, descriptions, tags
- **Generates** SEO-optimized descriptions using Claude AI
- **Creates** professional disclaimers
- **Optimizes** tags for maximum reach
- **Perfect for** your disaster/gun rights/celebrity channels

---

## 🛠️ TROUBLESHOOTING CHECKLIST:

- ✅ Python 3.8+ installed
- ✅ yt-dlp working (`yt-dlp --version`)
- ✅ Flask installed (`python3 -c "import flask"`)
- ✅ Port 8586 free (`lsof -i :8586`)
- ✅ Internet connection working
- ✅ No firewall blocking port

**If still broken, send me the error message!**