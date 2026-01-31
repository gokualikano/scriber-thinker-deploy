#!/usr/bin/env python3
"""
Simple HTTP Server for Chrome Extension
Receives URLs and copies them to clipboard (no GUI required)
"""

import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

class SimpleURLHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/paste-url':
            try:
                # Read request data
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                url = data.get('url', '')
                
                print(f"📹 Received URL: {url}")
                
                # Copy to clipboard
                self.copy_to_clipboard(url)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'status': 'success', 'message': 'URL copied to clipboard!'}
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
            
            response = {'status': 'online', 'message': 'Server running - URLs will be copied to clipboard'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            # macOS clipboard
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
            print(f"✅ URL copied to clipboard: {text}")
        except Exception as e:
            print(f"❌ Failed to copy to clipboard: {e}")
    
    def log_message(self, format, *args):
        # Reduce log noise
        pass

def main():
    print("📹 Simple Chrome Extension Server")
    print("🔌 URLs will be copied to clipboard")
    print("=" * 40)
    
    server = HTTPServer(('localhost', 7898), SimpleURLHandler)
    
    print("🌐 Server starting on http://localhost:7898")
    print("✅ Chrome extension ready!")
    print("\n💡 Usage:")
    print("  1. Right-click YouTube video → 'Send to Creators'")
    print("  2. URL is copied to clipboard automatically")
    print("  3. Paste (Cmd+V) into your desktop app")
    print("\n⚠️  Keep this running to receive URLs")
    print("⚡ Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        server.server_close()

if __name__ == "__main__":
    main()