#!/usr/bin/env python3
"""
Google Trends API using pytrends - Channel-specific trending analysis
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import time

# Add venv packages to path
VENV_PATH = Path(__file__).parent / "venv" / "lib"
for p in VENV_PATH.glob("python*/site-packages"):
    sys.path.insert(0, str(p))

try:
    from pytrends.request import TrendReq
    import pandas as pd
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("⚠️  pytrends not available. Run: pip install pytrends")

# Time filters
NOW = datetime.now()

def safe_pytrends_request(func, *args, **kwargs):
    """Wrapper for pytrends requests with error handling and rate limiting"""
    try:
        time.sleep(1)  # Rate limiting
        return func(*args, **kwargs)
    except Exception as e:
        print(f"PyTrends error: {e}")
        return None

def get_trending_searches_by_channel():
    """Get trending searches tailored for each channel"""
    if not PYTRENDS_AVAILABLE:
        return {}
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        channel_trends = {}
        
        # H1/H3 - Disaster keywords
        disaster_keywords = [
            "earthquake", "tsunami", "hurricane", "tornado", "volcano",
            "wildfire", "flood", "storm", "disaster", "emergency"
        ]
        
        print("🌋 Getting disaster trends...")
        disaster_trends = get_keyword_trends(pytrends, disaster_keywords[:5], "disasters")
        channel_trends["disasters"] = disaster_trends
        
        # H2 - Gun rights keywords  
        gun_keywords = [
            "gun rights", "second amendment", "ATF", "firearms", "gun ban",
            "constitutional carry", "gun control", "NRA", "Supreme Court gun"
        ]
        
        print("🔫 Getting gun rights trends...")
        gun_trends = get_keyword_trends(pytrends, gun_keywords[:5], "gun_rights")
        channel_trends["gun_rights"] = gun_trends
        
        # R1 - Taylor Swift keywords
        taylor_keywords = [
            "Taylor Swift", "Travis Kelce", "Eras Tour", "Swifties", "Taylor Travis",
            "Chiefs Taylor", "Swift concert", "Taylor album", "Swift news"
        ]
        
        print("💫 Getting Taylor Swift trends...")
        taylor_trends = get_keyword_trends(pytrends, taylor_keywords[:5], "taylor_swift")
        channel_trends["taylor_swift"] = taylor_trends
        
        # R2 - Legal/Crime keywords
        legal_keywords = [
            "court case", "verdict", "sentenced", "trial", "lawsuit",
            "Supreme Court", "federal court", "criminal trial", "legal news"
        ]
        
        print("⚖️ Getting legal trends...")
        legal_trends = get_keyword_trends(pytrends, legal_keywords[:5], "legal")
        channel_trends["legal"] = legal_trends
        
        # Tech trends (general viral potential)
        tech_keywords = [
            "AI", "ChatGPT", "cryptocurrency", "blockchain", "tech news",
            "startup", "silicon valley", "tech stock", "innovation"
        ]
        
        print("💻 Getting tech trends...")
        tech_trends = get_keyword_trends(pytrends, tech_keywords[:5], "tech")
        channel_trends["tech"] = tech_trends
        
        return channel_trends
        
    except Exception as e:
        print(f"Google Trends error: {e}")
        return {}

def get_keyword_trends(pytrends, keywords, category):
    """Get trend data for specific keywords"""
    trends = []
    
    try:
        # Interest over time (last 7 days)
        pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='US')
        interest_data = safe_pytrends_request(pytrends.interest_over_time)
        
        if interest_data is not None and not interest_data.empty:
            # Get latest week's data
            latest_data = interest_data.tail(7)  # Last 7 days
            
            for keyword in keywords:
                if keyword in latest_data.columns:
                    recent_values = latest_data[keyword].values
                    current_value = recent_values[-1] if len(recent_values) > 0 else 0
                    avg_value = recent_values.mean() if len(recent_values) > 0 else 0
                    
                    # Calculate trend direction
                    if len(recent_values) >= 2:
                        trend_direction = "rising" if recent_values[-1] > recent_values[-2] else "falling"
                    else:
                        trend_direction = "stable"
                    
                    # Only include if there's significant interest
                    if current_value > 0:
                        trends.append({
                            "keyword": keyword,
                            "current_interest": int(current_value),
                            "avg_interest": float(avg_value),
                            "trend_direction": trend_direction,
                            "category": category,
                            "timestamp": NOW.strftime("%Y-%m-%d %H:%M"),
                            "source": "Google Trends",
                            "source_type": "trends",
                            "priority": "HIGH" if current_value > 50 else "MEDIUM" if current_value > 25 else "LOW"
                        })
        
        time.sleep(2)  # Rate limiting between requests
        
        # Related queries for top keyword
        if keywords and trends:
            top_keyword = keywords[0]
            try:
                related_queries = safe_pytrends_request(pytrends.related_queries)
                if related_queries and top_keyword in related_queries:
                    rising_queries = related_queries[top_keyword].get('rising')
                    if rising_queries is not None and not rising_queries.empty:
                        for idx, row in rising_queries.head(3).iterrows():
                            trends.append({
                                "keyword": f"Related: {row['query']}",
                                "current_interest": int(row['value']) if pd.notna(row['value']) else 0,
                                "trend_direction": "rising",
                                "category": category,
                                "timestamp": NOW.strftime("%Y-%m-%d %H:%M"),
                                "source": "Google Trends (Related)",
                                "source_type": "trends",
                                "priority": "MEDIUM"
                            })
            except Exception as e:
                print(f"Related queries error: {e}")
        
        time.sleep(2)  # Rate limiting
        
    except Exception as e:
        print(f"Keyword trends error for {category}: {e}")
    
    return sorted(trends, key=lambda x: x.get('current_interest', 0), reverse=True)

def get_realtime_trending():
    """Get real-time trending searches (US)"""
    if not PYTRENDS_AVAILABLE:
        return []
    
    trends = []
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Real-time trending searches
        trending_searches = safe_pytrends_request(pytrends.trending_searches, pn='united_states')
        
        if trending_searches is not None and not trending_searches.empty:
            for idx, search_term in trending_searches.head(15).iterrows():
                search_query = search_term[0] if isinstance(search_term[0], str) else str(search_term[0])
                
                trends.append({
                    "keyword": search_query,
                    "rank": idx + 1,
                    "timestamp": NOW.strftime("%Y-%m-%d %H:%M"),
                    "source": "Google Trends (Realtime)",
                    "source_type": "realtime_trends",
                    "priority": "HIGH" if idx < 5 else "MEDIUM",
                    "category": "realtime"
                })
        
    except Exception as e:
        print(f"Realtime trends error: {e}")
    
    return trends

def get_rising_searches():
    """Get today's rising searches"""
    if not PYTRENDS_AVAILABLE:
        return []
    
    trends = []
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Today's rising searches
        today_searches = safe_pytrends_request(pytrends.today_searches, pn='US')
        
        if today_searches is not None and not today_searches.empty:
            for idx, row in today_searches.head(10).iterrows():
                search_query = row['query'] if 'query' in row else str(row[0])
                traffic = row.get('traffic', 'Unknown')
                
                trends.append({
                    "keyword": search_query,
                    "traffic": traffic,
                    "rank": idx + 1,
                    "timestamp": NOW.strftime("%Y-%m-%d %H:%M"),
                    "source": "Google Trends (Rising)",
                    "source_type": "rising_trends",
                    "priority": "HIGH" if "breaking" in search_query.lower() else "MEDIUM",
                    "category": "rising"
                })
        
    except Exception as e:
        print(f"Rising searches error: {e}")
    
    return trends

