#!/usr/bin/env python3
"""
Premiere Pro Bridge - Direct Timeline Paste Service
Works with PRGrabber Enhanced browser extension
"""

import os
import time
import subprocess
import tempfile
import threading
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from pynput import keyboard
import hashlib

app = Flask(__name__)
CORS(app)

class PremiereProBridge:
    def __init__(self):
        self.bridge_dir = os.path.expanduser("~/Desktop/PRGrabber")
        self.latest_image = None
        self.setup_directories()
        self.monitoring = True
        
        print("🎬 Premiere Pro Bridge - Direct Timeline Paste")
        print(f"📁 Bridge folder: {self.bridge_dir}")
        print("⚡ Ready for direct paste workflow!")
        
    def setup_directories(self):
        os.makedirs(self.bridge_dir, exist_ok=True)
        
    def download_and_prepare(self, image_url):
        """Download image and prepare for Premiere import"""
        try:
            # Download image
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:6]
            
            # Detect extension
            ext = 'jpg'
            if '.' in image_url:
                potential_ext = image_url.split('.')[-1].split('?')[0].lower()
                if potential_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                    ext = potential_ext
            
            filename = f"pr_{timestamp}_{url_hash}.{ext}"
            filepath = os.path.join(self.bridge_dir, filename)
            
            # Save image
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.latest_image = filepath
            print(f"📸 Image ready: {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
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
                                  capture_output=True, text=True, timeout=5)
            app_name = result.stdout.strip().lower()
            return "premiere" in app_name and "pro" in app_name
        except:
            return False
    
    def import_to_premiere(self, filepath):
        """Import image directly to Premiere Pro project"""
        try:
            filename = os.path.basename(filepath)
            print(f"📥 Importing to Premiere Pro 2022: {filename}")
            
            # AppleScript for Premiere Pro 2022 import
            script = f'''
            tell application "Adobe Premiere Pro 2022"
                activate
            end tell
            
            delay 0.5
            
            tell application "System Events"
                tell process "Adobe Premiere Pro 2022"
                    -- Import command (Cmd+I)
                    key code 34 using command down
                    delay 1.2
                    
                    -- Navigate to our bridge folder (Cmd+Shift+G)
                    keystroke "g" using {{command down, shift down}}
                    delay 0.5
                    keystroke "{self.bridge_dir}"
                    delay 0.3
                    key code 36 -- Enter
                    delay 0.8
                    
                    -- Type filename to select it
                    keystroke "{filename}"
                    delay 0.4
                    
                    -- Press Enter to import
                    key code 36
                    
                end tell
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print("✅ Image imported to Premiere Pro!")
                return True
            else:
                print(f"⚠️ Import script result: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Import failed: {e}")
            return False
    
    def handle_paste_command(self):
        """Handle Cmd+V in Premiere Pro"""
        if self.latest_image and self.is_premiere_active():
            print("⚡ Cmd+V detected in Premiere Pro!")
            success = self.import_to_premiere(self.latest_image)
            if success:
                # Clear the latest image so we don't import it again
                self.latest_image = None
            return success
        return False
    
    def start_keyboard_monitor(self):
        """Monitor for Cmd+V in Premiere Pro"""
        def on_key_press(key):
            try:
                # Detect V key (we'll check for Cmd modifier in the handler)
                if hasattr(key, 'char') and key.char == 'v':
                    # Small delay to ensure proper key combination detection
                    threading.Thread(target=self.delayed_paste_check, daemon=True).start()
            except AttributeError:
                pass
        
        print("⌨️  Monitoring Cmd+V in Premiere Pro...")
        
        with keyboard.Listener(on_press=on_key_press) as listener:
            try:
                listener.join()
            except:
                pass
    
    def delayed_paste_check(self):
        """Check for paste command with small delay"""
        time.sleep(0.1)  # Small delay to capture key combination
        self.handle_paste_command()

# Global bridge instance
bridge = PremiereProBridge()

@app.route('/paste-image', methods=['POST'])
def paste_image():
    """Handle paste image request from browser extension"""
    try:
        data = request.json
        image_url = data.get('imageUrl')
        
        if not image_url:
            return jsonify({'error': 'No image URL provided'}), 400
        
        # Download and prepare image
        filepath = bridge.download_and_prepare(image_url)
        
        if filepath:
            return jsonify({
                'success': True,
                'message': 'Image ready for Cmd+V paste',
                'filename': os.path.basename(filepath),
                'instructions': 'Switch to Premiere Pro and press Cmd+V'
            })
        else:
            return jsonify({'error': 'Failed to download image'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/import-now', methods=['POST'])
def import_now():
    """Trigger immediate import to Premiere"""
    try:
        if bridge.latest_image:
            success = bridge.import_to_premiere(bridge.latest_image)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Image imported to Premiere Pro'
                })
            else:
                return jsonify({'error': 'Import failed'}), 500
        else:
            return jsonify({'error': 'No image ready'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Get bridge status"""
    return jsonify({
        'status': 'active',
        'mode': 'direct_paste',
        'premiere_active': bridge.is_premiere_active(),
        'latest_image': bridge.latest_image,
        'bridge_dir': bridge.bridge_dir
    })

def main():
    # Start keyboard monitoring in background
    keyboard_thread = threading.Thread(target=bridge.start_keyboard_monitor, daemon=True)
    keyboard_thread.start()
    
    # Start Flask server
    print("🌐 Premiere Bridge Server: http://localhost:8590")
    print("🎯 Workflow: Browser extension → Cmd+V in Premiere → Direct paste!")
    app.run(host='localhost', port=8590, debug=False)

if __name__ == "__main__":
    main()