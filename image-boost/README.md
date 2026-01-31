# 🚀 ImageBoost

**4x Smart Upscale + AI Background Removal**

A drag-and-drop web tool that upscales images by 4x and removes backgrounds using intelligent color analysis.

## ✨ Features

- **4x Smart Upscaling**: LANCZOS resampling with sharpening and contrast enhancement
- **AI Background Removal**: Intelligent edge color detection with smooth alpha blending
- **Drag & Drop Interface**: Modern, responsive web UI
- **Multiple Formats**: Supports JPG, JPEG, PNG, WEBP, AVIF
- **Real-time Progress**: Live status updates during processing
- **Zero API Costs**: Pure local processing using Pillow
- **🔥 BULK PROCESSING**: Process multiple images simultaneously with ZIP download

## 🚀 Quick Start

1. **Setup** (one time):
   ```bash
   cd ~/clawd/image-boost
   ./setup_simple.sh
   ```

2. **Start server**:
   ```bash
   # Single image mode
   ./start_pillow.sh
   
   # OR bulk processing mode
   ./start_bulk.sh
   ```

3. **Open**: http://localhost:8587

## 🔥 Bulk Mode Features

- **Multiple file upload**: Select or drop multiple images at once
- **Individual progress tracking**: See progress for each file separately  
- **Batch status**: Overall batch completion tracking
- **ZIP download**: Download all processed images as a single ZIP file
- **Memory efficient**: Sequential processing to handle large batches
- **Error handling**: Continue processing even if some files fail

## 📁 Project Structure

```
image-boost/
├── server_pillow_only.py    # Single image mode (original)
├── server_bulk.py           # Bulk processing mode (NEW) 🔥
├── server_simple.py         # REMBG version (if available)
├── server_fallback.py       # OpenCV version (compatibility issues)
├── setup_simple.sh          # Setup script
├── start_pillow.sh          # Start single mode
├── start_bulk.sh            # Start bulk mode (NEW) 🔥
├── uploads/                 # Temporary uploads
├── outputs/                 # Processed images
└── venv/                    # Virtual environment
```

## 🎯 Two Modes Available

### 1. Single Image Mode (`./start_pillow.sh`)
- **Best for**: Quick single image processing
- **Interface**: Simple drag & drop for one image
- **Processing**: Immediate processing and download
- **Use case**: Quick edits, testing, single images

### 2. Bulk Mode (`./start_bulk.sh`) 🔥
- **Best for**: Processing multiple images at once
- **Interface**: Multi-select file upload with progress tracking
- **Processing**: Batch processing with individual file progress
- **Output**: Download all as ZIP or individual files
- **Use case**: Batch editing, workflow automation, multiple images

## 🎯 Processing Pipeline

1. **Upload**: Validates file type and size
2. **Enhancement**: Sharpens and enhances original image
3. **Upscaling**: 4x LANCZOS resize with post-processing
4. **Background Detection**: Analyzes edge pixels for background color
5. **Smart Masking**: Creates smooth alpha mask with gradual falloff
6. **Export**: Saves as PNG with transparent background

## ⏱️ Performance

- **Small images** (<1MB): ~5-15 seconds
- **Medium images** (1-5MB): ~10-30 seconds  
- **Large images** (5MB+): ~20-60 seconds

## 🔧 Technical Details

- **Backend**: Flask + Pure Pillow processing
- **Upscaling**: LANCZOS resampling with UnsharpMask filter
- **Background Removal**: Color distance analysis with tolerance thresholds
- **Edge Detection**: Smart edge pixel sampling for background color detection
- **Alpha Blending**: Gradual transparency for smooth results

## 💡 Usage Tips

- **Best results**: Images with solid/simple backgrounds
- **File limit**: 50MB maximum
- **Optimal input**: High contrast between subject and background
- **Format**: Always outputs PNG with transparency

## 🛠️ Development

To modify the processing algorithm:
1. Edit `server_pillow_only.py`
2. Modify functions: `smart_upscale()`, `detect_background_color()`, `remove_background_smart()`
3. Restart server to test changes

## 📊 Cost Analysis

- **Per image**: $0.00 (local processing)
- **Server hosting**: Free (localhost)
- **Dependencies**: Free open source
- **API calls**: None

**Total cost**: $0/month

---

Built in 3 hours using pure Python + Pillow for maximum compatibility and zero ongoing costs.