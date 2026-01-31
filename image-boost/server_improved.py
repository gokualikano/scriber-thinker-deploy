#!/usr/bin/env python3
"""
ImageBoost - Improved version with better color preservation
4x Smart Upscale + Gentle Background Removal (Individual Downloads)
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
batch_status = {}

def enhance_image(image):
    """Gentle enhancement that preserves colors"""
    # Mild sharpening only
    enhancer = ImageEnhance.Sharpness(image)
    enhanced = enhancer.enhance(1.15)  # Reduced from 1.3
    
    # Very mild contrast boost
    enhancer = ImageEnhance.Contrast(enhanced)
    enhanced = enhancer.enhance(1.05)  # Reduced from 1.2
    
    # Gentle unsharp mask
    enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=0.8, percent=100, threshold=5))
    
    return enhanced

def smart_upscale(image, scale=4):
    """Color-preserving upscaling"""
    # Store original color profile
    if hasattr(image, 'info') and 'icc_profile' in image.info:
        icc_profile = image.info['icc_profile']
    else:
        icc_profile = None
    
    # Gentle enhancement
    enhanced = enhance_image(image)
    
    width, height = enhanced.size
    new_size = (width * scale, height * scale)
    
    # High quality upscaling
    upscaled = enhanced.resize(new_size, Image.Resampling.LANCZOS)
    
    # Restore color profile if available
    if icc_profile:
        upscaled.info['icc_profile'] = icc_profile
    
    # Very gentle post-sharpening
    enhancer = ImageEnhance.Sharpness(upscaled)
    upscaled = enhancer.enhance(1.05)  # Reduced from 1.1
    
    return upscaled

def get_corner_pixels(image, sample_size=20):
    """Get pixels from corners (most likely background)"""
    width, height = image.size
    corner_pixels = []
    
    # Top-left corner
    for x in range(min(sample_size, width)):
        for y in range(min(sample_size, height)):
            corner_pixels.append(image.getpixel((x, y)))
    
    # Top-right corner
    for x in range(max(0, width - sample_size), width):
        for y in range(min(sample_size, height)):
            corner_pixels.append(image.getpixel((x, y)))
    
    # Bottom-left corner
    for x in range(min(sample_size, width)):
        for y in range(max(0, height - sample_size), height):
            corner_pixels.append(image.getpixel((x, y)))
    
    # Bottom-right corner
    for x in range(max(0, width - sample_size), width):
        for y in range(max(0, height - sample_size), height):
            corner_pixels.append(image.getpixel((x, y)))
    
    return corner_pixels

def detect_background_color_gentle(image):
    """More accurate background detection using corners"""
    corner_pixels = get_corner_pixels(image, sample_size=15)
    
    if not corner_pixels:
        return (255, 255, 255)
    
    # Convert to RGB if needed
    if image.mode == 'RGBA':
        rgb_pixels = [(r, g, b) for r, g, b, a in corner_pixels]
    else:
        rgb_pixels = corner_pixels
    
    if rgb_pixels:
        # Use most common corner color (more likely to be background)
        most_common = Counter(rgb_pixels).most_common(1)[0][0]
        return most_common
    
    return (255, 255, 255)

def create_gentle_mask(image, bg_color, tolerance=50):
    """Create gentle mask that preserves subject colors"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    width, height = image.size
    mask_data = []
    
    for y in range(height):
        for x in range(width):
            pixel = image.getpixel((x, y))
            r, g, b = pixel[:3]
            
            # Calculate color distance using weighted euclidean
            # Weight red/blue more than green (human perception)
            distance = ((r - bg_color[0]) * 0.3)**2 + ((g - bg_color[1]) * 0.59)**2 + ((b - bg_color[2]) * 0.11)**2
            distance = distance**0.5
            
            # More conservative transparency
            if distance <= tolerance * 0.6:  # Very similar to background
                mask_data.append(0)  # Full transparency
            elif distance <= tolerance:  # Somewhat similar
                # Gentler falloff
                alpha = min(255, max(30, int((distance - tolerance * 0.6) * 3)))
                mask_data.append(alpha)
            else:  # Clearly subject
                mask_data.append(255)  # Keep fully opaque
    
    # Create mask image
    mask = Image.new('L', (width, height))
    mask.putdata(mask_data)
    
    # Very gentle blur to smooth edges
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    return mask

