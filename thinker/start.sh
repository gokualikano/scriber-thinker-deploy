#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🧠 Starting Thinker on http://localhost:8585"
open http://localhost:8585
python server.py
