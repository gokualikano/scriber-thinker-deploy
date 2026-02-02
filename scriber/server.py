#!/usr/bin/env python3
"""
Scriber Server - YouTube SEO Optimizer
Extracts transcript, description, tags and generates optimized SEO content
"""

from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, render_template_string
from flask_cors import CORS
from functools import wraps
import subprocess
import json
import os
import re
import time
import base64
import httpx
from pathlib import Path

# Anthropic API - Use environment variable for security
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-me-in-production')
CORS(app)

# Authentication
ACCESS_PASSWORD = os.environ.get('ACCESS_PASSWORD', 'scriber2024')

# Storage
DATA_FILE = Path(__file__).parent / "scriber_data.json"

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
    <title>Scriber - Login</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; padding: 50px; }
        .login-box { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { color: #333; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .error { color: red; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🔒 Scriber Access</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="password" name="password" placeholder="Enter access password" required>
            <button type="submit">Access Scriber</button>
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

@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze_video():
    """Fetch video info, transcript, description, tags"""
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
    
    try:
        # Get video info including description and tags
        cmd = [
            "yt-dlp", 
            "--dump-json", 
            "--skip-download",
            "--no-check-certificate",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "--extractor-retries", "3",
            "--sleep-interval", "1",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if result.returncode != 0:
            error_msg = result.stderr[:500] if result.stderr else "Failed to fetch video info"
            print(f"yt-dlp error: {error_msg}")
            return jsonify({"error": f"Failed to fetch video info: {error_msg}"}), 400
        
        info = json.loads(result.stdout)
        
        # Get transcript
        transcript = ""
        try:
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                sub_cmd = [
                    "yt-dlp",
                    "--skip-download",
                    "--write-subs",
                    "--write-auto-subs",
                    "--sub-langs", "en.*,en",
                    "--sub-format", "vtt",
                    "--output", f"{tmpdir}/%(id)s",
                    "--no-check-certificate",
                    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "--extractor-retries", "3",
                    "--sleep-interval", "1",
                    url
                ]
                subprocess.run(sub_cmd, capture_output=True, text=True, timeout=90)
                
                # Find and parse VTT file
                vtt_files = list(Path(tmpdir).glob("*.vtt"))
                if vtt_files:
                    transcript = parse_vtt(vtt_files[0])
        except Exception as e:
            print(f"Transcript error: {e}")
        
        return jsonify({
            "video_id": video_id,
            "title": info.get('title', ''),
            "description": info.get('description', ''),
            "tags": info.get('tags', []) or [],
            "duration": info.get('duration', 0),
            "channel": info.get('channel', ''),
            "view_count": info.get('view_count', 0),
            "transcript": transcript,
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def parse_vtt(vtt_path):
    """Parse VTT file and extract clean text"""
    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    text_lines = []
    seen_lines = set()
    
    for line in lines:
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            continue
        if '-->' in line:
            continue
        if re.match(r'^\d+$', line.strip()):
            continue
        if not line.strip():
            continue
        
        clean_line = line.strip()
        clean_line = re.sub(r'<[^>]+>', '', clean_line)
        
        if clean_line and clean_line not in seen_lines:
            seen_lines.add(clean_line)
            text_lines.append(clean_line)
    
    text = ' '.join(text_lines)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

@app.route('/api/generate', methods=['POST'])
@login_required
def generate_seo():
    """Generate SEO-optimized description, disclaimer, and tags"""
    data = request.json
    title = data.get('title', '')
    description = data.get('description', '')
    tags = data.get('tags', [])
    transcript = data.get('transcript', '')
    extra_instructions = data.get('extra_instructions', '')
    
    if not title:
        return jsonify({"error": "Missing title"}), 400
    
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "No API key configured"}), 500
    
    try:
        # Build the prompt
        system_prompt = """You are an expert YouTube SEO specialist for disaster/news content channels targeting US audiences.

Your job is to analyze a video's transcript, current description, and tags, then generate:
1. An SEO-optimized description (high CTR, keyword-rich)
2. A professional disclaimer
3. Optimized YouTube tags

CRITICAL: Create completely ORIGINAL content. Do not copy, reference, or include ANY links, phrases, or credits from the source video's description. Treat the source description as reference material only - never copy elements from it into your output.

DESCRIPTION GUIDELINES:
- Start with a compelling hook (first 150 chars show in search)
- Include relevant keywords naturally
- Add timestamps if content allows
- Include call-to-action (subscribe, like, comment)
- 2000-3000 characters ideal
- Use relevant emojis sparingly for visual appeal
- NO fake quotes or made-up testimonials
- NO fabricated names, statements, or statistics
- 100% factual - only describe what actually happened based on the transcript
- News-style writing, no sensationalism
- NEVER include external links, donation links, or buymeacoffee links
- NEVER include URLs to websites or services not owned by the channel
- NO affiliate links, sponsor links, or third-party promotion links
- IGNORE any links from the original video description - do not copy them over
- DO NOT reference other channels, creators, or their donation links
- Create completely fresh content - don't copy phrases or links from source material
- NEVER claim the channel is operated by professionals, experts, scientists, geologists, meteorologists, etc.
- DO NOT invent credentials, qualifications, or professional backgrounds
- Keep channel identity generic - no fake expertise claims

YOUTUBE-SAFE LANGUAGE (CRITICAL):
Avoid these words that trigger demonetization:
- killed, dead, death, died, fatal, deadly
- Use instead: lost their lives, passed away, tragic, devastating, casualties, victims
- massacre, murder, suicide, shooting
- Use instead: incident, tragedy, emergency, crisis
- blood, bloody, graphic
- Use instead: severe, intense, catastrophic

DISCLAIMER GUIDELINES:
- Professional, covers fair use if using news footage
- Mentions educational/informational purpose
- Brief copyright notice
- NEVER claim fake credentials (no "professional geologist", "expert", "scientist", etc.)
- NEVER make up who operates the channel or their qualifications
- Keep generic - don't invent professional backgrounds or expertise claims
- Stick to basic fair use, educational purpose, and copyright disclaimers only
- 2-3 sentences

TAGS GUIDELINES (SEO OPTIMIZED):
- 15-25 tags for maximum reach
- Mix of: broad terms (weather, news, breaking) + specific (location, event name)
- Include searchable phrases people actually type
- Include location names, event types, year/date if relevant
- Put highest-volume search terms first
- No hashtags, just comma-separated words/phrases
- AVOID demonetization trigger words in tags too
- Include trending related terms

OUTPUT FORMAT - Use exactly this format:

**📝 SEO Description:**
[Full description here]

---

**⚠️ Disclaimer:**
[Disclaimer text here]

---

**🏷️ Tags:**
[tag1, tag2, tag3, tag4, tag5, etc...]

---"""

        user_content = f"""Video Title: {title}

Current Description:
{description[:2000] if description else 'No description provided'}

Current Tags: {', '.join(tags) if tags else 'No tags found'}

Transcript (first 3000 chars):
{transcript[:3000] if transcript else 'No transcript available'}"""

        if extra_instructions:
            user_content += f"\n\nExtra Instructions: {extra_instructions}"
        
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
                        "content": user_content
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
        parsed = parse_seo_response(content)
        parsed['raw_response'] = content
        
        return jsonify(parsed)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def clean_unwanted_content(text):
    """Remove unwanted external links and fake credentials from generated content"""
    if not text:
        return text
    
    # Remove buymeacoffee links
    text = re.sub(r'https?://[^\s]*buymeacoffee[^\s]*', '', text, flags=re.IGNORECASE)
    
    # Remove other common donation/external links
    unwanted_patterns = [
        r'https?://[^\s]*patreon[^\s]*',
        r'https?://[^\s]*paypal[^\s]*', 
        r'https?://[^\s]*kofi[^\s]*',
        r'https?://[^\s]*gofundme[^\s]*',
        r'https?://[^\s]*drastrogeotech[^\s]*'
    ]
    
    for pattern in unwanted_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove fake credential claims and source video references
    unwanted_content_patterns = [
        # Fake credentials
        r'This channel is operated by a professional [^.]*\.',
        r'[^.]*professional geologist[^.]*\.',
        r'[^.]*certified expert[^.]*\.',
        r'[^.]*licensed professional[^.]*\.',
        r'[^.]*qualified scientist[^.]*\.',
        r'[^.]*meteorologist[^.]*providing[^.]*\.',
        r'[^.]*expert analysis[^.]*\.',
        
        # References to original video/creator
        r'Original video by[^.]*\.',
        r'Credit to[^.]*\.',
        r'Source:[^.]*\.',
        r'Video courtesy of[^.]*\.',
        r'Thanks to[^.]*for this footage\.',
        r'Support the original creator[^.]*\.',
        
        # Generic donation language that might reference source
        r'Support[^.]*coffee[^.]*\.',
        r'Buy[^.]*coffee[^.]*\.',
        r'Donate[^.]*[^.]*\.',
        
        # Remove specific domain references and creator promotion
        r'Visit[^.]*\.com[^.]*\.',
        r'Check out[^.]*\.com[^.]*\.',
        r'Follow[^.]*\.com[^.]*\.',
        r'Subscribe to[^.]*original[^.]*\.'
    ]
    
    for pattern in unwanted_content_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up multiple newlines/spaces left by removed content
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    text = re.sub(r'  +', ' ', text)
    
    return text.strip()

def parse_seo_response(text):
    """Parse Claude's SEO response into structured data"""
    result = {
        "seo_description": "",
        "disclaimer": "",
        "tags": []
    }
    
    # Parse description
    desc_match = re.search(r'SEO Description:\*?\*?\n(.*?)(?=\n---|\n\*\*⚠️|\Z)', text, re.DOTALL | re.IGNORECASE)
    if desc_match:
        result["seo_description"] = clean_unwanted_content(desc_match.group(1).strip())
    
    # Parse disclaimer
    disc_match = re.search(r'Disclaimer:\*?\*?\n(.*?)(?=\n---|\n\*\*🏷️|\Z)', text, re.DOTALL | re.IGNORECASE)
    if disc_match:
        result["disclaimer"] = clean_unwanted_content(disc_match.group(1).strip())
    
    # Parse tags
    tags_match = re.search(r'Tags:\*?\*?\n(.*?)(?=\n---|\Z)', text, re.DOTALL | re.IGNORECASE)
    if tags_match:
        tags_text = tags_match.group(1).strip()
        # Split by comma and clean
        tags = [t.strip() for t in tags_text.split(',') if t.strip()]
        result["tags"] = tags
    
    return result

@app.route('/api/history')
@login_required
def get_history():
    """Get generation history"""
    storage = load_data()
    sessions = list(storage.get("sessions", {}).values())
    sessions.sort(key=lambda x: x.get('updated_at', 0), reverse=True)
    return jsonify(sessions[:20])

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
        **data,
        "updated_at": time.time()
    }
    save_data(storage)
    
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8586))
    print(f"✍️ Scriber Server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
