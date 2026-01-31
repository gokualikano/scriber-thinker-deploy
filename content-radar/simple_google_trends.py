#!/usr/bin/env python3
"""
Simple Google Trends Integration - Channel-specific trend analysis
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import time

# Add venv packages to path
VENV_PATH = Path(__file__).parent / "venv" / "lib"
for p in VENV_PATH.glob("python*/site-packages"):
    sys.path.insert(0, str(p))

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

NOW = datetime.now()

def get_simple_trends(keywords, category_name):
    """Get simple trend data for keywords"""
    if not PYTRENDS_AVAILABLE:
        return []
    
    trends = []
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        for keyword in keywords[:3]:  # Limit to 3 keywords to avoid rate limits
            try:
                pytrends.build_payload([keyword], timeframe='today 12-m', geo='US')
                data = pytrends.interest_over_time()
                
                if not data.empty and keyword in data.columns:
                    # Get recent values
                    recent_values = data[keyword].tail(4).values  # Last 4 weeks
                    current_value = recent_values[-1] if len(recent_values) > 0 else 0
                    
                    if current_value > 0:
                        # Calculate trend
                        if len(recent_values) >= 2:
                            trend_direction = "rising" if recent_values[-1] > recent_values[-2] else "falling"
                        else:
                            trend_direction = "stable"
                        
                        trends.append({
                            "keyword": keyword,
                            "interest": int(current_value),
                            "trend": trend_direction,
                            "category": category_name,
                            "source": "Google Trends",
                            "source_type": "trends",
                            "timestamp": NOW.strftime("%Y-%m-%d %H:%M"),
                            "priority": "HIGH" if current_value > 50 else "MEDIUM" if current_value > 20 else "LOW"
                        })
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"  Error with keyword '{keyword}': {e}")
                time.sleep(3)  # Longer wait on error
                continue
                
    except Exception as e:
        print(f"Trends error for {category_name}: {e}")
    
    return sorted(trends, key=lambda x: x.get('interest', 0), reverse=True)

def get_channel_trends():
    """Get trends for all channels with simplified approach"""
    if not PYTRENDS_AVAILABLE:
        print("⚠️  pytrends not available")
        return {}
    
    print("📈 SIMPLE GOOGLE TRENDS ANALYSIS")
    print("=" * 40)
    
    channel_trends = {}
    
    # Channel keywords mapping
    channel_keywords = {
        "disasters": ["earthquake", "hurricane", "wildfire"],
        "gun_rights": ["gun rights", "second amendment", "firearms"], 
        "taylor_swift": ["Taylor Swift", "Travis Kelce", "Eras Tour"],
        "legal": ["Supreme Court", "verdict", "lawsuit"],
        "tech": ["AI", "blockchain", "ChatGPT"]
    }
    
    for channel, keywords in channel_keywords.items():
        print(f"🔍 Getting {channel} trends...")
        channel_trends[channel] = get_simple_trends(keywords, channel)
        time.sleep(1)  # Rate limiting between channels
    
    return channel_trends

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Google Trends")
    parser.add_argument("--all", action="store_true", help="All channel trends")
    parser.add_argument("--test", type=str, help="Test single keyword")
    parser.add_argument("--json", action="store_true", help="JSON output")
    
    args = parser.parse_args()
    
    if args.test:
        print(f"🧪 Testing: {args.test}")
        trends = get_simple_trends([args.test], "test")
        if trends:
            trend = trends[0]
            print(f"Interest: {trend['interest']}, Trend: {trend['trend']}")
        else:
            print("No data found")
    
    elif args.all:
        results = get_channel_trends()
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for channel, trends in results.items():
                if trends:
                    print(f"\n{channel.upper().replace('_', ' ')}:")
                    for trend in trends:
                        emoji = "📈" if trend['trend'] == 'rising' else "📉" if trend['trend'] == 'falling' else "➡️"
                        print(f"  {emoji} {trend['keyword']} - Interest: {trend['interest']}")
    
    else:
        print("Simple Google Trends Integration")
        print("Usage:")
        print("  --all     : Get trends for all channels")
        print("  --test X  : Test single keyword")
        print("  --json    : JSON output")