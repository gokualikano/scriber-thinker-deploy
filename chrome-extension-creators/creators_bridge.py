#!/usr/bin/env python3
"""
Creators Video Automation Bridge Service
Receives URLs from Chrome extension and sends them to the .dmg desktop app
"""

import json
import subprocess
import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import tempfile
from pathlib import Path

class CreatorsBridgeHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/paste-url':
            try:
                # Read request data
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                url = data.get('url', '')
                
                print(f"📹 Received URL from Chrome: {url}")
                
                # Send URL to desktop app via multiple methods
                success = self.send_to_desktop_app(url)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                if success:
                    response = {'status': 'success', 'message': 'URL sent to Creators app!'}
                    print(f"✅ URL sent to desktop app: {url}")
                else:
                    response = {'status': 'partial', 'message': 'URL copied to clipboard as fallback'}
                    print(f"⚠️ Used clipboard fallback: {url}")
                
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                print(f"❌ Error: {e}")
                self.send_error(400, str(e))
    
    def do_GET(self):
        if self.path == '/ping':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Check if desktop app is running
            app_running = self.check_app_running()
            
            response = {
                'status': 'online', 
                'message': 'Bridge service running',
                'desktop_app_detected': app_running
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def check_app_running(self):
        """Check if Creators Video Automation app is running"""
        try:
            result = subprocess.run([
                'osascript', '-e', 
                'tell application "System Events" to return (name of processes) contains "Creators Video Automation"'
            ], capture_output=True, text=True, timeout=5)
            
            return 'true' in result.stdout.lower()
        except:
            return False
    
    def send_to_desktop_app(self, url):
        """Send URL to desktop app using multiple methods"""
        try:
            # Method 1: AppleScript to paste into active app
            success1 = self.method_applescript_paste(url)
            if success1:
                return True
            
            # Method 2: File-based communication
            success2 = self.method_file_communication(url)
            if success2:
                return True
                
            # Method 3: Clipboard fallback
            self.method_clipboard_fallback(url)
            return False
            
        except Exception as e:
            print(f"❌ All methods failed: {e}")
            self.method_clipboard_fallback(url)
            return False
    
    def method_applescript_paste(self, url):
        """Method 1: Use AppleScript to paste URL into focused app"""
        try:
            # Copy URL to clipboard first
            subprocess.run(['pbcopy'], input=url.encode('utf-8'))
            
            # AppleScript to paste into active app
            applescript = f'''
                tell application "System Events"
                    # Check if Creators app is active
                    set frontApp to name of first application process whose frontmost is true
                    if frontApp contains "Creators" then
                        # Try to find text field and paste
                        keystroke "v" using command down
                        return true
                    end if
                end tell
                return false
            '''
            
            result = subprocess.run([
                'osascript', '-e', applescript
            ], capture_output=True, text=True, timeout=10)
            
            if 'true' in result.stdout:
                print("✅ AppleScript paste successful")
                return True
                
        except Exception as e:
            print(f"⚠️ AppleScript method failed: {e}")
        
        return False
    
    def method_file_communication(self, url):
        """Method 2: Write URL to file that app might monitor"""
        try:
            # Create URLs file in app's expected locations
            possible_paths = [
                Path.home() / "Desktop" / "creators_urls.txt",
                Path("/tmp/creators_urls.txt"),
                Path.home() / "Documents" / "creators_urls.txt"
            ]
            
            for path in possible_paths:
                try:
                    # Append URL with timestamp
                    with open(path, 'a') as f:
                        f.write(f"{url}\n")
                    print(f"✅ URL written to {path}")
                    break
                except:
                    continue
            
            return True
            
        except Exception as e:
            print(f"⚠️ File method failed: {e}")
            return False
    
    def method_clipboard_fallback(self, url):
        """Method 3: Copy to clipboard as fallback"""
        try:
            subprocess.run(['pbcopy'], input=url.encode('utf-8'))
            print(f"📋 URL copied to clipboard as fallback")
        except Exception as e:
            print(f"❌ Clipboard fallback failed: {e}")
    
    def log_message(self, format, *args):
        # Reduce log noise
        pass

def check_app_running_standalone():
    """Check if Creators Video Automation app is running"""
    try:
        result = subprocess.run([
            'osascript', '-e', 
            'tell application "System Events" to return (name of processes) contains "Creators Video Automation"'
        ], capture_output=True, text=True, timeout=5)
        
        return 'true' in result.stdout.lower()
    except:
        return False

def main():
    print("🌉 Creators Video Automation - Bridge Service")
    print("🔗 Connects Chrome Extension → .dmg Desktop App")
    print("=" * 50)
    
    # Check if desktop app is running
    app_running = check_app_running_standalone()
    
    if app_running:
        print("✅ Creators Video Automation app detected!")
    else:
        print("⚠️ Creators Video Automation app not detected")
        print("💡 Start your .dmg app first, then this bridge will work better")
    
    print()
    server = HTTPServer(('localhost', 7898), CreatorsBridgeHandler)
    
    print("🌐 Bridge server starting on http://localhost:7898")
    print("✅ Chrome extension ready!")
    print()
    print("💡 Usage:")
    print("  1. Make sure Creators Video Automation.app is running")
    print("  2. Right-click YouTube video → 'Send to Creators'")
    print("  3. URL will be sent to your desktop app!")
    print()
    print("🔧 Communication methods:")
    print("  • AppleScript automation (best)")
    print("  • File-based communication")  
    print("  • Clipboard fallback")
    print()
    print("⚡ Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Bridge service stopped")
        server.server_close()

if __name__ == "__main__":
    main()