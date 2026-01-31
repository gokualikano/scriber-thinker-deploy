#!/bin/bash

echo "🚀 Starting ImageBoost BULK server..."

cd ~/clawd/image-boost
source venv/bin/activate
python3 server_bulk.py