#!/bin/bash

echo "🚀 Setting up ImageBoost (Simplified)..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install basic dependencies first
echo "📚 Installing core dependencies..."
pip install flask flask-cors
pip install pillow
pip install opencv-python
pip install numpy
pip install rembg

echo "✅ Basic setup complete!"
echo ""
echo "🚀 To start ImageBoost:"
echo "  cd ~/clawd/image-boost"
echo "  source venv/bin/activate"
echo "  python3 server.py"
echo ""
echo "🌐 Then open: http://localhost:8587"
echo ""
echo "Note: Real-ESRGAN will fall back to basic upscaling if not available."