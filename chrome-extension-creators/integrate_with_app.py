#!/usr/bin/env python3
"""
Integration Script: Add Chrome Extension Support to Creators Video Automation

This script shows how to integrate the Chrome extension server with your existing desktop app.
It creates a modified version of the main app with extension support built-in.
"""

import sys
import os
from pathlib import Path

# Add the desktop app directory to path
desktop_app_path = Path(__file__).parent.parent / "VideoAutomation" / "VideoAutomation"
sys.path.insert(0, str(desktop_app_path))

# Import the desktop server addon
from desktop_server_addon import add_extension_support, ExtensionServer

# Import original app components (you'll need to adjust these imports based on your actual app structure)
try:
    # Try to import from the original app
    # This assumes the video_app_v2.py is available
    import video_app_v2
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
except ImportError as e:
    print(f"❌ Could not import desktop app components: {e}")
    print("📝 Please ensure the desktop app files are in the correct location.")
    sys.exit(1)


class CreatorsAppWithExtension:
    """Enhanced Creators App with Chrome Extension Support"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        self.extension_server = None
    
    def start(self):
        """Start the enhanced application with extension support"""
        print("🚀 Starting Creators Video Automation with Chrome Extension support...")
        
        # Create Qt application
        self.app = QApplication(sys.argv)
        
        # Create main window (using your existing app)
        self.main_window = video_app_v2.CreatorsApp()  # Adjust class name as needed
        
        # Add extension support
        self.add_extension_integration()
        
        # Show the application
        self.main_window.show()
        
        print("✅ Application ready! Chrome extension can now send URLs.")
        print("📱 Install the Chrome extension to start using right-click integration.")
        
        # Start the application event loop
        return self.app.exec_()
    
    def add_extension_integration(self):
        """Integrate Chrome extension server with the desktop app"""
        try:
            # Find the URL input text widget
            # You may need to adjust this based on your actual widget structure
            url_text_widget = self.main_window.url_text
            
            # Add extension support
            self.extension_server = add_extension_support(
                self.main_window, 
                url_text_widget
            )
            
            # Add status indicator to app window
            self.add_extension_status_indicator()
            
        except AttributeError as e:
            print(f"⚠️ Could not find URL text widget: {e}")
            print("📝 Please check the widget name in your desktop app.")
    
    def add_extension_status_indicator(self):
        """Add visual indicator showing extension server status"""
        from PyQt5.QtWidgets import QLabel, QHBoxLayout
        from PyQt5.QtCore import Qt
        
        try:
            # Create status indicator
            status_layout = QHBoxLayout()
            
            self.extension_status = QLabel("🌐 Chrome Extension: Ready")
            self.extension_status.setStyleSheet("""
                QLabel {
                    background: #1a4f1a;
                    color: #4caf50;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-size: 11px;
                    border: 1px solid #4caf50;
                }
            """)
            
            status_layout.addWidget(self.extension_status)
            status_layout.addStretch()
            
            # Add to main window (adjust based on your layout)
            if hasattr(self.main_window, 'layout'):
                self.main_window.layout().addLayout(status_layout)
            
            print("✅ Extension status indicator added")
            
        except Exception as e:
            print(f"⚠️ Could not add status indicator: {e}")
    
    def cleanup(self):
        """Cleanup resources on app exit"""
        if self.extension_server:
            self.extension_server.stop_server()


def create_enhanced_app_launcher():
    """Create a launcher script for the enhanced app"""
    launcher_content = '''#!/usr/bin/env python3
"""
Enhanced Creators Video Automation with Chrome Extension Support
Launch script for the desktop app with extension integration
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the enhanced app
from integrate_with_app import CreatorsAppWithExtension

if __name__ == "__main__":
    print("📹 Creators Video Automation - Enhanced Edition")
    print("🔌 Chrome Extension Support Enabled")
    print("-" * 50)
    
    app = CreatorsAppWithExtension()
    
    try:
        exit_code = app.start()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\\n👋 Application interrupted by user")
        app.cleanup()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Application error: {e}")
        app.cleanup()
        sys.exit(1)
'''
    
    launcher_path = Path(__file__).parent / "launch_enhanced_app.py"
    launcher_path.write_text(launcher_content)
    launcher_path.chmod(0o755)
    
    print(f"✅ Created launcher script: {launcher_path}")
    return launcher_path


def main():
    """Main integration function"""
    print("🔧 Setting up Chrome Extension Integration...")
    
    # Create enhanced app launcher
    launcher_path = create_enhanced_app_launcher()
    
    print("\n📋 Setup Complete!")
    print("=" * 50)
    print("🚀 To run the enhanced app:")
    print(f"   python3 {launcher_path}")
    print("\n📱 To install Chrome extension:")
    print("   1. Open Chrome → Extensions → Developer mode")
    print("   2. Click 'Load unpacked'")
    print(f"   3. Select folder: {Path(__file__).parent}")
    print("\n✨ Usage:")
    print("   1. Start the desktop app")
    print("   2. Go to any YouTube video in Chrome")
    print("   3. Right-click → '📹 Paste to Creators'")
    print("   4. Video URL appears automatically in your app!")


if __name__ == "__main__":
    main()