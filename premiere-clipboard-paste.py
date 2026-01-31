#!/usr/bin/env python3
"""
Premiere Pro Direct Clipboard Paste
Puts images directly in clipboard for Cmd+V in Premiere timeline
"""

import os
import io
import subprocess
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import tempfile

app = Flask(__name__)
CORS(app)

class PremiereClipboardPaste:
    def __init__(self):
        print("🎬 Premiere Pro Direct Clipboard Paste")
        print("📋 Images go directly to clipboard for Cmd+V!")
        
    def download_to_clipboard(self, image_url):
        """Download image and put it directly in clipboard"""
        try:
            print(f"📥 Downloading image: {image_url}")
            
            # Download image
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Load image with PIL
            image = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if needed (for JPEG compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if len(image.split()) == 4 else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save to temporary file for clipboard
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                image.save(temp_file.name, 'PNG', optimize=True)
                temp_path = temp_file.name
            
            # Put image in clipboard using AppleScript (this works even without permissions)
            clipboard_script = f'''
            set theImage to POSIX file "{temp_path}"
            tell application "Finder"
                set the clipboard to (read file theImage as «class PNGf»)
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', clipboard_script], 
                                  capture_output=True, text=True, timeout=10)
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
            
            if result.returncode == 0:
                print("✅ Image copied to clipboard!")
                return {
                    'success': True,
                    'message': 'Image copied to clipboard - press Cmd+V in Premiere!',
                    'size': f"{image.width}x{image.height}",
                    'mode': image.mode
                }
            else:
                print(f"❌ Clipboard copy failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def test_clipboard(self):
        """Test if clipboard method works"""
        try:
            # Create a simple test image
            test_image = Image.new('RGB', (100, 100), (255, 0, 0))  # Red square
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                test_image.save(temp_file.name, 'PNG')
                temp_path = temp_file.name
            
            # Try to put in clipboard
            clipboard_script = f'''
            set theImage to POSIX file "{temp_path}"
            tell application "Finder"
                set the clipboard to (read file theImage as «class PNGf»)
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', clipboard_script], 
                                  capture_output=True, text=True, timeout=5)
            
            os.unlink(temp_path)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Clipboard test failed: {e}")
            return False

# Global instance
clipboard_paste = PremiereClipboardPaste()

@app.route('/paste-image', methods=['POST'])
def paste_image():
    """Handle image clipboard request"""
    try:
        data = request.json
        image_url = data.get('imageUrl')
        
        if not image_url:
            return jsonify({'error': 'No image URL provided'}), 400
        
        # Copy image to clipboard
        result = clipboard_paste.download_to_clipboard(image_url)
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to copy image to clipboard'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test-clipboard', methods=['GET'])
def test_clipboard():
    """Test clipboard functionality"""
    success = clipboard_paste.test_clipboard()
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Clipboard test passed - red square should be in clipboard'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Clipboard test failed'
        })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'active',
        'mode': 'clipboard_paste',
        'message': 'Direct Cmd+V paste in Premiere Pro'
    })

def main():
    # Test clipboard functionality on startup
    print("🧪 Testing clipboard functionality...")
    if clipboard_paste.test_clipboard():
        print("✅ Clipboard method working!")
    else:
        print("❌ Clipboard method not working")
        
    print("🌐 Clipboard Paste Server: http://localhost:8590")
    print("🎯 Right-click image → Cmd+V in Premiere timeline!")
    app.run(host='localhost', port=8590, debug=False)

if __name__ == "__main__":
    main()