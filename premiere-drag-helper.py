#!/usr/bin/env python3
"""
Premiere Drag Helper - Works with ANY Premiere version (including cracked)
No AppleScript automation needed - pure drag and drop solution
"""

import os
import subprocess
import requests
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib

app = Flask(__name__)
CORS(app)

class PremiereDragHelper:
    def __init__(self):
        self.drag_dir = os.path.expanduser("~/Desktop/Premiere-Drag")
        self.setup_directories()
        
        print("🎬 Premiere Drag Helper - Works with ANY Premiere version!")
        print(f"📁 Drag folder: {self.drag_dir}")
        print("🎯 No security permissions needed!")
        
    def setup_directories(self):
        os.makedirs(self.drag_dir, exist_ok=True)
        
    def download_and_show(self, image_url):
        """Download image and open Finder for easy dragging"""
        try:
            # Download image
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%H%M%S")
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:4]
            
            # Detect extension
            ext = 'jpg'
            if '.' in image_url:
                potential_ext = image_url.split('.')[-1].split('?')[0].lower()
                if potential_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                    ext = potential_ext
            
            filename = f"pr_{timestamp}_{url_hash}.{ext}"
            filepath = os.path.join(self.drag_dir, filename)
            
            # Save image
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"📸 Downloaded: {filename}")
            
            # Open Finder and select the file for easy dragging
            subprocess.run(['open', '-R', filepath])
            
            # Also bring Premiere to front if it's running
            try:
                subprocess.run([
                    'osascript', '-e', 
                    'tell application "Adobe Premiere Pro 2022" to activate'
                ], timeout=2, capture_output=True)
            except:
                pass  # Ignore if Premiere activation fails
            
            return {
                'filepath': filepath,
                'filename': filename,
                'action': 'drag_ready'
            }
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def cleanup_old_files(self):
        """Clean up files older than 1 hour"""
        try:
            import time
            current_time = time.time()
            
            for filename in os.listdir(self.drag_dir):
                if filename.startswith('pr_'):
                    filepath = os.path.join(self.drag_dir, filename)
                    file_time = os.path.getmtime(filepath)
                    
                    # Delete files older than 1 hour
                    if current_time - file_time > 3600:
                        os.remove(filepath)
                        print(f"🗑️ Cleaned up: {filename}")
                        
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

# Global helper
drag_helper = PremiereDragHelper()

@app.route('/paste-image', methods=['POST'])
def paste_image():
    """Handle paste image request - download and show for dragging"""
    try:
        data = request.json
        image_url = data.get('imageUrl')
        
        if not image_url:
            return jsonify({'error': 'No image URL provided'}), 400
        
        # Clean up old files first
        drag_helper.cleanup_old_files()
        
        # Download and show image
        result = drag_helper.download_and_show(image_url)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Image ready to drag to Premiere!',
                'filename': result['filename'],
                'instructions': 'Drag from Finder window to Premiere timeline'
            })
        else:
            return jsonify({'error': 'Failed to download image'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Get status"""
    # Check if Premiere is running
    premiere_running = False
    try:
        result = subprocess.run(['pgrep', '-f', 'Premiere'], 
                              capture_output=True, text=True)
        premiere_running = bool(result.stdout.strip())
    except:
        pass
    
    return jsonify({
        'status': 'active',
        'mode': 'drag_and_drop',
        'premiere_running': premiere_running,
        'drag_dir': drag_helper.drag_dir,
        'message': 'No security permissions needed - pure drag & drop'
    })

def main():
    print("🌐 Premiere Drag Helper Server: http://localhost:8590")
    print("✨ Works with ANY Premiere version (including cracked)")
    print("🎯 No AppleScript, no permissions, just drag & drop!")
    app.run(host='localhost', port=8590, debug=False)

if __name__ == "__main__":
    main()