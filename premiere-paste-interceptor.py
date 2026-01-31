#!/usr/bin/env python3
"""
Premiere Pro Clipboard Paste Interceptor
Makes Cmd+V work with clipboard images in Premiere Pro
"""

import time
import os
import subprocess
from datetime import datetime
from PIL import ImageGrab, Image
import hashlib
from pynput import keyboard
import threading

# Configuration
TEMP_DIR = os.path.expanduser("~/Desktop/PremierePasteTemp")
CHECK_INTERVAL = 0.1  # Fast response
LAST_IMAGE_HASH = None

class PremierePasteHandler:
    def __init__(self):
        self.setup_temp_directory()
        self.monitoring = True
        
    def setup_temp_directory(self):
        """Create temp directory if it doesn't exist"""
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)
            print(f"📁 Created temp dir: {TEMP_DIR}")

    def get_image_hash(self, image):
        """Generate hash of image to detect duplicates"""
        return hashlib.md5(image.tobytes()).hexdigest()[:8]
    
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
            return "Adobe Premiere Pro" in result.stdout.strip()
        except:
            return False
    
    def save_clipboard_image(self):
        """Save clipboard image and return file path"""
        try:
            image = ImageGrab.grabclipboard()
            
            if image and isinstance(image, Image.Image):
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                img_hash = self.get_image_hash(image)
                filename = f"paste_{timestamp}_{img_hash}.png"
                filepath = os.path.join(TEMP_DIR, filename)
                
                # Save image
                image.save(filepath, "PNG")
                print(f"📸 Saved for paste: {filename}")
                return filepath
                
        except Exception as e:
            print(f"❌ Save error: {e}")
            
        return None
    
    def import_to_premiere(self, filepath):
        """Import file to Premiere Pro project"""
        try:
            # AppleScript to import file to Premiere
            script = f'''
            tell application "Adobe Premiere Pro 2024"
                activate
                delay 0.5
                -- Import file to project
                import file "{filepath}"
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script], 
                          capture_output=True, text=True)
            print(f"📥 Imported to Premiere: {os.path.basename(filepath)}")
            
        except Exception as e:
            print(f"❌ Import error: {e}")
            
    def drag_to_timeline(self, filepath):
        """Simulate drag to timeline (fallback)"""
        try:
            # Open the temp folder so user can drag manually if needed
            subprocess.run(['open', TEMP_DIR])
            print(f"📂 Opened temp folder - drag {os.path.basename(filepath)} to timeline")
        except Exception as e:
            print(f"❌ Folder open error: {e}")

    def handle_paste_key(self):
        """Handle Cmd+V when Premiere is active"""
        global LAST_IMAGE_HASH
        
        if not self.is_premiere_active():
            return
            
        # Get clipboard image
        try:
            image = ImageGrab.grabclipboard()
            
            if image and isinstance(image, Image.Image):
                current_hash = self.get_image_hash(image)
                
                # Only process new images
                if current_hash != LAST_IMAGE_HASH:
                    print("🎬 Premiere paste detected!")
                    
                    # Save image
                    filepath = self.save_clipboard_image()
                    if filepath:
                        # Try to import directly
                        self.import_to_premiere(filepath)
                        
                        # Fallback: open folder for manual drag
                        time.sleep(1)
                        self.drag_to_timeline(filepath)
                        
                    LAST_IMAGE_HASH = current_hash
                    
        except Exception as e:
            print(f"❌ Paste handler error: {e}")
    
    def on_key_press(self, key):
        """Key press event handler"""
        try:
            # Detect Cmd+V (or Ctrl+V)
            if hasattr(key, 'vk') and key.vk == 86:  # V key
                # Check for modifiers in separate thread to avoid blocking
                threading.Thread(target=self.handle_paste_key, daemon=True).start()
                
        except AttributeError:
            pass
    
    def start_monitoring(self):
        """Start monitoring keyboard events"""
        print("🎬 Premiere Paste Interceptor Active")
        print("📋 Copy images, then Cmd+V in Premiere Pro!")
        print("⚠️  Press Ctrl+C to stop")
        
        # Start keyboard listener
        with keyboard.Listener(on_press=self.on_key_press) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\n👋 Stopping interceptor...")
                self.monitoring = False

def main():
    handler = PremierePasteHandler()
    handler.start_monitoring()

if __name__ == "__main__":
    main()