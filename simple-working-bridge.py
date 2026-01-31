#!/usr/bin/env python3
"""
Simple Working Premiere Bridge - No Permissions Needed
Extension downloads → Opens folder → Drag to Premiere
"""

import os
import subprocess
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

class SimpleBridge:
    def __init__(self):
        self.bridge_dir = os.path.expanduser("~/Desktop/PremiereBridge")
        self.setup_directories()
        
        print("🎬 Simple Working Premiere Bridge")
        print("📁 Images download to:", self.bridge_dir)
        print("🎯 Workflow: Extension → Auto-opens folder → Drag to Premiere")
        
    def setup_directories(self):
        os.makedirs(self.bridge_dir, exist_ok=True)
        
    def download_image(self, image_url, filename=None):
        """Download image and open folder"""
        try:
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = 'jpg'
                if '.' in image_url:
                    ext = image_url.split('.')[-1].split('?')[0].lower()
                    if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                        ext = 'jpg'
                filename = f"img_{timestamp}.{ext}"
            
            filepath = os.path.join(self.bridge_dir, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"📸 Downloaded: {filename}")
            
            # Auto-open folder for easy dragging
            subprocess.run(['open', '-R', filepath])
            
            return filepath
            
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None

# Global bridge
bridge = SimpleBridge()

@app.route('/copy-image', methods=['POST'])
def copy_image():
    """Handle extension requests"""
    try:
        data = request.json
        image_url = data.get('imageUrl')
        filename = data.get('filename')
        
        if not image_url:
            return jsonify({'error': 'No image URL'}), 400
        
        filepath = bridge.download_image(image_url, filename)
        
        if filepath:
            return jsonify({
                'success': True,
                'message': 'Image ready to drag',
                'filename': os.path.basename(filepath),
                'action': 'folder_opened'
            })
        else:
            return jsonify({'error': 'Download failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'active',
        'mode': 'simple_drag',
        'bridge_dir': bridge.bridge_dir
    })

def main():
    print("🌐 Simple Bridge Server: http://localhost:8589")
    print("✨ No complex permissions needed!")
    app.run(host='localhost', port=8589, debug=False)

if __name__ == "__main__":
    main()