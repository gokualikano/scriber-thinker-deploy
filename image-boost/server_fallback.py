#!/usr/bin/env python3
"""
ImageBoost - Fallback version without REMBG
4x Upscale + Basic Background Processing
"""

import os
import uuid
import time
from datetime import datetime
from pathlib import Path
import threading
import json
import logging

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from PIL import Image, ImageFilter, ImageEnhance
import cv2
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

# Create directories
for dir_path in [UPLOAD_DIR, OUTPUT_DIR]:
    dir_path.mkdir(exist_ok=True)

# Global processing status
processing_status = {}

def enhance_image(image):
    """Enhance image quality during upscaling"""
    # Convert to array for processing
    img_array = np.array(image)
    
    # Apply bilateral filter for noise reduction while preserving edges
    filtered = cv2.bilateralFilter(img_array, 9, 75, 75)
    
    # Convert back to PIL
    enhanced = Image.fromarray(filtered)
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(enhanced)
    enhanced = enhancer.enhance(1.2)
    
    # Enhance contrast slightly
    enhancer = ImageEnhance.Contrast(enhanced)
    enhanced = enhancer.enhance(1.1)
    
    return enhanced

def smart_upscale(image, scale=4):
    """Advanced upscaling with quality enhancement"""
    # First, enhance the original image
    enhanced = enhance_image(image)
    
    # Upscale using high-quality resampling
    width, height = enhanced.size
    new_size = (width * scale, height * scale)
    
    # Use LANCZOS for best quality
    upscaled = enhanced.resize(new_size, Image.Resampling.LANCZOS)
    
    return upscaled

def create_transparent_background(image):
    """Convert image to have transparent background (basic method)"""
    # Convert to RGBA if not already
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Get image data
    data = image.getdata()
    
    # Create new data list
    new_data = []
    
    # Get the most common edge colors (likely background)
    width, height = image.size
    edge_pixels = []
    
    # Sample edge pixels
    for x in range(width):
        edge_pixels.append(image.getpixel((x, 0)))  # Top edge
        edge_pixels.append(image.getpixel((x, height-1)))  # Bottom edge
    
    for y in range(height):
        edge_pixels.append(image.getpixel((0, y)))  # Left edge  
        edge_pixels.append(image.getpixel((width-1, y)))  # Right edge
    
    # Find most common color (simple background detection)
    from collections import Counter
    if edge_pixels:
        # Convert RGBA to RGB for comparison
        rgb_pixels = [(r, g, b) for r, g, b, a in edge_pixels]
        most_common = Counter(rgb_pixels).most_common(1)[0][0]
        bg_color = most_common
    else:
        bg_color = (255, 255, 255)  # Default to white
    
    # Make background transparent (with tolerance)
    tolerance = 30
    for item in data:
        r, g, b, a = item[:4] if len(item) >= 4 else (item[0], item[1], item[2], 255)
        
        # Check if pixel is close to background color
        if (abs(r - bg_color[0]) <= tolerance and 
            abs(g - bg_color[1]) <= tolerance and 
            abs(b - bg_color[2]) <= tolerance):
            # Make transparent
            new_data.append((r, g, b, 0))
        else:
            # Keep original
            new_data.append((r, g, b, a))
    
    # Create new image with transparent background
    result = Image.new('RGBA', image.size)
    result.putdata(new_data)
    
    return result

def process_image_background(task_id, input_path, output_path):
    """Background processing function"""
    global processing_status
    
    try:
        processing_status[task_id] = {"step": "starting", "progress": 0}
        
        # Load image
        logger.info(f"📂 Loading image: {input_path}")
        image = Image.open(input_path)
        
        processing_status[task_id] = {"step": "upscaling", "progress": 20}
        
        # Smart upscale 4x
        logger.info("🔍 Smart upscaling image 4x...")
        upscaled = smart_upscale(image, scale=4)
        
        processing_status[task_id] = {"step": "removing_bg", "progress": 70}
        
        # Create transparent background
        logger.info("🎭 Creating transparent background...")
        final_image = create_transparent_background(upscaled)
        
        processing_status[task_id] = {"step": "saving", "progress": 90}
        
        # Save final image
        logger.info(f"💾 Saving processed image: {output_path}")
        final_image.save(output_path, format='PNG', optimize=True)
        
        processing_status[task_id] = {"step": "complete", "progress": 100, "output_path": str(output_path)}
        
        # Clean up input file
        os.unlink(input_path)
        
        logger.info(f"✅ Processing complete: {task_id}")
        
    except Exception as e:
        logger.error(f"❌ Processing error: {e}")
        processing_status[task_id] = {"step": "error", "progress": 0, "error": str(e)}

