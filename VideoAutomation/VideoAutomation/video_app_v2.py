#!/usr/bin/env python3
"""
YouTube Video Automation GUI - V2 ENHANCED
Creators! - PyQt5 Interface with:
- Per-video download progress
- Green tick / Red cross status
- Auto-retry failed downloads
- Better error handling
"""

import sys
import os
import subprocess
import re
import shutil
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QTextEdit, QPushButton, 
                             QLabel, QProgressBar, QFileDialog, QMessageBox,
                             QListWidget, QListWidgetItem, QSplitter, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QColor, QIcon

class VideoDownloadWorker(QThread):
    """Worker thread for downloading a single video with progress tracking"""
    progress = pyqtSignal(int, str, int)  # index, status_message, percentage
    finished = pyqtSignal(int, bool, str)  # index, success, error_message
    
    def __init__(self, index, url, output_dir):
        super().__init__()
        self.index = index
        self.url = url
        self.output_dir = output_dir
    
    def run(self):
        try:
            # Validate URL
            if not self.url.startswith(('http://', 'https://')):
                self.finished.emit(self.index, False, "Invalid URL format")
                return
            
            # Build yt-dlp command
            cmd = [
                'yt-dlp',
                '-f', 'bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[vcodec^=avc1][ext=mp4]/best[ext=mp4]/best',
                '--merge-output-format', 'mp4',
                '-o', f'{self.output_dir}/%(title)s.%(ext)s',
                '--restrict-filenames',
                '--no-part',
                '--retries', '3',
                '--newline',  # Progress on new lines for parsing
                '--progress-template', '%(progress._percent_str)s',
                self.url
            ]
            
            # Run with live output parsing
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            last_percent = 0
            for line in process.stdout:
                line = line.strip()
                
                # Parse percentage from yt-dlp output
                percent_match = re.search(r'(\d+\.?\d*)%', line)
                if percent_match:
                    try:
                        percent = int(float(percent_match.group(1)))
                        if percent != last_percent:
                            last_percent = percent
                            self.progress.emit(self.index, f"Downloading... {percent}%", percent)
                    except:
                        pass
                
                # Check for download status messages
                if '[download]' in line.lower():
                    self.progress.emit(self.index, "Downloading...", last_percent)
                elif '[merger]' in line.lower() or 'merging' in line.lower():
                    self.progress.emit(self.index, "Merging audio/video...", 95)
            
            process.wait()
            
            if process.returncode == 0:
                self.progress.emit(self.index, "Complete!", 100)
                self.finished.emit(self.index, True, "")
            else:
                self.finished.emit(self.index, False, "Download failed - video may be unavailable or restricted")
                
        except FileNotFoundError:
            self.finished.emit(self.index, False, "yt-dlp not found. Install with: brew install yt-dlp")
        except Exception as e:
            self.finished.emit(self.index, False, str(e))


