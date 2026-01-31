"""
HTTP Server Addon for Creators Video Automation Desktop App
This module adds a local HTTP server to receive URLs from the Chrome extension
"""

import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from PyQt5.QtCore import QObject, pyqtSignal

class ExtensionServerHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Chrome extension communication"""
    
    def __init__(self, *args, url_callback=None, **kwargs):
        self.url_callback = url_callback
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """Handle POST requests from Chrome extension"""
        if self.path == '/paste-url':
            try:
                # Read the request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Parse JSON data
                data = json.loads(post_data.decode('utf-8'))
                url = data.get('url', '')
                
                print(f"📹 Received URL from Chrome extension: {url}")
                
                # Send URL to main application
                if self.url_callback:
                    self.url_callback(url)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    'status': 'success',
                    'message': 'URL received and added to queue'
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                print(f"❌ Error processing URL from extension: {e}")
                self.send_error(400, str(e))
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_GET(self):
        """Handle GET requests (ping for connection test)"""
        if self.path == '/ping':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'status': 'online',
                'message': 'Desktop app is running and ready to receive URLs'
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass


class ExtensionServer(QObject):
    """Qt-compatible HTTP server for Chrome extension communication"""
    
    url_received = pyqtSignal(str)  # Signal emitted when URL is received
    server_started = pyqtSignal(bool, str)  # Signal for server status
    
    def __init__(self, port=7898):
        super().__init__()
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
    
    def start_server(self):
        """Start the HTTP server in a background thread"""
        if self.running:
            print("⚠️ Server already running")
            return
        
        try:
            # Create HTTP server with custom handler
            def handler_factory(*args, **kwargs):
                return ExtensionServerHandler(*args, url_callback=self.handle_url, **kwargs)
            
            self.server = HTTPServer(('localhost', self.port), handler_factory)
            
            # Start server in background thread
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            self.running = True
            print(f"🌐 Chrome extension server started on http://localhost:{self.port}")
            self.server_started.emit(True, f"Server running on port {self.port}")
            
        except Exception as e:
            error_msg = f"Failed to start server on port {self.port}: {e}"
            print(f"❌ {error_msg}")
            self.server_started.emit(False, error_msg)
    
    def _run_server(self):
        """Run the server (called in background thread)"""
        try:
            self.server.serve_forever()
        except Exception as e:
            print(f"❌ Server error: {e}")
            self.running = False
    
    def stop_server(self):
        """Stop the HTTP server"""
        if self.server and self.running:
            print("🛑 Stopping Chrome extension server...")
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=2)
    
    def handle_url(self, url):
        """Handle incoming URL from Chrome extension"""
        print(f"📹 Processing URL from extension: {url}")
        # Emit signal to main thread (Qt thread-safe)
        self.url_received.emit(url)
    
    def is_running(self):
        """Check if server is running"""
        return self.running


# Integration helper function
def add_extension_support(main_app_instance, url_text_widget):
    """
    Add Chrome extension support to existing video app
    
    Args:
        main_app_instance: The main QMainWindow instance
        url_text_widget: The QTextEdit widget where URLs should be added
    """
    
    def on_url_received(url):
        """Callback when URL is received from extension"""
        try:
            # Get current text
            current_text = url_text_widget.toPlainText().strip()
            
            # Add new URL
            if current_text:
                new_text = current_text + '\n' + url
            else:
                new_text = url
            
            # Update the text widget
            url_text_widget.setPlainText(new_text)
            
            # Move cursor to end
            cursor = url_text_widget.textCursor()
            cursor.movePosition(cursor.End)
            url_text_widget.setTextCursor(cursor)
            
            print(f"✅ Added URL to input field: {url}")
            
            # Optional: Show visual feedback
            url_text_widget.setStyleSheet("""
                QTextEdit {
                    border: 2px solid #00FF00;
                    border-radius: 8px;
                    padding: 10px;
                    background: #0a0a0a;
                    color: #FFFF00;
                }
            """)
            
            # Reset style after 1 second
            def reset_style():
                url_text_widget.setStyleSheet("""
                    QTextEdit {
                        border: 2px solid #FFFF00;
                        border-radius: 8px;
                        padding: 10px;
                        background: #0a0a0a;
                        color: #FFFF00;
                    }
                """)
            
            # Use Qt timer for thread-safe style reset
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, reset_style)
            
        except Exception as e:
            print(f"❌ Error adding URL to input field: {e}")
    
    # Create and start extension server
    extension_server = ExtensionServer()
    extension_server.url_received.connect(on_url_received)
    extension_server.start_server()
    
    # Store reference in main app to prevent garbage collection
    main_app_instance.extension_server = extension_server
    
    # Handle cleanup on app exit
    def cleanup_server():
        if hasattr(main_app_instance, 'extension_server'):
            main_app_instance.extension_server.stop_server()
    
    main_app_instance.closeEvent = lambda event: (cleanup_server(), event.accept())
    
    return extension_server


if __name__ == "__main__":
    # Test the server standalone
    print("🧪 Testing Chrome Extension Server...")
    
    def test_callback(url):
        print(f"TEST: Received URL: {url}")
    
    server = ExtensionServer()
    server.url_received.connect(test_callback)
    server.start_server()
    
    try:
        input("Server running. Press Enter to stop...")
    except KeyboardInterrupt:
        pass
    finally:
        server.stop_server()
        print("✅ Test completed")