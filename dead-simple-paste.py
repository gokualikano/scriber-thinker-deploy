#!/usr/bin/env python3
"""
Dead Simple Premiere Pro Paste Bridge
Just monitors clipboard and auto-saves images to a bridge folder
"""

import time
import os
import subprocess
from datetime import datetime
from PIL import ImageGrab, Image
import hashlib

def main():
    bridge_dir = os.path.expanduser("~/Desktop/PremiereBridge")
    
    # Setup
    if not os.path.exists(bridge_dir):
        os.makedirs(bridge_dir)
        
    # Open bridge folder
    subprocess.run(['open', bridge_dir])
    
    print("🎬 Premiere Pro Paste Bridge - DEAD SIMPLE VERSION")
    print(f"📁 Auto-saving clipboard images to: {bridge_dir}")
    print("")
    print("🔄 Your new workflow:")
    print("   1. Copy any image (Cmd+C)")
    print("   2. Image auto-appears in Bridge folder")
    print("   3. Drag from Bridge folder → Premiere timeline")
    print("")
    print("💡 Pro tip: Keep Bridge folder open beside Premiere")
    print("⚠️  Press Ctrl+C to stop")
    print("")
    
    last_hash = None
    
    while True:
        try:
            # Get clipboard image
            image = ImageGrab.grabclipboard()
            
            if image and isinstance(image, Image.Image):
                # Generate hash to avoid duplicates
                current_hash = hashlib.md5(image.tobytes()).hexdigest()[:8]
                
                if current_hash != last_hash:
                    # Save with timestamp
                    timestamp = datetime.now().strftime("%H%M%S")
                    filename = f"paste_{timestamp}.png"
                    filepath = os.path.join(bridge_dir, filename)
                    
                    # Save image
                    image.save(filepath, "PNG", optimize=True)
                    
                    print(f"📸 → {filename} (ready to drag to Premiere)")
                    last_hash = current_hash
                    
            time.sleep(0.5)  # Check twice per second
            
        except KeyboardInterrupt:
            print("\n👋 Stopping paste bridge...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()