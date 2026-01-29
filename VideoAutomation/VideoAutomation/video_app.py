#!/usr/bin/env python3
"""
YouTube Video Automation GUI - ENHANCED VERSION
Creators! - PyQt5 Interface with Logo & Error Handling
"""

import sys
import os
import subprocess
import threading
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QTextEdit, QPushButton, 
                             QLabel, QProgressBar, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont, QPixmap

class DownloadThread(QThread):
    progress = pyqtSignal(str, int)  # message, percentage
    finished = pyqtSignal(bool, str)
    
    def __init__(self, urls):
        super().__init__()
        self.urls = urls
    
    def run(self):
        try:
            # Check if yt-dlp is installed
            try:
                subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.finished.emit(False, "ERROR: yt-dlp not installed. Please run: brew install yt-dlp")
                return
            
            # Create premiere_videos folder
            os.makedirs('premiere_videos', exist_ok=True)
            
            success_count = 0
            failed_urls = []
            
            for i, url in enumerate(self.urls, 1):
                percentage = int((i / len(self.urls)) * 100)
                self.progress.emit(f"Downloading video {i}/{len(self.urls)}...", percentage)
                
                # Validate URL
                if not url.startswith(('http://', 'https://')):
                    failed_urls.append(f"Line {i}: Invalid URL format")
                    continue
                
                cmd = [
                    'yt-dlp',
                    '-f', 'bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[vcodec^=avc1][ext=mp4]/best[ext=mp4]/best',
                    '--merge-output-format', 'mp4',
                    '-o', 'premiere_videos/%(title)s.%(ext)s',
                    '--restrict-filenames',
                    '--no-part',  # Don't use .part files
                    '--no-continue',  # Start fresh if interrupted
                    '--retries', '3',  # Retry 3 times on failure
                    url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    success_count += 1
                else:
                    failed_urls.append(f"Video {i}: {url[:50]}...")
            
            # Final message
            if failed_urls:
                error_msg = f"Downloaded {success_count}/{len(self.urls)} videos.\n\nFailed:\n" + "\n".join(failed_urls[:5])
                if len(failed_urls) > 5:
                    error_msg += f"\n...and {len(failed_urls) - 5} more"
                self.finished.emit(True, error_msg)
            else:
                self.finished.emit(True, f"Successfully downloaded all {success_count} videos!")
            
        except Exception as e:
            self.finished.emit(False, f"UNEXPECTED ERROR: {str(e)}\n\nPlease report this error.")

class ProcessThread(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, xml_path):
        super().__init__()
        self.xml_path = xml_path
    
    def run(self):
        try:
            # Check if process_timeline.py exists
            if not os.path.exists('process_timeline.py'):
                self.finished.emit(False, "ERROR: process_timeline.py not found in working directory.")
                return
            
            # Check if timeline.xml exists
            if not os.path.exists('timeline.xml'):
                self.finished.emit(False, "ERROR: timeline.xml not found. Please export from Premiere first.")
                return
            
            self.progress.emit("Reading XML file...", 20)
            
            # Check if XML is valid by trying to parse it
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse('timeline.xml')
                root = tree.getroot()
                if root.find('.//sequence') is None:
                    self.finished.emit(False, "ERROR: Invalid XML - No sequence found.\n\nMake sure you exported as 'Final Cut Pro XML' from Premiere.")
                    return
            except Exception as e:
                self.finished.emit(False, f"ERROR: Cannot parse XML file.\n\n{str(e)}\n\nMake sure it's a valid Final Cut Pro XML export.")
                return
            
            self.progress.emit("Cutting clips to 6 seconds...", 40)
            
            # Run the process_timeline.py script
            result = subprocess.run(
                ['python3', 'process_timeline.py'],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                input='\n'  # Auto-press Enter when script asks
            )
            
            self.progress.emit("Shuffling with smart algorithm...", 70)
            self.progress.emit("Adding color labels...", 90)
            
            # Check if output file was created (most reliable way to check success)
            if os.path.exists('timeline_processed.xml'):
                # Verify the file is not empty
                if os.path.getsize('timeline_processed.xml') > 0:
                    self.finished.emit(True, "✅ Successfully processed!\n\ntimeline_processed.xml created with:\n• 6-second cuts\n• Smart shuffle\n• Color labels")
                else:
                    self.finished.emit(False, f"ERROR: Output file is empty.\n\nScript output:\n{result.stdout[:300]}")
            else:
                error_detail = result.stderr if result.stderr else result.stdout
                self.finished.emit(False, f"PROCESSING FAILED:\n\n{error_detail[:300]}\n\nMake sure your XML was exported as 'Final Cut Pro XML'")
                
        except Exception as e:
            self.finished.emit(False, f"UNEXPECTED ERROR: {str(e)}\n\nTry exporting XML from Premiere again.")

class DropArea(QWidget):
    file_dropped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        
        layout = QVBoxLayout()
        
        label = QLabel("📁 DRAG & DROP timeline.xml HERE\n\nOR CLICK BROWSE BUTTON BELOW")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                border: 3px dashed #FFFF00;
                border-radius: 12px;
                padding: 45px;
                background-color: #0a0a0a;
                font-size: 15px;
                font-weight: bold;
                color: #FFFF00;
            }
        """)
        
        layout.addWidget(label)
        self.setLayout(layout)
        self.label = label
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setStyleSheet("""
                QLabel {
                    border: 3px dashed #00FF00;
                    border-radius: 12px;
                    padding: 45px;
                    background-color: #001a00;
                    font-size: 15px;
                    font-weight: bold;
                    color: #00FF00;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.label.setStyleSheet("""
            QLabel {
                border: 3px dashed #FFFF00;
                border-radius: 12px;
                padding: 45px;
                background-color: #0a0a0a;
                font-size: 15px;
                font-weight: bold;
                color: #FFFF00;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            if files[0].endswith('.xml'):
                self.file_dropped.emit(files[0])
                self.label.setText(f"✅ SELECTED: {os.path.basename(files[0])}")
            else:
                self.label.setText(f"❌ ERROR: Must be an XML file!")
        self.dragLeaveEvent(event)

class VideoAutomationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Creators! Video Automation")
        self.setGeometry(100, 100, 900, 700)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Logo section
        logo_layout = QHBoxLayout()
        logo_layout.addStretch()
        
        if os.path.exists('logo.png'):
            logo_label = QLabel()
            pixmap = QPixmap('logo.png')
            # Scale logo to reasonable size (max 200px wide)
            scaled_pixmap = pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(logo_label)
        
        logo_layout.addStretch()
        layout.addLayout(logo_layout)
        
        # Title
        title = QLabel("⚡ VIDEO AUTOMATION SYSTEM ⚡")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("padding: 20px; color: #FFFF00; background-color: #000000;")
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_download_tab(), "📥 DOWNLOAD VIDEOS")
        tabs.addTab(self.create_process_tab(), "⚙️ PROCESS TIMELINE")
        layout.addWidget(tabs)
        
        # Apply styling - ENHANCED
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QWidget {
                background-color: #000000;
                color: #FFFF00;
            }
            QTabWidget::pane {
                border: 2px solid #FFFF00;
                border-radius: 8px;
                background-color: #000000;
            }
            QTabBar::tab {
                background-color: #1a1a1a;
                color: #FFFF00;
                padding: 15px 30px;
                margin-right: 3px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #000000;
                border: 2px solid #FFFF00;
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background-color: #2a2a2a;
            }
            QPushButton {
                background-color: #FFFF00;
                color: #000000;
                border: 3px solid #FFFF00;
                padding: 18px 40px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #000000;
                color: #FFFF00;
                border: 3px solid #FFFF00;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: #CCCC00;
                color: #000000;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
                border: 3px solid #333333;
            }
            QTextEdit {
                border: 2px solid #FFFF00;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Courier New';
                font-size: 13px;
                background-color: #0a0a0a;
                color: #FFFF00;
                font-weight: bold;
            }
            QProgressBar {
                border: 2px solid #FFFF00;
                border-radius: 8px;
                text-align: center;
                height: 35px;
                background-color: #0a0a0a;
                color: #000000;
                font-weight: bold;
                font-size: 14px;
            }
            QProgressBar::chunk {
                background-color: #FFFF00;
                border-radius: 6px;
            }
            QLabel {
                color: #FFFF00;
                font-weight: bold;
            }
        """)
    
    def create_download_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("PASTE YOUTUBE URLs BELOW (ONE PER LINE):")
        instructions.setStyleSheet("font-size: 15px; padding: 15px; color: #FFFF00; font-weight: bold;")
        layout.addWidget(instructions)
        
        # URL text area
        self.url_text = QTextEdit()
        self.url_text.setPlaceholderText("https://www.youtube.com/watch?v=example1\nhttps://www.youtube.com/watch?v=example2\nhttps://www.youtube.com/watch?v=example3")
        layout.addWidget(self.url_text)
        
        # Download button - MORE PROMINENT
        self.download_btn = QPushButton("📥 DOWNLOAD VIDEOS (H.264)")
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)
        
        # Progress bar with percentage
        self.download_progress = QProgressBar()
        self.download_progress.setVisible(False)
        self.download_progress.setFormat("%p% - Downloading...")
        layout.addWidget(self.download_progress)
        
        # Status label
        self.download_status = QLabel("")
        self.download_status.setAlignment(Qt.AlignCenter)
        self.download_status.setStyleSheet("padding: 15px; font-size: 14px; font-weight: bold;")
        self.download_status.setWordWrap(True)
        layout.addWidget(self.download_status)
        
        tab.setLayout(layout)
        return tab
    
    def create_process_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("1. EXPORT PREMIERE TIMELINE AS 'FINAL CUT PRO XML'\n2. DROP IT BELOW OR BROWSE FOR IT\n3. CLICK PROCESS TO CUT, SHUFFLE & ADD COLOR LABELS")
        instructions.setStyleSheet("font-size: 15px; padding: 15px; color: #FFFF00; font-weight: bold;")
        layout.addWidget(instructions)
        
        # Drop area
        self.drop_area = DropArea()
        self.drop_area.file_dropped.connect(self.file_selected)
        layout.addWidget(self.drop_area)
        
        # Browse button
        browse_btn = QPushButton("📂 BROWSE FOR timeline.xml")
        browse_btn.clicked.connect(self.browse_file)
        layout.addWidget(browse_btn)
        
        # Process button - MORE PROMINENT
        self.process_btn = QPushButton("⚙️ CUT, SHUFFLE & ADD COLORS")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        # Progress bar with percentage
        self.process_progress = QProgressBar()
        self.process_progress.setVisible(False)
        self.process_progress.setFormat("%p% - Processing...")
        layout.addWidget(self.process_progress)
        
        # Status label
        self.process_status = QLabel("")
        self.process_status.setAlignment(Qt.AlignCenter)
        self.process_status.setStyleSheet("padding: 15px; font-size: 14px; font-weight: bold;")
        self.process_status.setWordWrap(True)
        layout.addWidget(self.process_status)
        
        # Open folder button
        self.open_folder_btn = QPushButton("📁 OPEN OUTPUT FOLDER")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.setVisible(False)
        layout.addWidget(self.open_folder_btn)
        
        tab.setLayout(layout)
        return tab
    
    def start_download(self):
        urls_text = self.url_text.toPlainText().strip()
        if not urls_text:
            QMessageBox.warning(self, "⚠️ No URLs", "Please paste YouTube URLs first!")
            return
        
        urls = [url.strip() for url in urls_text.split('\n') if url.strip() and not url.startswith('#')]
        
        if not urls:
            QMessageBox.warning(self, "⚠️ No Valid URLs", "Please paste valid YouTube URLs!\n\nFormat: https://www.youtube.com/watch?v=...")
            return
        
        # Disable button and show progress
        self.download_btn.setEnabled(False)
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)
        self.download_status.setText("Starting download...")
        
        # Start download thread
        self.download_thread = DownloadThread(urls)
        self.download_thread.progress.connect(self.update_download_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()
    
    def update_download_progress(self, message, percentage):
        self.download_status.setText(message)
        self.download_progress.setValue(percentage)
        self.download_progress.setFormat(f"{percentage}% - {message}")
    
    def download_finished(self, success, message):
        self.download_btn.setEnabled(True)
        self.download_progress.setVisible(False)
        
        if success:
            self.download_status.setText(f"✅ COMPLETE!")
            self.download_status.setStyleSheet("padding: 15px; font-size: 14px; color: #00FF00; font-weight: bold;")
            QMessageBox.information(self, "✅ Success", f"{message}\n\nVideos are in 'premiere_videos' folder.\n\nNext: Import to Premiere, scale clips, export XML.")
        else:
            self.download_status.setText(f"❌ ERROR")
            self.download_status.setStyleSheet("padding: 15px; font-size: 14px; color: #FF0000; font-weight: bold;")
            QMessageBox.critical(self, "❌ Error", message)
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select timeline.xml",
            "",
            "XML Files (*.xml)"
        )
        if file_path:
            self.file_selected(file_path)
    
    def file_selected(self, file_path):
        # Validate XML file
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "❌ File Not Found", f"Cannot find file:\n{file_path}")
            return
        
        # Copy file to timeline.xml if it has a different name
        try:
            if os.path.basename(file_path) != 'timeline.xml':
                import shutil
                shutil.copy(file_path, 'timeline.xml')
                self.process_status.setText(f"✅ COPIED: {os.path.basename(file_path)} → timeline.xml")
            else:
                self.process_status.setText(f"✅ SELECTED: timeline.xml")
            
            self.process_status.setStyleSheet("padding: 15px; font-size: 14px; color: #00FF00; font-weight: bold;")
            self.process_btn.setEnabled(True)
            self.selected_file = file_path
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Failed to copy file:\n{str(e)}")
    
    def start_processing(self):
        if not os.path.exists('timeline.xml'):
            QMessageBox.warning(self, "⚠️ No File", "Please select timeline.xml first!")
            return
        
        # Disable button and show progress
        self.process_btn.setEnabled(False)
        self.process_progress.setVisible(True)
        self.process_progress.setValue(0)
        self.process_status.setText("Starting processing...")
        self.open_folder_btn.setVisible(False)
        
        # Start processing thread
        self.process_thread = ProcessThread('timeline.xml')
        self.process_thread.progress.connect(self.update_process_progress)
        self.process_thread.finished.connect(self.process_finished)
        self.process_thread.start()
    
    def update_process_progress(self, message, percentage):
        self.process_status.setText(message)
        self.process_progress.setValue(percentage)
        self.process_progress.setFormat(f"{percentage}% - {message}")
    
    def process_finished(self, success, message):
        self.process_btn.setEnabled(True)
        self.process_progress.setVisible(False)
        
        if success:
            self.process_status.setText(f"✅ PROCESSING COMPLETE!")
            self.process_status.setStyleSheet("padding: 15px; font-size: 14px; color: #00FF00; font-weight: bold;")
            self.open_folder_btn.setVisible(True)
            QMessageBox.information(self, "✅ Success", message)
        else:
            self.process_status.setText(f"❌ PROCESSING FAILED")
            self.process_status.setStyleSheet("padding: 15px; font-size: 14px; color: #FF0000; font-weight: bold;")
            QMessageBox.critical(self, "❌ Error", message)
    
    def open_output_folder(self):
        folder = os.getcwd()
        subprocess.run(['open', folder])

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Creators! Video Automation")
    
    # Check for required tools
    missing_tools = []
    
    try:
        subprocess.run(['python3', '--version'], capture_output=True, check=True)
    except:
        missing_tools.append("Python 3")
    
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except:
        missing_tools.append("yt-dlp (run: brew install yt-dlp)")
    
    if missing_tools:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("❌ Missing Requirements")
        msg.setText("The following tools are required but not installed:\n\n" + "\n".join(f"• {tool}" for tool in missing_tools))
        msg.exec_()
        return
    
    window = VideoAutomationApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()