def run_complete_google_trends():
    """Run complete Google Trends analysis"""
    print("📈 GOOGLE TRENDS ANALYSIS")
    print("=" * 40)
    
    if not PYTRENDS_AVAILABLE:
        print("❌ pytrends not available. Install with: pip install pytrends")
        return {}
    
    all_trends = {
        "timestamp": NOW.strftime("%Y-%m-%d %H:%M:%S"),
        "channel_specific": {},
        "realtime_trending": [],
        "rising_searches": []
    }
    
    try:
        # Channel-specific trends
        print("🔍 Analyzing channel-specific trends...")
        all_trends["channel_specific"] = get_trending_searches_by_channel()
        
        # Real-time trending
        print("⚡ Getting real-time trending...")
        all_trends["realtime_trending"] = get_realtime_trending()
        
        # Rising searches
        print("📈 Getting today's rising searches...")
        all_trends["rising_searches"] = get_rising_searches()
        
        # Count total items
        total_items = (
            sum(len(trends) for trends in all_trends["channel_specific"].values()) +
            len(all_trends["realtime_trending"]) +
            len(all_trends["rising_searches"])
        )
        
        print(f"✅ Google Trends complete: {total_items} trend items found")
        
    except Exception as e:
        print(f"Google Trends analysis error: {e}")
    
    return all_trends

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Google Trends API using pytrends")
    parser.add_argument("--all", action="store_true", help="Complete trends analysis")
    parser.add_argument("--channels", action="store_true", help="Channel-specific trends only")
    parser.add_argument("--realtime", action="store_true", help="Real-time trending only")
    parser.add_argument("--rising", action="store_true", help="Rising searches only")
    parser.add_argument("--test", type=str, help="Test specific keyword")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if args.test:
        print(f"🧪 Testing keyword: {args.test}")
        if PYTRENDS_AVAILABLE:
            try:
                pytrends = TrendReq(hl='en-US', tz=360)
                pytrends.build_payload([args.test], timeframe='today 12-m')
                data = pytrends.interest_over_time()
                if not data.empty:
                    print(f"Recent trend data for '{args.test}':")
                    print(data.tail())
                else:
                    print("No trend data found")
            except Exception as e:
                print(f"Test error: {e}")
    
    elif args.channels:
        trends = get_trending_searches_by_channel()
        if args.json:
            print(json.dumps(trends, indent=2))
        else:
            for channel, channel_trends in trends.items():
                print(f"\n{channel.upper().replace('_', ' ')}:")
                for trend in channel_trends[:5]:
                    direction_emoji = "📈" if trend['trend_direction'] == 'rising' else "📉" if trend['trend_direction'] == 'falling' else "➡️"
                    print(f"  {direction_emoji} {trend['keyword']} - Interest: {trend['current_interest']}")
    
    elif args.realtime:
        trends = get_realtime_trending()
        if args.json:
            print(json.dumps(trends, indent=2))
        else:
            print("⚡ REAL-TIME TRENDING (US):")
            for trend in trends:
                print(f"  {trend['rank']}. {trend['keyword']}")
    
    elif args.rising:
        trends = get_rising_searches()
        if args.json:
            print(json.dumps(trends, indent=2))
        else:
            print("📈 TODAY'S RISING SEARCHES:")
            for trend in trends:
                print(f"  {trend['rank']}. {trend['keyword']} ({trend['traffic']})")
    
    else:
        # Default: complete analysis
        results = run_complete_google_trends()
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"\n📊 GOOGLE TRENDS SUMMARY")
            print(f"Channel-specific trends: {sum(len(t) for t in results['channel_specific'].values())}")
            print(f"Real-time trending: {len(results['realtime_trending'])}")
            print(f"Rising searches: {len(results['rising_searches'])}")