class DownloadManager(QThread):
    """Manages sequential downloads with retry logic"""
    video_started = pyqtSignal(int)  # index
    video_progress = pyqtSignal(int, str, int)  # index, message, percent
    video_finished = pyqtSignal(int, bool, str)  # index, success, error
    all_finished = pyqtSignal(int, int, list)  # success_count, total, failed_indices
    retry_starting = pyqtSignal()
    
    def __init__(self, urls, output_dir, use_cookies=False):
        super().__init__()
        self.urls = urls
        self.output_dir = output_dir
        self.use_cookies = use_cookies
        self.results = {}  # index -> (success, error)
    
    def download_video(self, index, url):
        """Download a single video and return result"""
        try:
            if not url.startswith(('http://', 'https://')):
                return False, "Invalid URL format"
            
            cmd = [
                'yt-dlp',
                '-f', 'bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[vcodec^=avc1][ext=mp4]/best[ext=mp4]/best',
                '--merge-output-format', 'mp4',
                '-o', f'{self.output_dir}/%(title)s.%(ext)s',
                '--restrict-filenames',
                '--no-part',
                '--retries', '3',
                '--newline',
                self.url if hasattr(self, 'url') else url
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            last_percent = 0
            for line in process.stdout:
                line = line.strip()
                percent_match = re.search(r'(\d+\.?\d*)%', line)
                if percent_match:
                    try:
                        percent = int(float(percent_match.group(1)))
                        if percent != last_percent:
                            last_percent = percent
                            self.video_progress.emit(index, f"Downloading... {percent}%", percent)
                    except:
                        pass
                
                if 'merging' in line.lower() or '[merger]' in line.lower():
                    self.video_progress.emit(index, "Merging...", 95)
            
            process.wait()
            
            if process.returncode == 0:
                return True, ""
            else:
                return False, "Download failed"
                
        except FileNotFoundError:
            return False, "yt-dlp not found"
        except Exception as e:
            return False, str(e)
    
    def run(self):
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            
            failed_indices = []
            success_count = 0
            
            # First pass: download all videos
            for i, url in enumerate(self.urls):
                try:
                    self.video_started.emit(i)
                    self.video_progress.emit(i, "Starting download...", 0)
                    
                    success, error = self.download_single(i, url)
                    
                    self.results[i] = (success, error)
                    
                    if success:
                        success_count += 1
                        self.video_progress.emit(i, "Complete!", 100)
                        self.video_finished.emit(i, True, "")
                    else:
                        failed_indices.append(i)
                        self.video_finished.emit(i, False, error)
                except Exception as e:
                    failed_indices.append(i)
                    self.video_finished.emit(i, False, str(e)[:50])
            
            # Retry pass: retry failed downloads once
            if failed_indices:
                self.retry_starting.emit()
                
                retry_indices = failed_indices.copy()
                failed_indices = []
                
                for i in retry_indices:
                    try:
                        url = self.urls[i]
                        self.video_started.emit(i)
                        self.video_progress.emit(i, "Retrying...", 0)
                        
                        success, error = self.download_single(i, url)
                        
                        if success:
                            success_count += 1
                            self.video_progress.emit(i, "Complete! (retry)", 100)
                            self.video_finished.emit(i, True, "")
                        else:
                            failed_indices.append(i)
                            self.video_finished.emit(i, False, f"Retry failed: {error}")
                    except Exception as e:
                        failed_indices.append(i)
                        self.video_finished.emit(i, False, str(e)[:50])
            
            self.all_finished.emit(success_count, len(self.urls), failed_indices)
        except Exception as e:
            # Emit failure for all remaining
            self.all_finished.emit(0, len(self.urls), list(range(len(self.urls))))
    
    def download_single(self, index, url):
        """Download a single video"""
        try:
            if not url.startswith(('http://', 'https://')):
                return False, "Invalid URL"
            
            # Find yt-dlp path
            ytdlp_paths = ['/opt/homebrew/bin/yt-dlp', '/usr/local/bin/yt-dlp']
            ytdlp_cmd = None
            for p in ytdlp_paths:
                if os.path.exists(p):
                    ytdlp_cmd = p
                    break
            
            if not ytdlp_cmd:
                return False, "yt-dlp not found. Install with: brew install yt-dlp"
            
            # Note: YouTube now requires cookies. Chrome must be logged into YouTube.
            # If you get permission errors, close Chrome and try again.
            
            # Use h264/mp4 format - prefer 720p, fallback to any working format
            cmd = [
                ytdlp_cmd,
                '-f', '136+140/135+140/134+140/18/best',
                '--merge-output-format', 'mp4',
                '-o', f'{self.output_dir}/%(title)s.%(ext)s',
                '--restrict-filenames',
                '--retries', '10',
                '--fragment-retries', '10',
                '--retry-sleep', '3',
                '--continue',
                '--newline',
                '--no-check-certificate',
                '--remote-components', 'ejs:github',  # Required for YouTube JS challenges
                '--cookies-from-browser', 'chrome',  # Required - YouTube needs login
            ]
            
            cmd.append(url)
            
            # Set up environment with proper PATH
            env = os.environ.copy()
            env['PATH'] = '/opt/homebrew/bin:/usr/local/bin:' + env.get('PATH', '')
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env
            )
            
            last_percent = 0
            error_lines = []
            
            # Read stdout for progress
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                    
                # Check for errors in output
                if 'error' in line.lower() or 'ERROR' in line:
                    error_lines.append(line)
                
                percent_match = re.search(r'(\d+\.?\d*)%', line)
                if percent_match:
                    try:
                        percent = int(float(percent_match.group(1)))
                        if percent > last_percent:
                            last_percent = percent
                            self.video_progress.emit(index, f"Downloading... {percent}%", percent)
                    except:
                        pass
                
                if 'merging' in line.lower() or '[merger]' in line.lower():
                    self.video_progress.emit(index, "Merging audio/video...", 95)
                elif '[download]' in line.lower() and 'destination' in line.lower():
                    self.video_progress.emit(index, "Saving file...", 90)
            
            # Get stderr for errors
            stderr_output = process.stderr.read()
            if stderr_output:
                error_lines.append(stderr_output.strip())
            
            process.wait()
            
            if process.returncode == 0:
                return True, ""
            else:
                # Provide useful error message
                full_error = "\n".join(error_lines) if error_lines else ""
                if error_lines:
                    error_msg = error_lines[-1][:150]
                    if 'unavailable' in full_error.lower():
                        return False, "Video unavailable or private"
                    elif 'private' in full_error.lower():
                        return False, "Video is private"
                    elif 'copyright' in full_error.lower():
                        return False, "Video blocked (copyright)"
                    elif 'region' in full_error.lower() or 'country' in full_error.lower():
                        return False, "Region restricted"
                    elif 'sign in' in full_error.lower() or 'age' in full_error.lower():
                        return False, "Age-restricted (login required)"
                    else:
                        return False, error_msg
                return False, f"Exit {process.returncode}: Check Terminal for details"
            
        except FileNotFoundError:
            return False, "yt-dlp not found. Install with: brew install yt-dlp"
        except Exception as e:
            return False, f"Error: {str(e)[:80]}"


