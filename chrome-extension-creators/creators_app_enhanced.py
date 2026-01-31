#!/usr/bin/env python3
"""
Enhanced Creators Video Automation with Chrome Extension Support
Quick launcher that adds HTTP server to your existing desktop app
"""

import sys
import os
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
desktop_app_dir = current_dir.parent / "VideoAutomation" / "VideoAutomation"
sys.path.insert(0, str(desktop_app_dir))
sys.path.insert(0, str(current_dir))

try:
    # Import existing desktop app
    from video_app_v2 import CreatorsApp
    from PyQt5.QtWidgets import QApplication
    from desktop_server_addon import ExtensionServer
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("📍 Make sure your desktop app files are in the correct location")
    sys.exit(1)

class EnhancedCreatorsApp(CreatorsApp):
    """Your existing app + Chrome Extension HTTP server"""
    
    def __init__(self):
        super().__init__()
        self.extension_server = None
        self.setup_extension_server()
    
    def setup_extension_server(self):
        """Add HTTP server for Chrome extension communication"""
        try:
            # Create extension server
            self.extension_server = ExtensionServer(port=7898)
            
            # Connect URL received signal to our handler
            self.extension_server.url_received.connect(self.on_url_from_extension)
            
            # Start the server
            self.extension_server.start_server()
            
            print("🌐 Chrome Extension server started on http://localhost:7898")
            print("✅ Desktop app ready to receive URLs from Chrome extension!")
            
        except Exception as e:
            print(f"⚠️ Failed to start extension server: {e}")
            print("📝 App will work without extension support")
    
    def on_url_from_extension(self, url):
        """Handle URL received from Chrome extension"""
        try:
            print(f"📹 Received URL from Chrome: {url}")
            
            # Get current URLs in text field
            current_text = self.url_text.toPlainText().strip()
            
            # Add new URL
            if current_text:
                new_text = current_text + '\n' + url
            else:
                new_text = url
            
            # Update text field
            self.url_text.setPlainText(new_text)
            
            # Move cursor to end
            cursor = self.url_text.textCursor()
            cursor.movePosition(cursor.End)
            self.url_text.setTextCursor(cursor)
            
            # Flash green border for feedback
            self.flash_url_field()
            
            print(f"✅ URL added to input field: {url}")
            
        except Exception as e:
            print(f"❌ Error handling URL from extension: {e}")
    
    def flash_url_field(self):
        """Flash green border to show URL was received"""
        try:
            # Green border
            self.url_text.setStyleSheet("""
                QTextEdit {
                    border: 3px solid #00FF00;
                    border-radius: 8px;
                    padding: 10px;
                    background: #0a0a0a;
                    color: #FFFF00;
                }
            """)
            
            # Reset to normal after 1 second
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, self.reset_url_field_style)
            
        except Exception as e:
            print(f"⚠️ Could not flash border: {e}")
    
    def reset_url_field_style(self):
        """Reset URL field to normal style"""
        self.url_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #FFFF00;
                border-radius: 8px;
                padding: 10px;
                background: #0a0a0a;
                color: #FFFF00;
            }
        """)
    
    def closeEvent(self, event):
        """Cleanup when app is closed"""
        if self.extension_server:
            print("🛑 Stopping Chrome extension server...")
            self.extension_server.stop_server()
        
        # Call parent closeEvent
        super().closeEvent(event)

def main():
    print("📹 Creators Video Automation - Enhanced Edition")
    print("🔌 Chrome Extension Support Enabled")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    try:
        # Create and show enhanced app
        main_window = EnhancedCreatorsApp()
        main_window.show()
        
        print("\n🎉 App started successfully!")
        print("🌐 HTTP server running on localhost:7898")
        print("📱 Chrome extension can now send URLs to this app")
        print("\n💡 Usage:")
        print("  1. Go to any YouTube video in Chrome")
        print("  2. Right-click → '📹 Send to Creators'") 
        print("  3. URL appears automatically in this app!")
        print("\n⚠️  Keep this app running to receive URLs from Chrome")
        
        # Start Qt event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Failed to start app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()