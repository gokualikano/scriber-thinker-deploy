#!/usr/bin/env python3
"""
Thinker Server - YouTube Thumbnail Analyzer & ImageFX Generator
"""

from flask import Flask, request, jsonify, send_from_directory, Response, session, redirect, url_for, render_template_string
from flask_cors import CORS
from functools import wraps
import subprocess
import json
import os
import re
import time
import threading
import base64
import httpx
from pathlib import Path

# Anthropic API - Use environment variable for security
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-me-in-production-thinker')
CORS(app)

# Authentication
ACCESS_PASSWORD = os.environ.get('ACCESS_PASSWORD', 'thinker2024')

# Storage for generated content
DATA_FILE = Path(__file__).parent / "thinker_data.json"
IMAGES_DIR = Path(__file__).parent / "generated_images"
IMAGES_DIR.mkdir(exist_ok=True)

def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {"sessions": {}}

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2))

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Login page template
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Thinker - Login</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; padding: 50px; }
        .login-box { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { color: #333; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #218838; }
        .error { color: red; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🎨 Thinker Access</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="password" name="password" placeholder="Enter access password" required>
            <button type="submit">Access Thinker</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ACCESS_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error='Incorrect password')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/thumbnail', methods=['POST'])
@login_required
def get_thumbnail():
    """Fetch YouTube thumbnail"""
    data = request.json
    url = data.get('url', '')
    
    # Extract video ID
    video_id = None
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    # Get video info
    try:
        cmd = [
            "yt-dlp", 
            "--dump-json", 
            "--skip-download",
            "--no-check-certificate",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "--extractor-retries", "5",
            "--fragment-retries", "5", 
            "--retry-sleep", "linear=2:5:1",
            "--sleep-interval", "2",
            "--sleep-subtitles", "2",
            "--add-header", "Accept-Language:en-US,en;q=0.9",
            "--add-header", "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        # If main method fails, try fallback with simpler extraction
        if result.returncode != 0:
            print(f"yt-dlp primary method failed: {result.stderr}")
            print("Trying fallback method...")
            
            # Fallback: simpler extraction
            fallback_cmd = [
                "yt-dlp", 
                "--dump-json", 
                "--skip-download",
                "--no-check-certificate",
                "--user-agent", "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                "--extractor-retries", "1",
                "--no-call-home",
                url
            ]
            
            fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=60)
            
            if fallback_result.returncode != 0:
                print(f"yt-dlp fallback also failed: {fallback_result.stderr}")
                print("Using manual fallback with basic video info...")
                
                # Last resort: return basic info using video ID
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                try:
                    import urllib.request
                    urllib.request.urlopen(thumbnail_url, timeout=5)
                except:
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                
                return jsonify({
                    "video_id": video_id,
                    "title": f"YouTube Video {video_id}",
                    "description": "Video info extraction failed, but thumbnail analysis can proceed.",
                    "thumbnail_url": thumbnail_url,
                    "duration": "Unknown",
                    "view_count": "Unknown"
                })
            else:
                result = fallback_result
                print("Fallback method succeeded")
        
        info = json.loads(result.stdout)
        
        # Get best thumbnail (try maxres, fallback to hq)
        import urllib.request
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        try:
            urllib.request.urlopen(thumbnail_url, timeout=3)
        except:
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        
        return jsonify({
            "video_id": video_id,
            "title": info.get('title', ''),
            "duration": info.get('duration', 0),
            "thumbnail_url": thumbnail_url,
            "channel": info.get('channel', ''),
            "view_count": info.get('view_count', 0)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/save', methods=['POST'])
@login_required
def save_generation():
    """Save generated content"""
    data = request.json
    video_id = data.get('video_id')
    
    if not video_id:
        return jsonify({"error": "No video_id"}), 400
    
    storage = load_data()
    storage["sessions"][video_id] = {
        "video_id": video_id,
        "title": data.get('title', ''),
        "thumbnail_url": data.get('thumbnail_url', ''),
        "prompts": data.get('prompts', []),
        "titles": data.get('titles', []),
        "captions": data.get('captions', []),
        "extra_instructions": data.get('extra_instructions', ''),
        "generated_images": data.get('generated_images', []),
        "updated_at": time.time()
    }
    save_data(storage)
    
    return jsonify({"success": True})

@app.route('/api/load/<video_id>')
@login_required
def load_generation(video_id):
    """Load saved generation"""
    storage = load_data()
    session = storage.get("sessions", {}).get(video_id)
    if session:
        return jsonify(session)
    return jsonify({"error": "Not found"}), 404

@app.route('/api/history')
@login_required
def get_history():
    """Get generation history"""
    storage = load_data()
    sessions = list(storage.get("sessions", {}).values())
    sessions.sort(key=lambda x: x.get('updated_at', 0), reverse=True)
    return jsonify(sessions[:20])

@app.route('/api/imagefx/generate', methods=['POST'])
@login_required
def generate_imagefx():
    """Generate image using ImageFX via browser automation"""
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    # Create a unique filename
    timestamp = int(time.time())
    filename = f"imagefx_{timestamp}.png"
    filepath = IMAGES_DIR / filename
    
    # Run browser automation script
    try:
        script_path = Path(__file__).parent / "imagefx_automation.py"
        result = subprocess.run(
            ["python3", str(script_path), prompt, str(filepath)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return jsonify({
                "error": "ImageFX generation failed",
                "details": result.stderr
            }), 500
        
        if filepath.exists():
            return jsonify({
                "success": True,
                "image_path": f"/images/{filename}",
                "filename": filename
            })
        else:
            return jsonify({"error": "Image not saved"}), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Generation timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/images/<filename>')
@login_required
def serve_image(filename):
    """Serve generated images"""
    return send_from_directory(IMAGES_DIR, filename)

@app.route('/api/generate', methods=['POST'])
@login_required
def generate_content():
    """Generate prompts, titles, captions using Claude API"""
    data = request.json
    video_id = data.get('video_id', '')
    title = data.get('title', '')
    thumbnail_url = data.get('thumbnail_url', '')
    extra_instructions = data.get('extra_instructions', '')
    regenerate_only = data.get('regenerate_only', '')  # 'prompts', 'titles', 'captions', or '' for all
    
    if not video_id or not thumbnail_url:
        return jsonify({"error": "Missing video_id or thumbnail_url"}), 400
    
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "No Anthropic API key configured"}), 500
    
    try:
        # Fetch thumbnail image
        import urllib.request
        with urllib.request.urlopen(thumbnail_url, timeout=10) as response:
            image_data = response.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Build the prompt
        system_prompt = """You are Thinker, a YouTube thumbnail and title generator for disaster/news content.

Your job is to analyze a competitor's YouTube thumbnail and generate:
1. ImageFX prompts (for creating similar but better thumbnails)
2. Video titles (80-100 characters)
3. Thumbnail captions (3-5 words)

IMAGEFX PROMPT STYLE (CRITICAL - REALISTIC FOOTAGE ONLY):

LOCATION AWARENESS:
- ALWAYS analyze the title for geographic locations (cities, countries, states, landmarks)
- Include SPECIFIC location details: "downtown Miami streets", "Texas highway", "Japanese coastline", "California wildfire area", "New York residential area"
- Use location-appropriate architecture, vegetation, weather patterns, and terrain
- Include local emergency vehicles/uniforms if relevant

REALISTIC CAPTURE QUALITY (MANDATORY):
- CCTV security camera footage: grainy, fixed angle, timestamp overlay, compression artifacts, low resolution
- Mobile phone capture: vertical orientation option, shaky hands, person running while filming, auto-focus hunting
- Dashboard camera: wide angle lens distortion, date/time stamp, reflection on windshield
- News helicopter footage: aerial view with zoom, slight motion blur, broadcast quality
- Surveillance drone: overhead military/emergency perspective, high contrast
- Body cam footage: first-person POV, badge/equipment visible in frame
- Security footage: black and white or washed out colors, fish-eye lens distortion

NEVER USE: cartoon style, 3D render, game graphics, anime, illustration, drawing, painting, digital art, CGI

REALISM ENHANCERS:
- Specific weather conditions matching the disaster type and location
- Authentic emergency response vehicles and personnel  
- Real architectural styles of the mentioned location
- Actual terrain and vegetation of the geographic area
- Authentic lighting conditions (time of day, weather-related lighting)
- Motion blur, camera shake, compression artifacts, grain, poor lighting
- Raw, unedited footage appearance

PERSPECTIVE VARIETY:
- Ground level: person filming while escaping, crowd POV, car dashboard view
- Elevated: building security cam, helicopter news footage, drone surveillance  
- Close-up: shaky phone footage of immediate danger, body cam perspective
- Wide shot: CCTV overview of large area, traffic cam, weather cam perspective

EXAMPLE LOCATION-AWARE PROMPTS:
- Flood in Miami: "CCTV security camera footage of flooded downtown Miami streets with Art Deco buildings, palm trees bending in storm winds, cars floating past colorful storefronts, grainy timestamp overlay, compression artifacts"
- Earthquake in California: "shaky cellphone video of California residential street during earthquake, Spanish tile roofs, palm trees swaying violently, cracks appearing in sidewalk, motion blur, vertical phone orientation"
- Tornado in Texas: "dashboard camera wide angle view of massive tornado approaching flat Texas farmland, grain silos in background, pickup trucks fleeing on rural highway, date stamp visible, windshield reflection"

TITLE GENERATION (80-100 characters):
- LOCATION-FIRST when mentioned: "Miami Floods Trap Thousands" not "Floods in Miami Trap Thousands"
- BE SPECIFIC: "Downtown Seattle" not just "Seattle", "Texas Highway 35" not just "Texas"
- INCLUDE SCALE: "Massive", "Historic", "Unprecedented" when appropriate
- NEWS-STYLE URGENCY: "Breaking", "Caught on Camera", "Never-Before-Seen"
- REALISTIC IMPACT: Focus on actual consequences, not exaggerated claims

CAPTION STYLE:
- LOCATION-SPECIFIC when possible: "MIAMI UNDERWATER", "TEXAS TORNADO", "JAPAN SHAKEN", "NYC BLACKOUT"  
- DISASTER-SPECIFIC: "FROZEN CHAOS", "COASTLINE CRUMBLING", "GROUND SPLITTING", "WALLS OF WATER"
- URGENT NEWS-STYLE: "NO ONE EXPECTED THIS", "IT HAPPENED SO FAST", "SITUATION CRITICAL", "CAUGHT ON CAMERA"
- REALITY-BASED: "CCTV CAPTURES ALL", "PHONE FOOTAGE", "SECURITY CAM", "LIVE WITNESS", "RAW FOOTAGE"
- Keep it authentic and news-appropriate, avoid sensational or clickbait language

OUTPUT FORMAT - Use exactly this format:
---

**🎨 ImageFX Prompts:**

**1. [Angle name]:**
```
[prompt here]
```

**2. [Angle name]:**
```
[prompt here]
```

(give 3-5 different prompts with different angles)

---

**📝 Titles (80-100 chars):**

1. [title] ([char count])
2. [title] ([char count])
3. [title] ([char count])
4. [title] ([char count])
5. [title] ([char count])

---

**🔥 Thumbnail Captions (10):**

1. [CAPTION]
2. [CAPTION]
3. [CAPTION]
4. [CAPTION]
5. [CAPTION]
6. [CAPTION]
7. [CAPTION]
8. [CAPTION]
9. [CAPTION]
10. [CAPTION]

---"""

        user_prompt = f"""Analyze this YouTube thumbnail for disaster/news content.

VIDEO TITLE: "{title}"

ANALYSIS REQUIREMENTS:
1. EXTRACT LOCATIONS: Identify any cities, countries, states, landmarks, or geographic areas mentioned in the title
2. IDENTIFY DISASTER TYPE: Determine the specific type of disaster/event (flood, earthquake, fire, storm, etc.)
3. CONTEXT UNDERSTANDING: Consider what the video is likely showing based on the title

LOCATION-SPECIFIC DETAILS TO INCLUDE:
- If location mentioned: Use authentic geographic features, architecture, local emergency services
- If no location: Use generic but realistic settings appropriate for the disaster type
- Consider climate and terrain of the mentioned area
- Include region-appropriate vehicles, buildings, and landscape features"""
        
        if extra_instructions:
            user_prompt += f"\n\nADDITIONAL INSTRUCTIONS: {extra_instructions}"
        
        # Handle regeneration of specific sections
        if regenerate_only == 'prompts':
            user_prompt += "\n\nONLY generate new ImageFX prompts. Skip titles and captions. Give 5 completely different prompts with new angles."
        elif regenerate_only == 'titles':
            user_prompt += "\n\nONLY generate new titles. Skip prompts and captions. Give 5 completely different high-CTR titles."
        elif regenerate_only == 'captions':
            user_prompt += "\n\nONLY generate new thumbnail captions. Skip prompts and titles. Give 10 completely different captions."
        
        # Call Claude API
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": user_prompt
                            }
                        ]
                    }
                ]
            },
            timeout=120
        )
        
        if response.status_code != 200:
            return jsonify({"error": f"Claude API error: {response.text}"}), 500
        
        result = response.json()
        content = result.get('content', [{}])[0].get('text', '')
        
        # Parse the response
        parsed = parse_claude_response(content)
        parsed['raw_response'] = content
        
        return jsonify(parsed)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def parse_claude_response(text):
    """Parse Claude's response into structured data"""
    result = {
        "prompts": [],
        "titles": [],
        "captions": []
    }
    
    # Parse ImageFX prompts (text between ```)
    prompt_matches = re.findall(r'```\n?(.*?)\n?```', text, re.DOTALL)
    result["prompts"] = [p.strip() for p in prompt_matches if p.strip() and len(p.strip()) > 50]
    
    # Parse titles (numbered list)
    title_matches = re.findall(r'\d+\.\s*([^(\n]+?)(?:\s*\(\d+\))?(?:\n|$)', text)
    # Filter to only those that look like titles (80-150 chars, after "Titles" section)
    titles_section = re.search(r'Titles.*?:(.*?)(?=\*\*🔥|\*\*\s*🔥|---|\Z)', text, re.DOTALL | re.IGNORECASE)
    if titles_section:
        title_matches = re.findall(r'\d+\.\s*([^(\n]+?)(?:\s*\(\d+\))?(?:\n|$)', titles_section.group(1))
        result["titles"] = [t.strip() for t in title_matches if 50 < len(t.strip()) < 150]
    
    # Parse captions (after "Captions" section)
    captions_section = re.search(r'Captions.*?:(.*?)(?=---|$)', text, re.DOTALL | re.IGNORECASE)
    if captions_section:
        caption_matches = re.findall(r'\d+\.\s*([A-Z][A-Z\s\']+?)(?:\n|$)', captions_section.group(1))
        result["captions"] = [c.strip() for c in caption_matches if 2 < len(c.strip()) < 50]
    
    return result