class ProcessThread(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, work_dir):
        super().__init__()
        self.work_dir = work_dir
    
    def run(self):
        try:
            script_path = os.path.join(self.work_dir, 'process_timeline.py')
            xml_path = os.path.join(self.work_dir, 'timeline.xml')
            output_path = os.path.join(self.work_dir, 'timeline_processed.xml')
            
            # Check if process_timeline.py exists
            if not os.path.exists(script_path):
                self.finished.emit(False, f"ERROR: process_timeline.py not found in {self.work_dir}")
                return
            
            # Check if timeline.xml exists
            if not os.path.exists(xml_path):
                self.finished.emit(False, "ERROR: timeline.xml not found. Please select a file first.")
                return
            
            self.progress.emit("Reading XML file...", 20)
            
            # Check if XML is valid by trying to parse it
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(xml_path)
                root = tree.getroot()
                if root.find('.//sequence') is None:
                    self.finished.emit(False, "ERROR: Invalid XML - No sequence found.\n\nMake sure you exported as 'Final Cut Pro XML' from Premiere.")
                    return
            except Exception as e:
                self.finished.emit(False, f"ERROR: Cannot parse XML file.\n\n{str(e)}\n\nMake sure it's a valid Final Cut Pro XML export.")
                return
            
            self.progress.emit("Cutting clips to 6 seconds...", 40)
            
            # Run the process_timeline.py script from work_dir
            result = subprocess.run(
                ['python3', script_path],
                capture_output=True,
                text=True,
                cwd=self.work_dir,
                input='\n'  # Auto-press Enter when script asks
            )
            
            self.progress.emit("Shuffling with smart algorithm...", 70)
            self.progress.emit("Adding color labels...", 90)
            
            # Check if output file was created (most reliable way to check success)
            if os.path.exists(output_path):
                # Verify the file is not empty
                if os.path.getsize(output_path) > 0:
                    self.finished.emit(True, f"✅ Successfully processed!\n\ntimeline_processed.xml created in:\n{self.work_dir}\n\n• 6-second cuts\n• Smart shuffle\n• Color labels")
                else:
                    self.finished.emit(False, f"ERROR: Output file is empty.\n\nScript output:\n{result.stdout[:300]}")
            else:
                error_detail = result.stderr if result.stderr else result.stdout
                self.finished.emit(False, f"PROCESSING FAILED:\n\n{error_detail[:300]}\n\nMake sure your XML was exported as 'Final Cut Pro XML'")
                
        except Exception as e:
            self.finished.emit(False, f"UNEXPECTED ERROR: {str(e)}\n\nTry exporting XML from Premiere again.")


