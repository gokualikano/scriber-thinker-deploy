#!/usr/bin/env python3
"""
Viral APIs - Comprehensive free API collection for early content signals
Adds: EMSC, NASA FIRMS, GDACS, Congress, Federal Register, Supreme Court, 
      Reddit Enhanced, Instagram, YouTube API, Spotify
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import time

# Add venv packages to path
VENV_PATH = Path(__file__).parent / "venv" / "lib"
for p in VENV_PATH.glob("python*/site-packages"):
    sys.path.insert(0, str(p))

import requests
import feedparser
from bs4 import BeautifulSoup

# Paths
BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "api_state.json"

# HTTP headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Time filtering
NOW = datetime.now()
CUTOFF_24H = NOW - timedelta(hours=24)
CUTOFF_1H = NOW - timedelta(hours=1)

def load_state():
    """Load last check timestamps"""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_checks": {}}

def save_state(state):
    """Save current timestamps"""
    STATE_FILE.write_text(json.dumps(state, indent=2))

# =============================================================================
# DISASTER APIs (H1/H3)
# =============================================================================

def get_emsc_earthquakes(min_magnitude=5.5):
    """EMSC Earthquake API - Often 5-15 min before USGS"""
    alerts = []
    try:
        url = "https://www.seismicportal.eu/fdsnws/event/1/query?format=json&limit=20&orderby=time"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            
            for event in data.get('features', []):
                props = event.get('properties', {})
                mag = props.get('mag', 0)
                time_str = props.get('time', '')
                
                if mag >= min_magnitude and time_str:
                    # Parse time
                    event_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    if event_time > CUTOFF_24H.replace(tzinfo=timezone.utc):
                        location = props.get('place', 'Unknown location')
                        
                        alerts.append({
                            "title": f"M{mag} Earthquake - {location}",
                            "magnitude": mag,
                            "location": location,
                            "time": event_time.strftime("%Y-%m-%d %H:%M UTC"),
                            "url": f"https://www.seismicportal.eu/earthquakes/details.php?id={props.get('publicID', '')}",
                            "source": "EMSC",
                            "source_type": "earthquake",
                            "priority": "HIGH" if mag >= 6.5 else "MEDIUM"
                        })
    except Exception as e:
        print(f"EMSC API error: {e}")
    
    return sorted(alerts, key=lambda x: x.get('magnitude', 0), reverse=True)

def get_nasa_fires():
    """NASA FIRMS - Real-time wildfire hotspots"""
    fires = []
    try:
        # VIIRS active fires (last 24h)
        url = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/viirs/csv/VNP14IMGTDL_NRT_USA_contiguous_and_Hawaii_24h.csv"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            headers = lines[0].split(',')
            
            fire_count = {}  # Group by state/region
            
            for line in lines[1:51]:  # First 50 fires
                fields = line.split(',')
                if len(fields) >= 10:
                    lat = fields[0]
                    lon = fields[1]
                    confidence = fields[8]
                    acq_date = fields[5]
                    acq_time = fields[6]
                    
                    # Group fires by approximate location
                    region_key = f"{lat[:4]},{lon[:5]}"  # Approximate region grouping
                    
                    if region_key not in fire_count:
                        fire_count[region_key] = {
                            "count": 0,
                            "max_confidence": 0,
                            "lat": lat,
                            "lon": lon,
                            "date": acq_date,
                            "time": acq_time
                        }
                    
                    fire_count[region_key]["count"] += 1
                    fire_count[region_key]["max_confidence"] = max(
                        fire_count[region_key]["max_confidence"], 
                        float(confidence) if confidence.replace('.', '').isdigit() else 0
                    )
            
            # Convert to alerts for significant fire clusters
            for region, data in fire_count.items():
                if data["count"] >= 5:  # 5+ hotspots in same area
                    fires.append({
                        "title": f"Wildfire Cluster: {data['count']} hotspots detected",
                        "location": f"Lat {data['lat']}, Lon {data['lon']}",
                        "confidence": data['max_confidence'],
                        "count": data['count'],
                        "date": data['date'],
                        "url": f"https://firms.modaps.eosdis.nasa.gov/map/#d:24hrs;@{data['lon']},{data['lat']},12z",
                        "source": "NASA FIRMS",
                        "source_type": "wildfire",
                        "priority": "HIGH" if data['count'] >= 15 else "MEDIUM"
                    })
                    
    except Exception as e:
        print(f"NASA FIRMS error: {e}")
    
    return sorted(fires, key=lambda x: x.get('count', 0), reverse=True)[:10]

def get_gdacs_alerts():
    """GDACS - Global Disaster Alert and Coordination System"""
    alerts = []
    try:
        url = "https://www.gdacs.org/xml/rss.xml"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            
            for entry in feed.entries[:15]:
                pub_date = datetime(*entry.published_parsed[:6])
                if pub_date > CUTOFF_24H:
                    
                    # Extract alert level from description
                    desc = entry.get('description', '')
                    alert_level = "MEDIUM"
                    if "RED" in desc.upper() or "SEVERE" in desc.upper():
                        alert_level = "HIGH"
                    elif "ORANGE" in desc.upper():
                        alert_level = "MEDIUM"
                    
                    alerts.append({
                        "title": entry.title,
                        "description": desc[:200],
                        "url": entry.link,
                        "published": pub_date.strftime("%Y-%m-%d %H:%M"),
                        "source": "GDACS",
                        "source_type": "disaster",
                        "priority": alert_level
                    })
                    
    except Exception as e:
        print(f"GDACS error: {e}")
    
    return alerts

# =============================================================================
# POLITICAL/LEGAL APIs (H2/R2)
# =============================================================================

def get_congress_bills(keywords=["gun", "firearm", "amendment", "atf", "rifle"]):
    """Congress.gov API - New bills and activities"""
    bills = []
    try:
        # Recent bills with gun-related keywords
        url = f"https://api.congress.gov/v3/bill?format=json&limit=20"
        # Note: Requires API key, but basic info available via RSS
        
        # Use RSS feed instead (free)
        rss_url = "https://www.congress.gov/rss/bills-introduced.xml"
        resp = requests.get(rss_url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            
            for entry in feed.entries[:20]:
                title = entry.title.lower()
                description = entry.get('description', '').lower()
                
                # Check for gun-related keywords
                if any(kw in title or kw in description for kw in keywords):
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date > CUTOFF_24H:
                        bills.append({
                            "title": entry.title,
                            "description": entry.get('description', '')[:200],
                            "url": entry.link,
                            "published": pub_date.strftime("%Y-%m-%d %H:%M"),
                            "source": "Congress.gov",
                            "source_type": "legislation",
                            "priority": "MEDIUM"
                        })
                        
    except Exception as e:
        print(f"Congress API error: {e}")
    
    return bills

def get_federal_register(keywords=["ATF", "firearm", "gun", "second amendment"]):
    """Federal Register API - New regulations"""
    regulations = []
    try:
        url = "https://www.federalregister.gov/api/v1/documents.json"
        params = {
            "per_page": 20,
            "order": "newest",
            "conditions[publication_date][gte]": CUTOFF_24H.strftime("%Y-%m-%d"),
            "fields[]": ["title", "html_url", "publication_date", "abstract", "agencies"]
        }
        
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            
            for doc in data.get('results', []):
                title = doc.get('title', '').lower()
                abstract = doc.get('abstract', '').lower()
                agencies = str(doc.get('agencies', [])).lower()
                
                # Check for relevant keywords
                if any(kw.lower() in title or kw.lower() in abstract or kw.lower() in agencies for kw in keywords):
                    regulations.append({
                        "title": doc.get('title', ''),
                        "abstract": doc.get('abstract', '')[:200],
                        "url": doc.get('html_url', ''),
                        "publication_date": doc.get('publication_date', ''),
                        "agencies": doc.get('agencies', []),
                        "source": "Federal Register",
                        "source_type": "regulation",
                        "priority": "HIGH" if "atf" in title or "atf" in abstract else "MEDIUM"
                    })
                    
    except Exception as e:
        print(f"Federal Register error: {e}")
    
    return regulations

def get_supreme_court_cases():
    """Supreme Court API (Oyez) - Case activities"""
    cases = []
    try:
        # Get recent term cases
        current_year = datetime.now().year
        url = f"https://api.oyez.org/cases?per_page=50&filter=term:{current_year-1}"
        
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            
            for case in data[:10]:
                # Look for gun rights cases
                name = case.get('name', '').lower()
                if any(kw in name for kw in ['gun', 'firearm', 'amendment', 'bear', 'arms']):
                    cases.append({
                        "title": case.get('name', ''),
                        "docket_number": case.get('docket_number', ''),
                        "url": f"https://www.oyez.org/cases/{current_year-1}/{case.get('docket_number', '')}",
                        "source": "Supreme Court",
                        "source_type": "court_case",
                        "priority": "HIGH"
                    })
    except Exception as e:
        print(f"Supreme Court API error: {e}")
    
    return cases

# =============================================================================
# SOCIAL/TRENDING APIs
# =============================================================================

def get_reddit_trending(subreddits=["news", "worldnews", "legaladvice", "TaylorSwift"], limit=10):
    """Enhanced Reddit API - Real-time trending posts"""
    posts = []
    
    for subreddit in subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                
                for child in data.get('data', {}).get('children', []):
                    post = child.get('data', {})
                    created_utc = post.get('created_utc', 0)
                    created_time = datetime.fromtimestamp(created_utc)
                    
                    if created_time > CUTOFF_24H:
                        score = post.get('score', 0)
                        num_comments = post.get('num_comments', 0)
                        
                        # Trending criteria: high engagement in short time
                        age_hours = (NOW - created_time).total_seconds() / 3600
                        engagement_rate = (score + num_comments * 2) / max(age_hours, 1)
                        
                        posts.append({
                            "title": post.get('title', '')[:100],
                            "url": f"https://reddit.com{post.get('permalink', '')}",
                            "subreddit": subreddit,
                            "score": score,
                            "comments": num_comments,
                            "engagement_rate": engagement_rate,
                            "created": created_time.strftime("%Y-%m-%d %H:%M"),
                            "source": f"r/{subreddit}",
                            "source_type": "reddit",
                            "priority": "HIGH" if engagement_rate > 50 else "MEDIUM"
                        })
                        
        except Exception as e:
            print(f"Reddit r/{subreddit} error: {e}")
    
    # Sort by engagement rate and return top posts
    return sorted(posts, key=lambda x: x.get('engagement_rate', 0), reverse=True)[:20]

def get_youtube_trending_channels():
    """YouTube Data API v3 - Channel analytics (free quota)"""
    # Note: This would require YouTube API key setup
    # For now, we'll enhance the RSS approach
    trending = []
    
    # Could add YouTube API implementation here with proper quota management
    print("YouTube API integration - requires API key setup")
    
    return trending

# =============================================================================
# CELEBRITY APIs (R1)
# =============================================================================

def get_spotify_taylor_swift():
    """Spotify Web API - Taylor Swift new releases"""
    releases = []
    try:
        # Note: Spotify API requires OAuth, but we can use public RSS/web scraping
        # For now, placeholder for future implementation
        print("Spotify API - requires OAuth setup")
    except Exception as e:
        print(f"Spotify API error: {e}")
    
    return releases

# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def run_all_free_apis():
    """Run all free APIs and return consolidated results"""
    print("🔍 Scanning all free APIs...")
    
    all_results = {
        "timestamp": NOW.strftime("%Y-%m-%d %H:%M:%S"),
        "disasters": {
            "emsc_earthquakes": get_emsc_earthquakes(),
            "nasa_fires": get_nasa_fires(),
            "gdacs_alerts": get_gdacs_alerts()
        },
        "politics_legal": {
            "congress_bills": get_congress_bills(),
            "federal_register": get_federal_register(),
            "supreme_court": get_supreme_court_cases()
        },
        "social_trending": {
            "reddit_posts": get_reddit_trending()
        }
    }
    
    # Count results
    total_items = 0
    for category in all_results.values():
        if isinstance(category, dict):
            for items in category.values():
                if isinstance(items, list):
                    total_items += len(items)
    
    print(f"✅ Found {total_items} items across all APIs")
    
    return all_results

def get_high_priority_alerts():
    """Get only high-priority alerts across all APIs"""
    all_data = run_all_free_apis()
    high_priority = []
    
    # Extract high priority items
    for category in all_data.values():
        if isinstance(category, dict):
            for source, items in category.items():
                if isinstance(items, list):
                    for item in items:
                        if item.get('priority') == 'HIGH':
                            high_priority.append(item)
    
    return sorted(high_priority, key=lambda x: x.get('magnitude', x.get('engagement_rate', x.get('count', 0))), reverse=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Viral APIs - Free content intelligence")
    parser.add_argument("--all", action="store_true", help="Run all APIs")
    parser.add_argument("--disasters", action="store_true", help="Disaster APIs only")
    parser.add_argument("--politics", action="store_true", help="Politics/legal APIs only")
    parser.add_argument("--social", action="store_true", help="Social trending APIs only")
    parser.add_argument("--high-priority", action="store_true", help="High priority alerts only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if args.high_priority:
        results = get_high_priority_alerts()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"\n🚨 HIGH PRIORITY ALERTS ({len(results)} items)")
            print("=" * 50)
            for item in results:
                print(f"🔴 {item.get('title', 'No title')}")
                print(f"   Source: {item.get('source', 'Unknown')}")
                print(f"   URL: {item.get('url', 'No URL')}")
                print()
    
    elif args.disasters:
        print("🌋 DISASTER APIs")
        print("=" * 30)
        
        earthquakes = get_emsc_earthquakes()
        print(f"EMSC Earthquakes: {len(earthquakes)} found")
        for eq in earthquakes[:3]:
            print(f"  • M{eq['magnitude']} - {eq['location']}")
        
        fires = get_nasa_fires()
        print(f"NASA Fire Hotspots: {len(fires)} clusters found")
        for fire in fires[:3]:
            print(f"  • {fire['count']} hotspots - {fire['location']}")
        
        gdacs = get_gdacs_alerts()
        print(f"GDACS Alerts: {len(gdacs)} found")
        for alert in gdacs[:3]:
            print(f"  • {alert['title']}")
    
    elif args.politics:
        print("⚖️ POLITICS/LEGAL APIs")
        print("=" * 30)
        
        bills = get_congress_bills()
        print(f"Congress Bills: {len(bills)} found")
        
        regs = get_federal_register()
        print(f"Federal Register: {len(regs)} found")
        
        cases = get_supreme_court_cases()
        print(f"Supreme Court: {len(cases)} found")
    
    elif args.social:
        print("📱 SOCIAL TRENDING APIs")
        print("=" * 30)
        
        reddit_posts = get_reddit_trending()
        print(f"Reddit Trending: {len(reddit_posts)} posts")
        for post in reddit_posts[:5]:
            print(f"  • {post['title'][:60]}... ({post['source']})")
    
    else:
        # Default: run all
        results = run_all_free_apis()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("🔍 ALL FREE APIs RESULTS")
            print("=" * 40)
            
            # Summary
            for category, sources in results.items():
                if isinstance(sources, dict) and category != "timestamp":
                    print(f"\n{category.upper().replace('_', ' ')}:")
                    for source, items in sources.items():
                        if isinstance(items, list):
                            print(f"  {source}: {len(items)} items")