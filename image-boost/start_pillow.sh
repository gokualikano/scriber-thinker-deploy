#!/bin/bash

echo "🚀 Starting ImageBoost server (Pure Pillow Mode)..."

cd ~/clawd/image-boost
source venv/bin/activate
python3 server_pillow_only.py