class VideoListItem(QWidget):
    """Custom widget for video list items with status"""
    def __init__(self, index, url):
        super().__init__()
        self.index = index
        self.url = url
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status icon
        self.status_label = QLabel("⏳")
        self.status_label.setFixedWidth(30)
        self.status_label.setFont(QFont("Arial", 16))
        layout.addWidget(self.status_label)
        
        # URL and progress info
        info_layout = QVBoxLayout()
        
        # URL (truncated)
        display_url = url[:60] + "..." if len(url) > 60 else url
        self.url_label = QLabel(f"{index + 1}. {display_url}")
        self.url_label.setStyleSheet("color: #FFFF00; font-size: 12px;")
        info_layout.addWidget(self.url_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #FFFF00;
                border-radius: 3px;
                background-color: #1a1a1a;
                text-align: center;
                color: #000;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #FFFF00;
            }
        """)
        info_layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_text = QLabel("Waiting...")
        self.status_text.setStyleSheet("color: #888; font-size: 11px;")
        info_layout.addWidget(self.status_text)
        
        layout.addLayout(info_layout)
        self.setLayout(layout)
    
    def set_waiting(self):
        self.status_label.setText("⏳")
        self.status_text.setText("Waiting...")
        self.progress_bar.setValue(0)
    
    def set_downloading(self, message="Downloading...", percent=0):
        self.status_label.setText("📥")
        self.status_text.setText(message)
        self.status_text.setStyleSheet("color: #FFFF00; font-size: 11px;")
        self.progress_bar.setValue(percent)
    
    def set_success(self):
        self.status_label.setText("✅")
        self.status_text.setText("Downloaded successfully!")
        self.status_text.setStyleSheet("color: #00FF00; font-size: 11px;")
        self.progress_bar.setValue(100)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #00FF00;
                border-radius: 3px;
                background-color: #1a1a1a;
                text-align: center;
                color: #000;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #00FF00;
            }
        """)
    
    def set_failed(self, error="Download failed"):
        self.status_label.setText("❌")
        self.status_text.setText(error[:50])
        self.status_text.setStyleSheet("color: #FF4444; font-size: 11px;")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #FF4444;
                border-radius: 3px;
                background-color: #1a1a1a;
                text-align: center;
                color: #FFF;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #FF4444;
            }
        """)
    
    def set_retrying(self):
        self.status_label.setText("🔄")
        self.status_text.setText("Retrying...")
        self.status_text.setStyleSheet("color: #FFA500; font-size: 11px;")
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #FFA500;
                border-radius: 3px;
                background-color: #1a1a1a;
                text-align: center;
                color: #000;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #FFA500;
            }
        """)


