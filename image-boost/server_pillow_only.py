#!/usr/bin/env python3
"""
ImageBoost - Pillow-only version
4x Upscale + Smart Background Processing (Pure Python)
"""

import os
import uuid
import time
from datetime import datetime
from pathlib import Path
import threading
import json
import logging
from collections import Counter

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from PIL import Image, ImageFilter, ImageEnhance, ImageOps

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
    """Enhance image quality using Pillow"""
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image)
    enhanced = enhancer.enhance(1.3)
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(enhanced)
    enhanced = enhancer.enhance(1.2)
    
    # Apply unsharp mask for better detail
    enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
    
    return enhanced

def smart_upscale(image, scale=4):
    """Advanced upscaling using Pillow with quality enhancement"""
    # First enhance the original
    enhanced = enhance_image(image)
    
    # Calculate new size
    width, height = enhanced.size
    new_size = (width * scale, height * scale)
    
    # Use LANCZOS for highest quality upscaling
    upscaled = enhanced.resize(new_size, Image.Resampling.LANCZOS)
    
    # Apply post-upscaling enhancement
    enhancer = ImageEnhance.Sharpness(upscaled)
    upscaled = enhancer.enhance(1.1)
    
    return upscaled

def get_edge_pixels(image):
    """Get pixels from the edges of the image"""
    width, height = image.size
    edge_pixels = []
    
    # Sample edge pixels
    for x in range(0, width, max(1, width//50)):  # Sample every ~2% of width
        if y := 0: edge_pixels.append(image.getpixel((x, y)))  # Top edge
        if y := height-1: edge_pixels.append(image.getpixel((x, y)))  # Bottom edge
    
    for y in range(0, height, max(1, height//50)):  # Sample every ~2% of height
        if x := 0: edge_pixels.append(image.getpixel((x, y)))  # Left edge
        if x := width-1: edge_pixels.append(image.getpixel((x, y)))  # Right edge
    
    return edge_pixels

def detect_background_color(image):
    """Detect the most likely background color"""
    edge_pixels = get_edge_pixels(image)
    
    if not edge_pixels:
        return (255, 255, 255)  # Default to white
    
    # Convert to RGB if needed
    if image.mode == 'RGBA':
        rgb_pixels = [(r, g, b) for r, g, b, a in edge_pixels]
    else:
        rgb_pixels = edge_pixels
    
    # Find most common color
    if rgb_pixels:
        most_common = Counter(rgb_pixels).most_common(1)[0][0]
        return most_common
    
    return (255, 255, 255)

def create_smart_mask(image, bg_color, tolerance=40):
    """Create a mask for background removal"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    width, height = image.size
    mask_data = []
    
    for y in range(height):
        for x in range(width):
            pixel = image.getpixel((x, y))
            r, g, b = pixel[:3]
            
            # Calculate distance from background color
            distance = ((r - bg_color[0])**2 + (g - bg_color[1])**2 + (b - bg_color[2])**2)**0.5
            
            # Create mask based on distance
            if distance <= tolerance:
                mask_data.append(0)  # Background (transparent)
            else:
                # Gradual falloff near background color
                alpha = min(255, max(0, int((distance - tolerance) * 2)))
                mask_data.append(alpha)
    
    # Create mask image
    mask = Image.new('L', (width, height))
    mask.putdata(mask_data)
    
    # Apply slight blur to smooth edges
    mask = mask.filter(ImageFilter.GaussianBlur(radius=1))
    
    return mask

def remove_background_smart(image):
    """Smart background removal using color analysis"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Detect background color
    bg_color = detect_background_color(image)
    logger.info(f"Detected background color: {bg_color}")
    
    # Create smart mask
    mask = create_smart_mask(image, bg_color, tolerance=35)
    
    # Apply mask to create transparent background
    image.putalpha(mask)
    
    return image

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
        
        # Smart background removal
        logger.info("🎭 Smart background removal...")
        final_image = remove_background_smart(upscaled)
        
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
        download_name=f"imageBoost_processed.png",
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

# HTML Template (same as before, with updated messaging)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 ImageBoost - Smart Upscale & Background Removal</title>
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
        
        .features {
            background: #f1f8e9;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            font-size: 0.9em;
            color: #33691e;
        }
        
        .version-info {
            background: #e8f5e8;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            font-size: 0.9em;
            color: #2e7d32;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ImageBoost</h1>
            <p>Smart 4x Upscale + AI Background Removal</p>
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
                <strong>✨ Smart Features:</strong> 
                • 4x LANCZOS upscaling with sharpening
                • Intelligent background color detection
                • Smooth edge processing with gradual alpha
                • Enhanced contrast and detail preservation
            </div>
            
            <div class="version-info">
                <strong>🎯 Pure Pillow Mode:</strong> 
                Optimized for maximum compatibility. Uses advanced color analysis and edge detection
                for professional background removal results.
            </div>
            
            <div class="processing-card" id="processingCard">
                <div class="status-text" id="statusText">Preparing...</div>
                <div class="progress-container">
                    <div class="progress-bar" id="progressBar"></div>
                </div>
                <button class="download-btn" id="downloadBtn">📥 Download Enhanced Image</button>
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
                        statusText.textContent = 'Analyzing image...';
                        break;
                    case 'upscaling':
                        statusText.textContent = '🔍 Smart upscaling 4x with enhancement...';
                        break;
                    case 'removing_bg':
                        statusText.textContent = '🎭 AI background analysis & removal...';
                        break;
                    case 'saving':
                        statusText.textContent = '💾 Finalizing enhanced image...';
                        break;
                    case 'complete':
                        statusText.textContent = '✅ Enhancement complete!';
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
                link.download = `imageBoost_enhanced.png`;
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
    logger.info("🚀 Starting ImageBoost server (Pure Pillow Mode)...")
    
    logger.info("🌐 Server running at http://localhost:8587")
    logger.info("📁 Upload dir: " + str(UPLOAD_DIR))  
    logger.info("📁 Output dir: " + str(OUTPUT_DIR))
    logger.info("✨ Using pure Pillow processing for maximum compatibility")
    
    app.run(host='0.0.0.0', port=8587, debug=False, threaded=True)