def remove_background_gentle(image):
    """Gentle background removal that preserves subject colors"""
    original_mode = image.mode
    
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Detect background color from corners
    bg_color = detect_background_color_gentle(image)
    logger.info(f"Detected background color: {bg_color}")
    
    # Create gentle mask with higher tolerance
    mask = create_gentle_mask(image, bg_color, tolerance=60)  # Increased tolerance
    
    # Apply mask
    image.putalpha(mask)
    
    return image

def process_single_image(file_info, batch_id):
    """Process a single image with gentle settings"""
    file_id = file_info['id']
    input_path = file_info['input_path']
    output_path = file_info['output_path']
    filename = file_info['filename']
    
    try:
        # Update status
        processing_status[file_id] = {"step": "starting", "progress": 0, "filename": filename}
        
        # Load image
        logger.info(f"📂 Processing: {filename}")
        image = Image.open(input_path)
        
        processing_status[file_id] = {"step": "upscaling", "progress": 20, "filename": filename}
        
        # Gentle upscale 4x
        upscaled = smart_upscale(image, scale=4)
        
        processing_status[file_id] = {"step": "removing_bg", "progress": 70, "filename": filename}
        
        # Gentle background removal
        final_image = remove_background_gentle(upscaled)
        
        processing_status[file_id] = {"step": "saving", "progress": 90, "filename": filename}
        
        # Save final image
        final_image.save(output_path, format='PNG', optimize=True)
        
        processing_status[file_id] = {
            "step": "complete", 
            "progress": 100, 
            "filename": filename,
            "output_path": str(output_path)
        }
        
        # Clean up input file
        os.unlink(input_path)
        
        logger.info(f"✅ Completed: {filename}")
        
    except Exception as e:
        logger.error(f"❌ Error processing {filename}: {e}")
        processing_status[file_id] = {
            "step": "error", 
            "progress": 0, 
            "filename": filename,
            "error": str(e)
        }

def process_batch_background(batch_id, files_info):
    """Background batch processing function"""
    global batch_status
    
    try:
        batch_status[batch_id] = {
            "step": "processing",
            "total_files": len(files_info),
            "completed": 0,
            "files": {}
        }
        
        # Process files sequentially
        for file_info in files_info:
            file_id = file_info['id']
            batch_status[batch_id]["files"][file_id] = {"status": "processing"}
            
            # Process single image
            process_single_image(file_info, batch_id)
            
            # Update batch progress
            if processing_status[file_id]["step"] == "complete":
                batch_status[batch_id]["completed"] += 1
                batch_status[batch_id]["files"][file_id] = {"status": "complete"}
            else:
                batch_status[batch_id]["files"][file_id] = {"status": "error"}
        
        # Mark batch as complete
        batch_status[batch_id]["step"] = "complete"
        
        logger.info(f"✅ Batch {batch_id} complete: {batch_status[batch_id]['completed']}/{batch_status[batch_id]['total_files']}")
        
    except Exception as e:
        logger.error(f"❌ Batch processing error: {e}")
        batch_status[batch_id] = {"step": "error", "error": str(e)}

