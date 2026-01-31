#!/bin/bash

echo "🚀 Setting up ImageBoost..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install pillow==10.2.0
pip install opencv-python==4.9.0.80
pip install numpy==1.24.3
pip install rembg==2.0.50

# Install Real-ESRGAN (separate due to dependencies)
echo "🔍 Installing Real-ESRGAN..."
pip install basicsr==1.4.2
pip install realesrgan==0.3.0
pip install gfpgan==1.3.8

# Install PyTorch (CPU version for Mac compatibility)
echo "🧠 Installing PyTorch..."
pip install torch==2.1.0 torchvision==0.16.0

echo "✅ Setup complete!"
echo ""
echo "🚀 To start ImageBoost:"
echo "  cd ~/clawd/image-boost"
echo "  source venv/bin/activate"
echo "  python3 server.py"
echo ""
echo "🌐 Then open: http://localhost:8587"