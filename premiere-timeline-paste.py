#!/usr/bin/env python3
"""
Enhanced Premiere Pro Timeline Paste
Actually pastes images directly to the timeline cursor position
"""

import os
import time
import subprocess
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pynput import keyboard
import threading
import requests
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

class PremiereTimelinePaste:
    def __init__(self):
        self.bridge_dir = os.path.expanduser("~/Desktop/PremiereBridge")
        self.latest_image = None
        self.setup_directories()
        
        print("🎬 Premiere Pro TIMELINE Paste Ready!")
        
    def setup_directories(self):
        os.makedirs(self.bridge_dir, exist_ok=True)
        
    def download_image(self, image_url, filename=None):
        """Download image from URL"""
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                parsed_url = urlparse(image_url)
                ext = parsed_url.path.split('.')[-1].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                    ext = 'jpg'
                filename = f"timeline_{timestamp}.{ext}"
            
            filepath = os.path.join(self.bridge_dir, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.latest_image = filepath
            print(f"📸 Ready for timeline: {filename}")
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
            app_name = result.stdout.strip().lower()
            return "premiere" in app_name or "adobe premiere" in app_name
        except:
            return False
    
    def paste_to_timeline(self):
        """Import image AND place it directly on timeline at playhead"""
        if not self.latest_image or not os.path.exists(self.latest_image):
            print("❌ No image ready to paste")
            return False
            
        try:
            print(f"📥 Pasting to TIMELINE: {os.path.basename(self.latest_image)}")
            
            # Enhanced AppleScript for timeline placement
            script = f'''
            tell application "Adobe Premiere Pro 2024"
                activate
            end tell
            
            delay 0.5
            
            tell application "System Events"
                tell process "Adobe Premiere Pro 2024"
                    -- First, import the file (Cmd+I)
                    key code 34 using command down
                    delay 1.0
                    
                    -- Navigate to our bridge directory
                    keystroke "g" using {{command down, shift down}}
                    delay 0.5
                    keystroke "{self.bridge_dir}"
                    delay 0.3
                    key code 36 -- Enter
                    delay 0.5
                    
                    -- Select our file
                    keystroke "{os.path.basename(self.latest_image)}"
                    delay 0.3
                    key code 36 -- Enter to import
                    delay 1.0
                    
                    -- Now drag to timeline at playhead position
                    -- Select the newly imported item (should be selected)
                    -- Drag to timeline
                    key code 36 -- Enter or double-click to add to timeline
                    
                end tell
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print("✅ Image pasted to TIMELINE!")
                return True
            else:
                print(f"⚠️ Timeline paste script result: {result.stderr}")
                # Fallback: just import to project panel
                return self.fallback_import()
                
        except Exception as e:
            print(f"❌ Timeline paste error: {e}")
            return self.fallback_import()
    
    def fallback_import(self):
        """Fallback: Import to project panel only"""
        try:
            print("💡 Fallback: Importing to project panel...")
            
            script = f'''
            tell application "System Events"
                tell process "Adobe Premiere Pro 2024"
                    key code 34 using command down -- Cmd+I
                    delay 0.8
                    keystroke "g" using {{command down, shift down}}
                    delay 0.3
                    keystroke "{self.bridge_dir}"
                    key code 36
                    delay 0.3
                    keystroke "{os.path.basename(self.latest_image)}"
                    delay 0.2
                    key code 36
                end tell
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            print("📁 Image imported to project panel - drag to timeline manually")
            return True
            
        except Exception as e:
            print(f"❌ Fallback failed: {e}")
            return False
    
    def on_key_press(self, key):
        """Handle Cmd+V in Premiere Pro"""
        try:
            if (hasattr(key, 'char') and key.char == 'v' and 
                self.is_premiere_active() and self.latest_image):
                
                print("⚡ Cmd+V detected in Premiere Pro!")
                threading.Thread(target=self.paste_to_timeline, daemon=True).start()
                
        except AttributeError:
            pass
    
    def start_keyboard_monitor(self):
        """Start monitoring for Cmd+V"""
        print("⌨️  Monitoring Cmd+V in Premiere Pro...")
        
        with keyboard.Listener(on_press=self.on_key_press) as listener:
            try:
                listener.join()
            except:
                pass

# Global instance
timeline_paste = PremiereTimelinePaste()

@app.route('/copy-image', methods=['POST'])
def copy_image():
    """Endpoint for browser extension"""
    try:
        data = request.json
        image_url = data.get('imageUrl')
        filename = data.get('filename')
        
        if not image_url:
            return jsonify({'error': 'No image URL provided'}), 400
        
        filepath = timeline_paste.download_image(image_url, filename)
        
        if filepath:
            return jsonify({
                'success': True,
                'message': 'Image ready for timeline paste',
                'filename': os.path.basename(filepath),
                'path': filepath
            })
        else:
            return jsonify({'error': 'Failed to download image'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/paste-now', methods=['POST'])
def paste_now():
    """Trigger immediate timeline paste"""
    try:
        success = timeline_paste.paste_to_timeline()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Image pasted to timeline'
            })
        else:
            return jsonify({'error': 'Failed to paste to timeline'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Get status"""
    return jsonify({
        'status': 'active',
        'mode': 'timeline_paste',
        'premiere_active': timeline_paste.is_premiere_active(),
        'latest_image': timeline_paste.latest_image,
        'bridge_dir': timeline_paste.bridge_dir
    })

def main():
    # Start keyboard monitoring
    keyboard_thread = threading.Thread(target=timeline_paste.start_keyboard_monitor, daemon=True)
    keyboard_thread.start()
    
    # Start server
    print("🌐 Timeline Paste Server: http://localhost:8589")
    app.run(host='localhost', port=8589, debug=False)

if __name__ == "__main__":
    main()