@app.route('/')
def index():
    """Main interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle multiple file upload and start processing"""
    
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('files')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400
    
    # Validate files
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.avif'}
    valid_files = []
    
    for file in files:
        if file.filename == '':
            continue
            
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Unsupported file type: {file_ext}'}), 400
            
        valid_files.append(file)
    
    if not valid_files:
        return jsonify({'error': 'No valid files found'}), 400
    
    try:
        # Generate batch ID
        batch_id = str(uuid.uuid4())
        
        # Prepare file info
        files_info = []
        
        for file in valid_files:
            file_id = str(uuid.uuid4())
            file_ext = Path(file.filename).suffix.lower()
            
            input_filename = f"{file_id}_input{file_ext}"
            output_filename = f"{file_id}_processed.png"
            
            input_path = UPLOAD_DIR / input_filename
            output_path = OUTPUT_DIR / output_filename
            
            # Save uploaded file
            file.save(input_path)
            
            files_info.append({
                'id': file_id,
                'filename': file.filename,
                'input_path': input_path,
                'output_path': output_path
            })
        
        # Start background processing
        thread = threading.Thread(
            target=process_batch_background,
            args=(batch_id, files_info)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'batch_id': batch_id,
            'file_count': len(files_info),
            'file_ids': [f['id'] for f in files_info],
            'status': 'processing_started'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/batch-status/<batch_id>')
def get_batch_status(batch_id):
    """Get batch processing status"""
    batch = batch_status.get(batch_id, {"step": "not_found"})
    
    # Add individual file statuses
    if batch.get("step") == "processing" or batch.get("step") == "complete":
        file_statuses = {}
        for file_id in batch.get("files", {}):
            file_statuses[file_id] = processing_status.get(file_id, {"step": "waiting", "progress": 0})
        batch["file_statuses"] = file_statuses
    
    return jsonify(batch)

@app.route('/download/<file_id>')
def download_single_file(file_id):
    """Download single processed file"""
    
    status = processing_status.get(file_id, {})
    
    if status.get("step") != "complete":
        return jsonify({'error': 'Processing not complete'}), 400
    
    output_path = status.get("output_path")
    filename = status.get("filename", "processed")
    
    if not output_path or not os.path.exists(output_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Create download name
    base_name = Path(filename).stem
    download_name = f"{base_name}_processed.png"
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=download_name,
        mimetype='image/png'
    )

@app.route('/cleanup-batch/<batch_id>', methods=['POST'])
def cleanup_batch(batch_id):
    """Clean up batch files"""
    try:
        batch = batch_status.get(batch_id, {})
        cleaned_count = 0
        
        for file_id in batch.get("files", {}):
            status = processing_status.get(file_id, {})
            output_path = status.get("output_path")
            
            if output_path and os.path.exists(output_path):
                os.unlink(output_path)
                cleaned_count += 1
            
            # Remove from status dict
            if file_id in processing_status:
                del processing_status[file_id]
        
        # Remove batch status
        if batch_id in batch_status:
            del batch_status[batch_id]
        
        return jsonify({'status': 'cleaned', 'files_cleaned': cleaned_count})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# HTML Template with individual downloads
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎨 ImageBoost Pro - Color-Preserving Upscale & Background Removal</title>
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
            max-width: 900px;
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
        
        .batch-info {
            background: #e8f5e8;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            display: none;
        }
        
        .file-list {
            margin-top: 20px;
            display: none;
        }
        
        .file-item {
            background: #f8f9ff;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .file-item.complete {
            border-left-color: #4caf50;
            background: #f1f8e9;
        }
        
        .file-item.error {
            border-left-color: #f44336;
            background: #ffebee;
        }
        
        .file-details {
            flex-grow: 1;
        }
        
        .file-name {
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .file-progress {
            background: #e1e5fe;
            border-radius: 10px;
            height: 6px;
            margin: 10px 0;
            overflow: hidden;
            width: 300px;
        }
        
        .file-progress-bar {
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%;
            width: 0%;
            border-radius: 10px;
            transition: width 0.5s ease;
        }
        
        .file-status {
            font-size: 0.9em;
            color: #666;
        }
        
        .file-actions {
            margin-left: 20px;
        }
        
        .download-btn {
            background: linear-gradient(135deg, #4caf50, #45a049);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
            display: none;
        }
        
        .download-btn:hover {
            transform: translateY(-1px);
        }
        
        .download-btn.visible {
            display: inline-block;
        }
        
        .cleanup-section {
            background: #f5f5f5;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            text-align: center;
            display: none;
        }
        
        .cleanup-btn {
            background: linear-gradient(135deg, #757575, #616161);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        
        .cleanup-btn:hover {
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
            background: #e8f5e8;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            font-size: 0.9em;
            color: #2e7d32;
        }
        
        .pro-badge {
            background: #4caf50;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 ImageBoost <span class="pro-badge">PRO</span></h1>
            <p>Color-Preserving Upscale + Gentle Background Removal</p>
        </div>
        
        <div class="content">
            <div class="drop-zone" id="dropZone">
                <div class="drop-icon">📁</div>
                <div class="drop-text">Drop multiple images here</div>
                <div class="drop-hint">or click to select multiple files</div>
            </div>
            
            <input type="file" id="fileInput" class="file-input" accept=".jpg,.jpeg,.png,.webp,.avif" multiple />
            
            <div class="supported-formats">
                <strong>Supported formats:</strong>
                <span class="format-tag">JPG</span>
                <span class="format-tag">JPEG</span>
                <span class="format-tag">PNG</span>
                <span class="format-tag">WEBP</span>
                <span class="format-tag">AVIF</span>
            </div>
            
            <div class="features">
                <strong>✨ Pro Features:</strong> 
                • Gentle 4x upscaling preserves original colors
                • Corner-based background detection for accuracy
                • Individual download for each processed image
                • Smart tolerance reduces color shifting
            </div>
            
            <div class="batch-info" id="batchInfo">
                <strong>📦 Processing Status:</strong> <span id="batchText"></span>
            </div>
            
            <div class="file-list" id="fileList"></div>
            
            <div class="cleanup-section" id="cleanupSection">
                <button class="cleanup-btn" id="cleanupBtn">🗑️ Clean Up All Files</button>
                <p style="margin-top: 10px; color: #666; font-size: 0.9em;">Remove all processed files from server</p>
            </div>
            
            <div class="error-card" id="errorCard">
                <strong>Error:</strong> <span id="errorText"></span>
            </div>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const batchInfo = document.getElementById('batchInfo');
        const batchText = document.getElementById('batchText');
        const fileList = document.getElementById('fileList');
        const cleanupSection = document.getElementById('cleanupSection');
        const cleanupBtn = document.getElementById('cleanupBtn');
        const errorCard = document.getElementById('errorCard');
        const errorText = document.getElementById('errorText');
        
        let currentBatchId = null;
        let statusInterval = null;
        let fileStatuses = {};
        
        // Drag and drop handlers
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', handleDragOver);
        dropZone.addEventListener('dragleave', handleDragLeave);
        dropZone.addEventListener('drop', handleDrop);
        fileInput.addEventListener('change', handleFileSelect);
        cleanupBtn.addEventListener('click', handleCleanup);
        
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
            
            const files = Array.from(e.dataTransfer.files);
            if (files.length > 0) {
                processFiles(files);
            }
        }
        
        function handleFileSelect(e) {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                processFiles(files);
            }
        }
        
        function showError(message) {
            errorText.textContent = message;
            errorCard.style.display = 'block';
        }
        
        function hideError() {
            errorCard.style.display = 'none';
        }
        
        function createFileItem(fileId, filename) {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.id = `file-${fileId}`;
            
            item.innerHTML = `
                <div class="file-details">
                    <div class="file-name">${filename}</div>
                    <div class="file-progress">
                        <div class="file-progress-bar" id="progress-${fileId}"></div>
                    </div>
                    <div class="file-status" id="status-${fileId}">Waiting...</div>
                </div>
                <div class="file-actions">
                    <button class="download-btn" id="download-${fileId}" onclick="downloadFile('${fileId}')">
                        📥 Download
                    </button>
                </div>
            `;
            
            return item;
        }
        
        async function processFiles(files) {
            hideError();
            
            // Validate files
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
            const validFiles = files.filter(file => 
                validTypes.includes(file.type) || file.name.toLowerCase().endsWith('.avif')
            );
            
            if (validFiles.length === 0) {
                showError('No valid image files selected');
                return;
            }
            
            // Show batch info
            batchInfo.style.display = 'block';
            batchText.textContent = `Processing ${validFiles.length} images...`;
            
            // Create file list
            fileList.innerHTML = '';
            fileList.style.display = 'block';
            cleanupSection.style.display = 'none';
            
            // Upload files
            const formData = new FormData();
            validFiles.forEach(file => {
                formData.append('files', file);
            });
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.error || 'Upload failed');
                }
                
                currentBatchId = result.batch_id;
                const fileIds = result.file_ids;
                
                // Create file items
                validFiles.forEach((file, index) => {
                    const fileId = fileIds[index];
                    const item = createFileItem(fileId, file.name);
                    fileList.appendChild(item);
                    fileStatuses[fileId] = { filename: file.name };
                });
                
                // Start polling for status
                statusInterval = setInterval(checkBatchStatus, 1000);
                
            } catch (error) {
                showError('Upload failed: ' + error.message);
            }
        }
        
        async function checkBatchStatus() {
            if (!currentBatchId) return;
            
            try {
                const response = await fetch(`/batch-status/${currentBatchId}`);
                const status = await response.json();
                
                if (status.step === 'complete') {
                    batchText.textContent = `✅ Batch complete: ${status.completed}/${status.total_files} images processed`;
                    cleanupSection.style.display = 'block';
                    clearInterval(statusInterval);
                } else if (status.step === 'error') {
                    showError('Batch processing failed: ' + status.error);
                    clearInterval(statusInterval);
                    return;
                }
                
                // Update individual file statuses
                if (status.file_statuses) {
                    Object.entries(status.file_statuses).forEach(([fileId, fileStatus]) => {
                        const progressBar = document.getElementById(`progress-${fileId}`);
                        const statusText = document.getElementById(`status-${fileId}`);
                        const fileItem = document.getElementById(`file-${fileId}`);
                        const downloadBtn = document.getElementById(`download-${fileId}`);
                        
                        if (progressBar && statusText && fileItem) {
                            progressBar.style.width = fileStatus.progress + '%';
                            
                            switch (fileStatus.step) {
                                case 'starting':
                                    statusText.textContent = 'Starting...';
                                    break;
                                case 'upscaling':
                                    statusText.textContent = '🔍 Gentle upscaling 4x...';
                                    break;
                                case 'removing_bg':
                                    statusText.textContent = '🎨 Preserving colors & removing background...';
                                    break;
                                case 'saving':
                                    statusText.textContent = '💾 Saving enhanced image...';
                                    break;
                                case 'complete':
                                    statusText.textContent = '✅ Ready to download';
                                    fileItem.className = 'file-item complete';
                                    downloadBtn.classList.add('visible');
                                    break;
                                case 'error':
                                    statusText.textContent = '❌ Error: ' + fileStatus.error;
                                    fileItem.className = 'file-item error';
                                    break;
                                default:
                                    statusText.textContent = 'Waiting...';
                            }
                        }
                    });
                }
                
            } catch (error) {
                showError('Status check failed: ' + error.message);
                clearInterval(statusInterval);
            }
        }
        
        async function downloadFile(fileId) {
            try {
                const link = document.createElement('a');
                link.href = `/download/${fileId}`;
                link.download = `processed_image.png`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
            } catch (error) {
                showError('Download failed: ' + error.message);
            }
        }
        
        async function handleCleanup() {
            if (!currentBatchId) return;
            
            try {
                await fetch(`/cleanup-batch/${currentBatchId}`, { method: 'POST' });
                
                // Reset UI
                fileList.innerHTML = '';
                fileList.style.display = 'none';
                batchInfo.style.display = 'none';
                cleanupSection.style.display = 'none';
                currentBatchId = null;
                fileStatuses = {};
                
            } catch (error) {
                showError('Cleanup failed: ' + error.message);
            }
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    logger.info("🎨 Starting ImageBoost PRO server (Color-Preserving Mode)...")
    
    logger.info("🌐 Server running at http://localhost:8587")
    logger.info("📁 Upload dir: " + str(UPLOAD_DIR))  
    logger.info("📁 Output dir: " + str(OUTPUT_DIR))
    logger.info("✨ Using gentle processing with color preservation")
    
    app.run(host='0.0.0.0', port=8587, debug=False, threaded=True)