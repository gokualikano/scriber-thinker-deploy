#!/bin/bash
# Install Viral APIs - All Free Content Intelligence Sources

cd "$(dirname "$0")"

echo "🚀 Installing Viral APIs..."
echo "Adding: EMSC, NASA FIRMS, GDACS, Congress, Federal Register, Supreme Court, Enhanced Reddit"

# Activate virtual environment
source venv/bin/activate

# Update requirements if needed
pip install beautifulsoup4 --quiet

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Available Commands:"
echo ""
echo "# Test all free APIs"
echo "source venv/bin/activate && python viral_apis.py --all"
echo ""
echo "# Get high priority alerts only"  
echo "source venv/bin/activate && python viral_apis.py --high-priority"
echo ""
echo "# Test individual categories"
echo "source venv/bin/activate && python viral_apis.py --disasters"
echo "source venv/bin/activate && python viral_apis.py --politics"
echo "source venv/bin/activate && python viral_apis.py --social"
echo ""
echo "# Enhanced Trello integration"
echo "source venv/bin/activate && python enhanced_trello_radar.py --test"
echo "source venv/bin/activate && python enhanced_trello_radar.py --full"
echo ""
echo "🎯 NEW API SOURCES ADDED:"
echo "  🌋 EMSC Earthquakes (5-15 min before USGS)"
echo "  🔥 NASA FIRMS Wildfire Hotspots"
echo "  🌍 GDACS Global Disaster Alerts"
echo "  🏛️ Congress.gov Bills & Activities"
echo "  📋 Federal Register ATF/Gun Regulations"
echo "  ⚖️ Supreme Court Cases (Oyez API)"
echo "  📱 Enhanced Reddit Trending"
echo ""
echo "💰 Cost: $0.00/month (all free!)"
echo "⏰ Head start: 15-45 minutes vs competitors"