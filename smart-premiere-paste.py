#!/usr/bin/env python3
"""
Smart Premiere Pro Paste - Optimized Workflow
Import → Auto-select → One keypress to timeline
"""

import os
import time
import subprocess
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pynput import keyboard
import threading

app = Flask(__name__)
CORS(app)

class SmartPremierePaste:
    def __init__(self):
        self.bridge_dir = os.path.expanduser("~/Desktop/PremiereBridge")
        self.latest_image = None
        self.setup_directories()
        
        print("🎬 Smart Premiere Pro Paste Ready!")
        print("📋 Workflow: Right-click → Cmd+V → Enter (adds to timeline)")
        
    def setup_directories(self):
        os.makedirs(self.bridge_dir, exist_ok=True)
        
    def download_image(self, image_url, filename=None):
        """Download image from URL"""
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = 'jpg'  # Default
                if '.' in image_url:
                    ext = image_url.split('.')[-1].split('?')[0].lower()
                    if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        ext = 'jpg'
                filename = f"smart_{timestamp}.{ext}"
            
            filepath = os.path.join(self.bridge_dir, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.latest_image = filepath
            print(f"📸 Ready: {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None
    
    def is_premiere_active(self):
        """Check if Premiere Pro is active"""
        try:
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                return frontApp
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            return "premiere" in result.stdout.strip().lower()
        except:
            return False
    
    def smart_import(self):
        """Import and auto-select for easy timeline addition"""
        if not self.latest_image or not os.path.exists(self.latest_image):
            print("❌ No image ready")
            return False
            
        try:
            filename = os.path.basename(self.latest_image)
            print(f"📥 Smart importing: {filename}")
            
            # Reliable import script
            script = f'''
            tell application "Adobe Premiere Pro 2024"
                activate
            end tell
            
            delay 0.3
            
            tell application "System Events"
                tell process "Adobe Premiere Pro 2024"
                    -- Import (Cmd+I)
                    key code 34 using command down
                    delay 0.8
                    
                    -- Navigate to bridge folder
                    keystroke "g" using {{command down, shift down}}
                    delay 0.4
                    keystroke "{self.bridge_dir}"
                    delay 0.2
                    key code 36 -- Enter
                    delay 0.5
                    
                    -- Select file
                    keystroke "{filename}"
                    delay 0.3
                    key code 36 -- Import
                    delay 0.8
                    
                    -- File should now be selected in project panel
                    -- Ready for Enter key to add to timeline
                    
                end tell
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ Image imported & selected!")
                print("💡 Press ENTER in Premiere to add to timeline at playhead")
                return True
            else:
                print(f"⚠️ Import issue: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Import error: {e}")
            return False

# Global instance
smart_paste = SmartPremierePaste()

@app.route('/copy-image', methods=['POST'])
def copy_image():
    """Browser extension endpoint"""
    try:
        data = request.json
        image_url = data.get('imageUrl')
        filename = data.get('filename')
        
        filepath = smart_paste.download_image(image_url, filename)
        
        if filepath:
            return jsonify({
                'success': True,
                'message': 'Image ready for smart paste',
                'filename': os.path.basename(filepath)
            })
        else:
            return jsonify({'error': 'Download failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'active',
        'mode': 'smart_paste',
        'premiere_active': smart_paste.is_premiere_active(),
        'latest_image': smart_paste.latest_image
    })

def handle_cmd_v():
    """Handle Cmd+V presses"""
    def on_key_press(key):
        try:
            if (hasattr(key, 'char') and key.char == 'v' and 
                smart_paste.is_premiere_active()):
                print("⚡ Cmd+V in Premiere!")
                threading.Thread(target=smart_paste.smart_import, daemon=True).start()
        except:
            pass
    
    with keyboard.Listener(on_press=on_key_press):
        while True:
            time.sleep(1)

def main():
    # Start keyboard monitor
    threading.Thread(target=handle_cmd_v, daemon=True).start()
    
    print("🌐 Smart Paste Server: http://localhost:8589")
    app.run(host='localhost', port=8589, debug=False)

if __name__ == "__main__":
    main()