class DropArea(QWidget):
    """Drag and drop area for XML files"""
    file_dropped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("📁 DRAG & DROP timeline.xml HERE\n\nOR CLICK BROWSE BELOW")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                border: 3px dashed #FFFF00;
                border-radius: 12px;
                padding: 30px;
                background-color: #0a0a0a;
                font-size: 14px;
                font-weight: bold;
                color: #FFFF00;
            }
        """)
        
        layout.addWidget(self.label)
        self.setLayout(layout)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setStyleSheet("""
                QLabel {
                    border: 3px dashed #00FF00;
                    border-radius: 12px;
                    padding: 30px;
                    background-color: #001a00;
                    font-size: 14px;
                    font-weight: bold;
                    color: #00FF00;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.label.setStyleSheet("""
            QLabel {
                border: 3px dashed #FFFF00;
                border-radius: 12px;
                padding: 30px;
                background-color: #0a0a0a;
                font-size: 14px;
                font-weight: bold;
                color: #FFFF00;
            }
        """)
    
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files and files[0].endswith('.xml'):
            self.file_dropped.emit(files[0])
            self.label.setText(f"✅ SELECTED:\n{os.path.basename(files[0])}")
        else:
            self.label.setText("❌ ERROR: Must be an XML file!")
        self.dragLeaveEvent(event)


class VideoAutomationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Creators! Video Automation v2")
        self.setGeometry(100, 100, 1000, 800)
        
        self.video_items = []
        self.download_manager = None
        
        # Set up working directory
        self.work_dir = os.path.expanduser('~/Documents/VideoAutomation')
        os.makedirs(self.work_dir, exist_ok=True)
        os.chdir(self.work_dir)
        
        # Copy process_timeline.py to work directory (always update)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_script = os.path.join(script_dir, 'process_timeline.py')
        dst_script = os.path.join(self.work_dir, 'process_timeline.py')
        if os.path.exists(src_script):
            shutil.copy(src_script, dst_script)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Logo
        logo_layout = QHBoxLayout()
        logo_layout.addStretch()
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, 'logo.png')
        if not os.path.exists(logo_path):
            logo_path = 'logo.png'
        
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaledToWidth(180, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled)
            logo_layout.addWidget(logo_label)
        
        logo_layout.addStretch()
        layout.addLayout(logo_layout)
        
        # Title
        title = QLabel("⚡ VIDEO AUTOMATION SYSTEM v2 ⚡")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("padding: 15px; color: #FFFF00; background-color: #000;")
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_download_tab(), "📥 DOWNLOAD VIDEOS")
        tabs.addTab(self.create_process_tab(), "⚙️ PROCESS TIMELINE")
        layout.addWidget(tabs)
        
        self.apply_styles()
    
    def create_download_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("PASTE YOUTUBE URLs BELOW (ONE PER LINE):")
        instructions.setStyleSheet("font-size: 14px; padding: 10px; color: #FFFF00;")
        layout.addWidget(instructions)
        
        # Splitter for URL input and video list
        splitter = QSplitter(Qt.Vertical)
        
        # URL text area
        self.url_text = QTextEdit()
        self.url_text.setPlaceholderText("https://www.youtube.com/watch?v=example1\nhttps://www.youtube.com/watch?v=example2")
        self.url_text.setMaximumHeight(150)
        splitter.addWidget(self.url_text)
        
        # Video list widget (shows status of each video)
        video_list_container = QWidget()
        video_list_layout = QVBoxLayout()
        video_list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("📋 DOWNLOAD STATUS:")
        list_label.setStyleSheet("font-size: 13px; padding: 5px; color: #FFFF00;")
        video_list_layout.addWidget(list_label)
        
        self.video_list_widget = QWidget()
        self.video_list_layout = QVBoxLayout()
        self.video_list_layout.setAlignment(Qt.AlignTop)
        self.video_list_widget.setLayout(self.video_list_layout)
        
        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidget(self.video_list_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 2px solid #FFFF00; border-radius: 8px; background: #0a0a0a; }")
        video_list_layout.addWidget(scroll)
        
        video_list_container.setLayout(video_list_layout)
        splitter.addWidget(video_list_container)
        
        layout.addWidget(splitter)
        
        # Cookie option for age-restricted videos
        cookie_layout = QHBoxLayout()
        self.cookie_checkbox = QCheckBox("🍪 Use Chrome cookies (RECOMMENDED - quit Chrome first!)")
        self.cookie_checkbox.setChecked(True)  # Default ON - YouTube often requires login
        self.cookie_checkbox.setStyleSheet("color: #FFFF00; font-size: 12px; padding: 5px;")
        self.cookie_checkbox.setToolTip("YouTube now often requires login to download.\nQuit Chrome (Cmd+Q) before downloading.\nChrome must be logged into YouTube.")
        cookie_layout.addWidget(self.cookie_checkbox)
        cookie_layout.addStretch()
        layout.addLayout(cookie_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("📥 START DOWNLOAD")
        self.download_btn.clicked.connect(self.start_download)
        btn_layout.addWidget(self.download_btn)
        
        self.open_folder_btn = QPushButton("📁 OPEN FOLDER")
        self.open_folder_btn.clicked.connect(self.open_download_folder)
        self.open_folder_btn.setEnabled(False)
        btn_layout.addWidget(self.open_folder_btn)
        
        layout.addLayout(btn_layout)
        
        # Overall progress
        self.overall_progress = QProgressBar()
        self.overall_progress.setVisible(False)
        self.overall_progress.setFormat("Overall: %p%")
        layout.addWidget(self.overall_progress)
        
        # Status
        self.download_status = QLabel("")
        self.download_status.setAlignment(Qt.AlignCenter)
        self.download_status.setStyleSheet("padding: 10px; font-size: 14px;")
        self.download_status.setWordWrap(True)
        layout.addWidget(self.download_status)
        
        tab.setLayout(layout)
        return tab
    
    def create_process_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        instructions = QLabel("1. EXPORT PREMIERE TIMELINE AS 'FINAL CUT PRO XML'\n2. DROP IT BELOW OR BROWSE\n3. CLICK PROCESS")
        instructions.setStyleSheet("font-size: 14px; padding: 10px; color: #FFFF00;")
        layout.addWidget(instructions)
        
        self.drop_area = DropArea()
        self.drop_area.file_dropped.connect(self.file_selected)
        layout.addWidget(self.drop_area)
        
        browse_btn = QPushButton("📂 BROWSE FOR XML")
        browse_btn.clicked.connect(self.browse_file)
        layout.addWidget(browse_btn)
        
        self.process_btn = QPushButton("⚙️ PROCESS TIMELINE")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        self.process_progress = QProgressBar()
        self.process_progress.setVisible(False)
        layout.addWidget(self.process_progress)
        
        self.process_status = QLabel("")
        self.process_status.setAlignment(Qt.AlignCenter)
        self.process_status.setStyleSheet("padding: 10px; font-size: 14px;")
        self.process_status.setWordWrap(True)
        layout.addWidget(self.process_status)
        
        self.open_output_btn = QPushButton("📁 OPEN OUTPUT FOLDER")
        self.open_output_btn.clicked.connect(self.open_output_folder)
        self.open_output_btn.setVisible(False)
        layout.addWidget(self.open_output_btn)
        
        tab.setLayout(layout)
        return tab
    
    def start_download(self):
        urls_text = self.url_text.toPlainText().strip()
        if not urls_text:
            QMessageBox.warning(self, "No URLs", "Please paste YouTube URLs first!")
            return
        
        urls = [u.strip() for u in urls_text.split('\n') if u.strip() and not u.startswith('#')]
        
        if not urls:
            QMessageBox.warning(self, "No Valid URLs", "No valid URLs found!")
            return
        
        # Clear previous items
        for item in self.video_items:
            self.video_list_layout.removeWidget(item)
            item.deleteLater()
        self.video_items = []
        
        # Create video list items
        for i, url in enumerate(urls):
            item = VideoListItem(i, url)
            self.video_items.append(item)
            self.video_list_layout.addWidget(item)
        
        # Setup UI
        self.download_btn.setEnabled(False)
        self.overall_progress.setVisible(True)
        self.overall_progress.setValue(0)
        self.overall_progress.setMaximum(len(urls))
        self.download_status.setText("Starting downloads...")
        self.download_status.setStyleSheet("padding: 10px; font-size: 14px; color: #FFFF00;")
        
        # Get output directory - use Documents folder for reliability
        output_dir = os.path.expanduser('~/Documents/VideoAutomation/premiere_videos')
        os.makedirs(output_dir, exist_ok=True)
        
        # Start download manager
        use_cookies = self.cookie_checkbox.isChecked()
        self.download_manager = DownloadManager(urls, output_dir, use_cookies)
        self.download_manager.video_started.connect(self.on_video_started)
        self.download_manager.video_progress.connect(self.on_video_progress)
        self.download_manager.video_finished.connect(self.on_video_finished)
        self.download_manager.all_finished.connect(self.on_all_finished)
        self.download_manager.retry_starting.connect(self.on_retry_starting)
        self.download_manager.start()
    
    def on_video_started(self, index):
        if index < len(self.video_items):
            self.video_items[index].set_downloading("Starting...", 0)
    
    def on_video_progress(self, index, message, percent):
        if index < len(self.video_items):
            self.video_items[index].set_downloading(message, percent)
    
    def on_video_finished(self, index, success, error):
        if index < len(self.video_items):
            if success:
                self.video_items[index].set_success()
            else:
                self.video_items[index].set_failed(error)
        
        # Update overall progress
        completed = sum(1 for item in self.video_items 
                       if item.status_label.text() in ["✅", "❌"])
        self.overall_progress.setValue(completed)
    
    def on_retry_starting(self):
        self.download_status.setText("🔄 Retrying failed downloads...")
        self.download_status.setStyleSheet("padding: 10px; font-size: 14px; color: #FFA500;")
        
        # Mark failed items as retrying
        for item in self.video_items:
            if item.status_label.text() == "❌":
                item.set_retrying()
    
    def on_all_finished(self, success_count, total, failed_indices):
        self.download_btn.setEnabled(True)
        self.overall_progress.setValue(total)
        self.open_folder_btn.setEnabled(True)
        
        if failed_indices:
            self.download_status.setText(f"⚠️ Completed: {success_count}/{total} videos downloaded")
            self.download_status.setStyleSheet("padding: 10px; font-size: 14px; color: #FFA500;")
            
            # Gather actual error messages from video items
            errors = []
            for i in failed_indices[:5]:
                if i < len(self.video_items):
                    error_text = self.video_items[i].status_text.text()
                    errors.append(f"Video {i+1}: {error_text}")
            
            error_details = "\n".join(errors)
            if len(failed_indices) > 5:
                error_details += f"\n(+{len(failed_indices)-5} more)"
            
            QMessageBox.warning(self, "Download Complete", 
                f"Downloaded {success_count}/{total} videos.\n\n"
                f"Failed:\n{error_details}")
        else:
            self.download_status.setText(f"✅ All {total} videos downloaded successfully!")
            self.download_status.setStyleSheet("padding: 10px; font-size: 14px; color: #00FF00;")
            QMessageBox.information(self, "Success", 
                f"All {total} videos downloaded!\n\nFiles are in:\n~/Documents/VideoAutomation/premiere_videos")
    
    def open_download_folder(self):
        folder = os.path.expanduser('~/Documents/VideoAutomation/premiere_videos')
        os.makedirs(folder, exist_ok=True)
        subprocess.run(['open', folder])
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select XML", "", "XML Files (*.xml)")
        if file_path:
            self.file_selected(file_path)
    
    def file_selected(self, file_path):
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Error", f"File not found: {file_path}")
            return
        
        try:
            # Copy to work_dir as timeline.xml (unless already there)
            dest_path = os.path.join(self.work_dir, 'timeline.xml')
            src_real = os.path.realpath(file_path)
            dst_real = os.path.realpath(dest_path)
            
            if src_real != dst_real:
                shutil.copy(file_path, dest_path)
            # else: file is already in place, no need to copy
            
            self.process_status.setText(f"✅ Selected: {os.path.basename(file_path)}")
            self.process_status.setStyleSheet("padding: 10px; font-size: 14px; color: #00FF00;")
            self.process_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy file: {e}")
    
    def start_processing(self):
        timeline_path = os.path.join(self.work_dir, 'timeline.xml')
        if not os.path.exists(timeline_path):
            QMessageBox.warning(self, "No File", "Please select timeline.xml first!")
            return
        
        self.process_btn.setEnabled(False)
        self.process_progress.setVisible(True)
        self.process_progress.setValue(0)
        self.open_output_btn.setVisible(False)
        
        self.process_thread = ProcessThread(self.work_dir)
        self.process_thread.progress.connect(self.update_process_progress)
        self.process_thread.finished.connect(self.process_finished)
        self.process_thread.start()
    
    def update_process_progress(self, message, percent):
        self.process_status.setText(message)
        self.process_progress.setValue(percent)
    
    def process_finished(self, success, message):
        self.process_btn.setEnabled(True)
        self.process_progress.setVisible(False)
        
        if success:
            self.process_status.setText("✅ PROCESSING COMPLETE!")
            self.process_status.setStyleSheet("padding: 10px; font-size: 14px; color: #00FF00;")
            self.open_output_btn.setVisible(True)
            QMessageBox.information(self, "Success", message)
        else:
            self.process_status.setText("❌ PROCESSING FAILED")
            self.process_status.setStyleSheet("padding: 10px; font-size: 14px; color: #FF4444;")
            QMessageBox.critical(self, "Error", message)
    
    def open_output_folder(self):
        subprocess.run(['open', self.work_dir])
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #000;
                color: #FFFF00;
            }
            QTabWidget::pane {
                border: 2px solid #FFFF00;
                border-radius: 8px;
                background: #000;
            }
            QTabBar::tab {
                background: #1a1a1a;
                color: #FFFF00;
                padding: 12px 25px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #000;
                border: 2px solid #FFFF00;
                border-bottom: none;
            }
            QPushButton {
                background: #FFFF00;
                color: #000;
                border: 2px solid #FFFF00;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #000;
                color: #FFFF00;
            }
            QPushButton:disabled {
                background: #333;
                color: #666;
                border-color: #333;
            }
            QTextEdit {
                border: 2px solid #FFFF00;
                border-radius: 8px;
                padding: 10px;
                background: #0a0a0a;
                color: #FFFF00;
                font-family: monospace;
            }
            QProgressBar {
                border: 2px solid #FFFF00;
                border-radius: 8px;
                text-align: center;
                height: 30px;
                background: #0a0a0a;
                color: #000;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: #FFFF00;
                border-radius: 6px;
            }
            QLabel {
                color: #FFFF00;
            }
            QScrollArea {
                background: #0a0a0a;
            }
        """)


