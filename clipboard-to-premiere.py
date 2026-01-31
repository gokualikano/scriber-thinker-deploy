#!/usr/bin/env python3
"""
Clipboard to Premiere Pro Bridge
Monitors clipboard for images and auto-saves them to a watched folder
"""

import time
import os
from datetime import datetime
from PIL import ImageGrab, Image
import hashlib

# Configuration
OUTPUT_DIR = os.path.expanduser("~/Desktop/ClipboardImages")
CHECK_INTERVAL = 0.5  # Check every 500ms
SUPPORTED_FORMATS = ['PNG', 'JPEG', 'TIFF', 'BMP']

def setup_output_directory():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Created: {OUTPUT_DIR}")

def get_image_hash(image):
    """Generate hash of image to detect duplicates"""
    return hashlib.md5(image.tobytes()).hexdigest()[:8]

def save_clipboard_image():
    """Save clipboard image if one exists"""
    try:
        # Get image from clipboard
        image = ImageGrab.grabclipboard()
        
        if image and isinstance(image, Image.Image):
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_hash = get_image_hash(image)
            filename = f"clipboard_{timestamp}_{img_hash}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            # Skip if file already exists (duplicate)
            if os.path.exists(filepath):
                return False
                
            # Save image
            image.save(filepath, "PNG")
            print(f"📸 Saved: {filename}")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    return False

def main():
    print("🎬 Clipboard to Premiere Pro Bridge")
    print(f"📁 Watching clipboard, saving to: {OUTPUT_DIR}")
    print("📋 Copy images from anywhere, they'll auto-save!")
    print("⚠️  Press Ctrl+C to stop")
    
    setup_output_directory()
    
    last_hash = None
    
    while True:
        try:
            # Check if there's an image in clipboard
            image = ImageGrab.grabclipboard()
            
            if image and isinstance(image, Image.Image):
                current_hash = get_image_hash(image)
                
                # Only save if it's a new image
                if current_hash != last_hash:
                    if save_clipboard_image():
                        last_hash = current_hash
                        
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n👋 Stopping clipboard monitor...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()