@app.route('/')
def index():
    """Main interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start processing"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.avif'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        return jsonify({'error': f'Unsupported file type: {file_ext}'}), 400
    
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Save uploaded file
        input_filename = f"{task_id}_input{file_ext}"
        output_filename = f"{task_id}_processed.png"
        
        input_path = UPLOAD_DIR / input_filename
        output_path = OUTPUT_DIR / output_filename
        
        file.save(input_path)
        
        # Start background processing
        thread = threading.Thread(
            target=process_image_background,
            args=(task_id, input_path, output_path)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'status': 'processing_started'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status/<task_id>')
def get_status(task_id):
    """Get processing status"""
    status = processing_status.get(task_id, {"step": "not_found", "progress": 0})
    return jsonify(status)

@app.route('/download/<task_id>')
def download_file(task_id):
    """Download processed file"""
    
    status = processing_status.get(task_id, {})
    
    if status.get("step") != "complete":
        return jsonify({'error': 'Processing not complete'}), 400
    
    output_path = status.get("output_path")
    if not output_path or not os.path.exists(output_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"processed_{task_id}.png",
        mimetype='image/png'
    )

@app.route('/cleanup/<task_id>', methods=['POST'])
def cleanup_task(task_id):
    """Clean up processed files"""
    try:
        status = processing_status.get(task_id, {})
        output_path = status.get("output_path")
        
        if output_path and os.path.exists(output_path):
            os.unlink(output_path)
        
        # Remove from status dict
        if task_id in processing_status:
            del processing_status[task_id]
        
        return jsonify({'status': 'cleaned'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 ImageBoost - 4x Upscale + BG Removal</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #ff6b6b, #ffa500);
            padding: 30px;
            text-align: center;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.2em;
        }
        
        .content {
            padding: 40px;
        }
        
        .drop-zone {
            border: 3px dashed #667eea;
            border-radius: 12px;
            padding: 60px 20px;
            text-align: center;
            background: #f8f9ff;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 30px;
        }
        
        .drop-zone:hover {
            border-color: #ff6b6b;
            background: #fff5f5;
        }
        
        .drop-zone.dragover {
            border-color: #ffa500;
            background: #fffbf0;
            transform: scale(1.02);
        }
        
        .drop-icon {
            font-size: 3em;
            margin-bottom: 15px;
            opacity: 0.7;
        }
        
        .drop-text {
            font-size: 1.3em;
            color: #667eea;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .drop-hint {
            color: #666;
            font-size: 0.95em;
        }
        
        .file-input {
            display: none;
        }
        
        .processing-card {
            background: #f8f9ff;
            border-radius: 12px;
            padding: 30px;
            margin-top: 20px;
            display: none;
        }
        
        .progress-container {
            background: #e1e5fe;
            border-radius: 20px;
            height: 8px;
            margin: 20px 0;
            overflow: hidden;
        }
        
        .progress-bar {
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%;
            width: 0%;
            border-radius: 20px;
            transition: width 0.5s ease;
        }
        
        .status-text {
            text-align: center;
            color: #667eea;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .download-btn {
            background: linear-gradient(135deg, #4caf50, #45a049);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            display: none;
            margin: 20px auto 0;
            transition: transform 0.2s ease;
        }
        
        .download-btn:hover {
            transform: translateY(-2px);
        }
        
        .error-card {
            background: #ffebee;
            border: 1px solid #f44336;
            border-radius: 8px;
            padding: 20px;
            color: #c62828;
            margin-top: 20px;
            display: none;
        }
        
        .supported-formats {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 0.9em;
        }
        
        .format-tag {
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 8px;
            border-radius: 4px;
            margin: 0 2px;
            font-weight: 500;
        }
        
        .version-info {
            background: #fff3e0;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            font-size: 0.9em;
            color: #e65100;
        }
        
        .features {
            background: #f1f8e9;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            font-size: 0.9em;
            color: #33691e;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ImageBoost</h1>
            <p>4x Smart Upscale + Background Processing</p>
        </div>
        
        <div class="content">
            <div class="drop-zone" id="dropZone">
                <div class="drop-icon">📁</div>
                <div class="drop-text">Drop your image here</div>
                <div class="drop-hint">or click to select</div>
            </div>
            
            <input type="file" id="fileInput" class="file-input" accept=".jpg,.jpeg,.png,.webp,.avif" />
            
            <div class="supported-formats">
                <strong>Supported formats:</strong>
                <span class="format-tag">JPG</span>
                <span class="format-tag">JPEG</span>
                <span class="format-tag">PNG</span>
                <span class="format-tag">WEBP</span>
                <span class="format-tag">AVIF</span>
            </div>
            
            <div class="features">
                <strong>✨ Features:</strong> 
                Smart 4x upscaling with noise reduction, edge enhancement, and intelligent background processing.
            </div>
            
            <div class="version-info">
                <strong>📝 Fallback Mode:</strong> Using advanced Pillow upscaling + smart background detection.
                Optimized for compatibility and reliability.
            </div>
            
            <div class="processing-card" id="processingCard">
                <div class="status-text" id="statusText">Preparing...</div>
                <div class="progress-container">
                    <div class="progress-bar" id="progressBar"></div>
                </div>
                <button class="download-btn" id="downloadBtn">📥 Download Processed Image</button>
            </div>
            
            <div class="error-card" id="errorCard">
                <strong>Error:</strong> <span id="errorText"></span>
            </div>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const processingCard = document.getElementById('processingCard');
        const statusText = document.getElementById('statusText');
        const progressBar = document.getElementById('progressBar');
        const downloadBtn = document.getElementById('downloadBtn');
        const errorCard = document.getElementById('errorCard');
        const errorText = document.getElementById('errorText');
        
        let currentTaskId = null;
        let statusInterval = null;
        
        // Drag and drop handlers
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', handleDragOver);
        dropZone.addEventListener('dragleave', handleDragLeave);
        dropZone.addEventListener('drop', handleDrop);
        fileInput.addEventListener('change', handleFileSelect);
        downloadBtn.addEventListener('click', handleDownload);
        
        function handleDragOver(e) {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }
        
        function handleDragLeave(e) {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }
        
        function handleDrop(e) {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                processFile(files[0]);
            }
        }
        
        function handleFileSelect(e) {
            if (e.target.files.length > 0) {
                processFile(e.target.files[0]);
            }
        }
        
        function showError(message) {
            errorText.textContent = message;
            errorCard.style.display = 'block';
            processingCard.style.display = 'none';
        }
        
        function hideError() {
            errorCard.style.display = 'none';
        }
        
        async function processFile(file) {
            hideError();
            
            // Validate file type
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
            if (!validTypes.includes(file.type) && !file.name.toLowerCase().endsWith('.avif')) {
                showError('Please select a valid image file (JPG, PNG, WEBP, AVIF)');
                return;
            }
            
            // Validate file size (max 50MB)
            if (file.size > 50 * 1024 * 1024) {
                showError('File too large. Please select an image under 50MB.');
                return;
            }
            
            // Show processing card
            processingCard.style.display = 'block';
            downloadBtn.style.display = 'none';
            
            // Upload file
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                statusText.textContent = 'Uploading...';
                progressBar.style.width = '10%';
                
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.error || 'Upload failed');
                }
                
                currentTaskId = result.task_id;
                
                // Start polling for status
                statusInterval = setInterval(checkStatus, 1000);
                
            } catch (error) {
                showError('Upload failed: ' + error.message);
            }
        }
        
        async function checkStatus() {
            if (!currentTaskId) return;
            
            try {
                const response = await fetch(`/status/${currentTaskId}`);
                const status = await response.json();
                
                progressBar.style.width = status.progress + '%';
                
                switch (status.step) {
                    case 'starting':
                        statusText.textContent = 'Starting processing...';
                        break;
                    case 'upscaling':
                        statusText.textContent = '🔍 Smart upscaling 4x...';
                        break;
                    case 'removing_bg':
                        statusText.textContent = '🎭 Processing background...';
                        break;
                    case 'saving':
                        statusText.textContent = '💾 Saving enhanced image...';
                        break;
                    case 'complete':
                        statusText.textContent = '✅ Processing complete!';
                        downloadBtn.style.display = 'block';
                        clearInterval(statusInterval);
                        break;
                    case 'error':
                        showError('Processing failed: ' + status.error);
                        clearInterval(statusInterval);
                        break;
                    default:
                        statusText.textContent = 'Processing...';
                }
                
            } catch (error) {
                showError('Status check failed: ' + error.message);
                clearInterval(statusInterval);
            }
        }
        
        async function handleDownload() {
            if (!currentTaskId) return;
            
            try {
                // Create download link
                const link = document.createElement('a');
                link.href = `/download/${currentTaskId}`;
                link.download = `imageBoost_processed.png`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                // Clean up after a delay
                setTimeout(async () => {
                    try {
                        await fetch(`/cleanup/${currentTaskId}`, { method: 'POST' });
                    } catch (e) {
                        console.log('Cleanup failed:', e);
                    }
                }, 5000);
                
            } catch (error) {
                showError('Download failed: ' + error.message);
            }
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    logger.info("🚀 Starting ImageBoost server (Fallback Mode)...")
    
    logger.info("🌐 Server running at http://localhost:8587")
    logger.info("📁 Upload dir: " + str(UPLOAD_DIR))
    logger.info("📁 Output dir: " + str(OUTPUT_DIR))
    logger.info("✨ Using smart upscaling + intelligent background processing")
    
    app.run(host='0.0.0.0', port=8587, debug=True, threaded=True)