@app.route('/api/parse', methods=['POST'])
@login_required
def parse_response():
    """Parse Jarvis response into structured data"""
    data = request.json
    text = data.get('text', '')
    
    result = {
        "prompts": [],
        "titles": [],
        "captions": []
    }
    
    # Parse ImageFX prompts (text between ```)
    prompt_matches = re.findall(r'```\n?(.*?)\n?```', text, re.DOTALL)
    result["prompts"] = [p.strip() for p in prompt_matches if p.strip()]
    
    # Parse titles (numbered list after "Titles")
    title_section = re.search(r'Titles.*?:(.*?)(?=\*\*|🔥|$)', text, re.DOTALL | re.IGNORECASE)
    if title_section:
        titles = re.findall(r'\d+\.\s*(.+?)(?:\(\d+\))?(?:\n|$)', title_section.group(1))
        result["titles"] = [t.strip() for t in titles if t.strip()]
    
    # Parse captions (numbered list after "Captions")
    caption_section = re.search(r'Captions.*?:(.*?)(?=---|$)', text, re.DOTALL | re.IGNORECASE)
    if caption_section:
        captions = re.findall(r'\d+\.\s*(.+?)(?:\n|$)', caption_section.group(1))
        result["captions"] = [c.strip() for c in captions if c.strip()]
    
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8585))
    print(f"🧠 Thinker Server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
