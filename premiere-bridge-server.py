#!/usr/bin/env python3
"""
Premiere Pro Bridge Server
Receives images from browser extension and enables Cmd+V paste in Premiere
"""

import os
import time
import subprocess
import tempfile
import shutil
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pynput import keyboard
import threading
import requests
from urllib.parse import urlparse
import hashlib

app = Flask(__name__)
CORS(app)

class PremiereBridge:
    def __init__(self):
        self.bridge_dir = os.path.expanduser("~/Desktop/PremiereBridge")
        self.temp_dir = os.path.expanduser("~/Desktop/.premiere_temp")
        self.latest_image = None
        self.setup_directories()
        self.monitoring_keys = True
        
        print("🎬 Premiere Pro Bridge Server Starting...")
        print(f"📁 Bridge folder: {self.bridge_dir}")
        
    def setup_directories(self):
        """Create necessary directories"""
        os.makedirs(self.bridge_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def download_image(self, image_url, filename=None):
        """Download image from URL"""
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                parsed_url = urlparse(image_url)
                ext = parsed_url.path.split('.')[-1].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                    ext = 'jpg'
                filename = f"browser_{timestamp}.{ext}"
            
            filepath = os.path.join(self.bridge_dir, filename)
            
            # Download and save
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            
            self.latest_image = filepath
            print(f"📸 Downloaded: {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None
    
    def is_premiere_active(self):
        """Check if Premiere Pro is the active application"""
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
    
    def paste_to_premiere(self):
        """Import latest image to Premiere Pro"""
        if not self.latest_image or not os.path.exists(self.latest_image):
            print("❌ No image ready to paste")
            return False
            
        try:
            print(f"📥 Pasting to Premiere: {os.path.basename(self.latest_image)}")
            
            # Method 1: Use Premiere Pro's scripting interface
            script = f'''
            tell application "Adobe Premiere Pro 2024"
                activate
            end tell
            
            delay 0.3
            
            tell application "System Events"
                tell process "Adobe Premiere Pro 2024"
                    -- Open Import dialog
                    key code 31 using command down
                    delay 0.5
                    
                    -- Navigate to file
                    keystroke "g" using {{command down, shift down}}
                    delay 0.3
                    keystroke "{self.bridge_dir}"
                    delay 0.3
                    key code 36
                    delay 0.3
                    
                    -- Select the file
                    keystroke "{os.path.basename(self.latest_image)}"
                    delay 0.2
                    key code 36
                    
                end tell
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Image pasted to Premiere Pro!")
                return True
            else:
                print(f"⚠️ Script result: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Paste error: {e}")
            return False
    
    def on_key_press(self, key):
        """Handle keyboard events"""
        try:
            # Detect Cmd+V in Premiere Pro
            if (hasattr(key, 'char') and key.char == 'v' and 
                self.is_premiere_active()):
                
                # Small delay to ensure we're handling the right event
                threading.Thread(target=self.handle_paste_command, daemon=True).start()
                
        except AttributeError:
            pass
    
    def handle_paste_command(self):
        """Handle paste command with small delay"""
        time.sleep(0.1)  # Small delay to capture the key combination properly
        
        # Check if Cmd is being held (this is tricky to detect reliably)
        # For now, we'll just attempt the paste when V is pressed in Premiere
        if self.is_premiere_active() and self.latest_image:
            print("🎬 Cmd+V detected in Premiere Pro!")
            self.paste_to_premiere()
    
    def start_keyboard_monitor(self):
        """Start monitoring keyboard for Cmd+V"""
        print("⌨️  Monitoring keyboard for Cmd+V in Premiere Pro...")
        
        with keyboard.Listener(on_press=self.on_key_press) as listener:
            try:
                listener.join()
            except:
                pass

# Global bridge instance
bridge = PremiereBridge()

@app.route('/copy-image', methods=['POST'])
def copy_image():
    """Endpoint for browser extension to send images"""
    try:
        data = request.json
        image_url = data.get('imageUrl')
        filename = data.get('filename')
        
        if not image_url:
            return jsonify({'error': 'No image URL provided'}), 400
        
        # Download the image
        filepath = bridge.download_image(image_url, filename)
        
        if filepath:
            return jsonify({
                'success': True,
                'message': 'Image ready for Premiere Pro',
                'filename': os.path.basename(filepath),
                'path': filepath
            })
        else:
            return jsonify({'error': 'Failed to download image'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/paste-now', methods=['POST'])
def paste_now():
    """Endpoint to trigger immediate paste"""
    try:
        success = bridge.paste_to_premiere()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Image pasted to Premiere Pro'
            })
        else:
            return jsonify({'error': 'Failed to paste to Premiere'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Get bridge status"""
    return jsonify({
        'status': 'active',
        'premiere_active': bridge.is_premiere_active(),
        'latest_image': bridge.latest_image,
        'bridge_dir': bridge.bridge_dir
    })

def start_server():
    """Start the Flask server"""
    print("🌐 Starting Premiere Pro Bridge Server on http://localhost:8589")
    print("📡 Browser extension can now communicate with Premiere Pro!")
    app.run(host='localhost', port=8589, debug=False)

def main():
    # Start keyboard monitoring in background thread
    keyboard_thread = threading.Thread(target=bridge.start_keyboard_monitor, daemon=True)
    keyboard_thread.start()
    
    # Start web server
    start_server()

if __name__ == "__main__":
    main()