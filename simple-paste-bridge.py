#!/usr/bin/env python3
"""
Simple Paste Bridge for Premiere Pro
Auto-saves clipboard images to a folder that Premiere can access
"""

import time
import os
import subprocess
from datetime import datetime
from PIL import ImageGrab, Image
import hashlib

# Configuration
BRIDGE_DIR = os.path.expanduser("~/Desktop/PremiereBridge")
CHECK_INTERVAL = 0.3
LAST_IMAGE_HASH = None

def setup_bridge_directory():
    """Create bridge directory"""
    if not os.path.exists(BRIDGE_DIR):
        os.makedirs(BRIDGE_DIR)
        print(f"📁 Created bridge folder: {BRIDGE_DIR}")

def get_image_hash(image):
    """Get hash of image"""
    return hashlib.md5(image.tobytes()).hexdigest()[:8]

def save_clipboard_image():
    """Save clipboard image to bridge folder"""
    global LAST_IMAGE_HASH
    
    try:
        image = ImageGrab.grabclipboard()
        
        if image and isinstance(image, Image.Image):
            current_hash = get_image_hash(image)
            
            # Only save new images
            if current_hash != LAST_IMAGE_HASH:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"clipboard_{timestamp}.png"
                filepath = os.path.join(BRIDGE_DIR, filename)
                
                # Save image
                image.save(filepath, "PNG", optimize=True)
                print(f"📸 Ready for Premiere: {filename}")
                
                LAST_IMAGE_HASH = current_hash
                return filepath
                
    except Exception as e:
        print(f"❌ Error: {e}")
        
    return None

def main():
    print("🎬 Premiere Pro Paste Bridge")
    print(f"📁 Auto-saving clipboard images to: {BRIDGE_DIR}")
    print("🔄 Workflow:")
    print("   1. Copy image from anywhere (Cmd+C)")
    print("   2. Go to Premiere Pro")
    print("   3. Drag from Bridge folder to timeline")
    print("   4. Or use File → Import to get the latest image")
    print("\n⚠️  Press Ctrl+C to stop")
    
    setup_bridge_directory()
    
    # Open bridge folder once at start
    subprocess.run(['open', BRIDGE_DIR])
    
    while True:
        try:
            save_clipboard_image()
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n👋 Stopping paste bridge...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()