class InstallDialog(QMainWindow):
    """Dialog to install missing dependencies"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Setup Required")
        self.setFixedSize(500, 350)
        
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        widget.setLayout(layout)
        
        # Icon/Title
        title = QLabel("⚠️ One-Time Setup Required")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Message
        msg = QLabel("This app needs yt-dlp to download YouTube videos.\n\nClick the button below to install it automatically.\n(This only takes about 30 seconds)")
        msg.setFont(QFont("Arial", 13))
        msg.setAlignment(Qt.AlignCenter)
        msg.setWordWrap(True)
        layout.addWidget(msg)
        
        # Install button
        self.install_btn = QPushButton("📦 Install yt-dlp Now")
        self.install_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.install_btn.setMinimumHeight(60)
        self.install_btn.clicked.connect(self.install_ytdlp)
        layout.addWidget(self.install_btn)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.status_label)
        
        # Skip button (if already installed elsewhere)
        skip_btn = QPushButton("I already have it installed → Continue")
        skip_btn.setStyleSheet("background: transparent; color: #888; border: none; text-decoration: underline;")
        skip_btn.clicked.connect(self.check_and_continue)
        layout.addWidget(skip_btn)
        
        layout.addStretch()
        
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a1a;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #FFFF00;
                color: #000000;
                border: none;
                border-radius: 10px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #DDDD00;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)
    
    def install_ytdlp(self):
        self.install_btn.setEnabled(False)
        self.install_btn.setText("⏳ Installing...")
        self.status_label.setText("Please wait, this may take a minute...")
        self.status_label.setStyleSheet("color: #FFFF00;")
        
        # Force UI update
        QApplication.processEvents()
        
        try:
            # Check if brew is installed
            brew_check = subprocess.run(['which', 'brew'], capture_output=True, text=True)
            
            if brew_check.returncode != 0:
                # Homebrew not installed - try to find common paths
                brew_paths = ['/opt/homebrew/bin/brew', '/usr/local/bin/brew']
                brew_path = None
                for p in brew_paths:
                    if os.path.exists(p):
                        brew_path = p
                        break
                
                if not brew_path:
                    self.status_label.setText("❌ Homebrew not found!\n\nPlease install Homebrew first:\n/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
                    self.status_label.setStyleSheet("color: #FF6666;")
                    self.install_btn.setText("📦 Try Again")
                    self.install_btn.setEnabled(True)
                    return
            else:
                brew_path = brew_check.stdout.strip()
            
            # Run brew install yt-dlp
            env = os.environ.copy()
            env['PATH'] = '/opt/homebrew/bin:/usr/local/bin:' + env.get('PATH', '')
            
            result = subprocess.run(
                ['brew', 'install', 'yt-dlp'],
                capture_output=True,
                text=True,
                env=env,
                timeout=120
            )
            
            # Verify installation
            verify = subprocess.run(['yt-dlp', '--version'], capture_output=True, env=env)
            
            if verify.returncode == 0:
                self.status_label.setText("✅ Installation complete!")
                self.status_label.setStyleSheet("color: #00FF00;")
                self.install_btn.setText("🚀 Launch App")
                self.install_btn.setEnabled(True)
                self.install_btn.clicked.disconnect()
                self.install_btn.clicked.connect(self.launch_main_app)
            else:
                self.status_label.setText("❌ Installation may have failed.\nTry running in Terminal:\nbrew install yt-dlp")
                self.status_label.setStyleSheet("color: #FF6666;")
                self.install_btn.setText("📦 Try Again")
                self.install_btn.setEnabled(True)
                
        except subprocess.TimeoutExpired:
            self.status_label.setText("⏱️ Installation timed out.\nPlease run manually in Terminal:\nbrew install yt-dlp")
            self.status_label.setStyleSheet("color: #FF6666;")
            self.install_btn.setText("📦 Try Again")
            self.install_btn.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)[:100]}\n\nTry running in Terminal:\nbrew install yt-dlp")
            self.status_label.setStyleSheet("color: #FF6666;")
            self.install_btn.setText("📦 Try Again")
            self.install_btn.setEnabled(True)
    
    def check_and_continue(self):
        env = os.environ.copy()
        env['PATH'] = '/opt/homebrew/bin:/usr/local/bin:' + env.get('PATH', '')
        
        try:
            result = subprocess.run(['yt-dlp', '--version'], capture_output=True, env=env)
            if result.returncode == 0:
                self.launch_main_app()
            else:
                self.status_label.setText("❌ yt-dlp not found. Please install it first.")
                self.status_label.setStyleSheet("color: #FF6666;")
        except:
            self.status_label.setText("❌ yt-dlp not found. Please install it first.")
            self.status_label.setStyleSheet("color: #FF6666;")
    
    def launch_main_app(self):
        self.hide()
        self.main_window = VideoAutomationApp()
        self.main_window.show()


def check_ytdlp_installed():
    """Check if yt-dlp is available"""
    env = os.environ.copy()
    env['PATH'] = '/opt/homebrew/bin:/usr/local/bin:' + env.get('PATH', '')
    
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, env=env, timeout=5)
        return result.returncode == 0
    except:
        return False


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Creators! Video Automation v2")
    
    # Check for yt-dlp
    if check_ytdlp_installed():
        window = VideoAutomationApp()
        window.show()
    else:
        # Show install dialog
        install_dialog = InstallDialog()
        install_dialog.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
