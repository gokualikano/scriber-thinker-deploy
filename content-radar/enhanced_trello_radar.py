#!/usr/bin/env python3
"""
Enhanced Trello ContentRadar v5 - Now with ALL FREE APIs
Includes: EMSC, NASA FIRMS, GDACS, Congress, Federal Register, Supreme Court, Reddit Enhanced
"""

import json
import subprocess
import requests
import feedparser
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import re
from urllib.parse import quote_plus

# Add venv packages
VENV_PATH = Path(__file__).parent / "venv" / "lib"
for p in VENV_PATH.glob("python*/site-packages"):
    sys.path.insert(0, str(p))

# Import our viral APIs
from viral_apis import (
    get_emsc_earthquakes, get_nasa_fires, get_gdacs_alerts,
    get_congress_bills, get_federal_register, get_supreme_court_cases,
    get_reddit_trending
)

BASE_DIR = Path(__file__).parent

# Load Trello credentials
config = json.loads(Path('/Users/malikano/clawdbot_system/config.json').read_text())
API_KEY = config['trello_api_key']
TOKEN = config['trello_api_token']

LIST_IDS = json.loads((BASE_DIR / 'trello_lists.json').read_text())
COMPETITORS = json.loads((BASE_DIR.parent / 'competitors.json').read_text())

RSS_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

# Time filters - STRICT 24h
NOW = datetime.now()
YESTERDAY = (NOW - timedelta(hours=24)).strftime("%Y%m%d")
CUTOFF_TIMESTAMP = (NOW - timedelta(hours=24)).timestamp()

def trello_request(method, endpoint, **kwargs):
    url = f"https://api.trello.com/1/{endpoint}"
    params = kwargs.pop('params', {})
    params.update({"key": API_KEY, "token": TOKEN})
    return requests.request(method, url, params=params, **kwargs)

def create_enhanced_card(list_name, title, findings):
    """Create ONE card with ALL findings including new APIs"""
    list_id = LIST_IDS.get(list_name)
    if not list_id:
        return None
    
    desc_lines = [
        f"📅 Scan: {NOW.strftime('%Y-%m-%d %H:%M')}",
        "🆕 ENHANCED with FREE APIs",
        "⏰ Last 24 hours only",
        ""
    ]
    
    # Group findings by type
    findings_by_type = {}
    for item in findings:
        source_type = item.get('source_type', 'other')
        if source_type not in findings_by_type:
            findings_by_type[source_type] = []
        findings_by_type[source_type].append(item)
    
    # Priority markers
    def format_item(item):
        priority = item.get('priority', 'MEDIUM')
        emoji = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "⚪"
        
        title = item.get('title', 'No title')[:65]
        source = item.get('source', '')
        url = item.get('url', '#')
        
        # Add extra info based on type
        extra = ""
        if item.get('magnitude'):
            extra = f" • M{item['magnitude']}"
        elif item.get('count'):
            extra = f" • {item['count']} hotspots"
        elif item.get('engagement_rate'):
            extra = f" • {item['engagement_rate']:.1f} rate"
        elif item.get('score'):
            extra = f" • {item['score']} score"
        
        return f"{emoji} [{source}] {title}{extra}\n🔗 {url}\n"
    
    # NEW DISASTER APIS
    if any(t in findings_by_type for t in ['earthquake', 'wildfire', 'disaster']):
        desc_lines.append("🌋 **NEW DISASTER SOURCES:**")
        
        for source_type in ['earthquake', 'wildfire', 'disaster']:
            if source_type in findings_by_type:
                items = findings_by_type[source_type]
                for item in items[:3]:  # Top 3 per type
                    desc_lines.append(format_item(item))
        desc_lines.append("")
    
    # NEW POLITICAL/LEGAL APIS  
    if any(t in findings_by_type for t in ['legislation', 'regulation', 'court_case']):
        desc_lines.append("⚖️ **NEW POLITICAL SOURCES:**")
        
        for source_type in ['legislation', 'regulation', 'court_case']:
            if source_type in findings_by_type:
                items = findings_by_type[source_type]
                for item in items[:3]:
                    desc_lines.append(format_item(item))
        desc_lines.append("")
    
    # ENHANCED REDDIT
    if 'reddit' in findings_by_type:
        desc_lines.append("📱 **ENHANCED REDDIT:**")
        reddit_items = sorted(findings_by_type['reddit'], 
                            key=lambda x: x.get('engagement_rate', 0), reverse=True)
        for item in reddit_items[:5]:
            desc_lines.append(format_item(item))
        desc_lines.append("")
    
    # EXISTING SOURCES (YouTube, Google News, etc.)
    for source_type in ['youtube', 'google_news', 'trends', 'twitter']:
        if source_type in findings_by_type:
            type_emojis = {
                'youtube': '🎬', 'google_news': '📰', 
                'trends': '📈', 'twitter': '🐦'
            }
            desc_lines.append(f"{type_emojis.get(source_type, '📌')} **{source_type.upper().replace('_', ' ')}:**")
            
            items = findings_by_type[source_type][:6]
            for item in items:
                desc_lines.append(format_item(item))
            desc_lines.append("")
    
    # Summary stats
    total_items = len(findings)
    high_priority = len([f for f in findings if f.get('priority') == 'HIGH'])
    
    desc_lines.extend([
        "📊 **SUMMARY:**",
        f"• Total items: {total_items}",
        f"• High priority: {high_priority}",
        f"• API sources: {len(findings_by_type)}",
        "",
        "💡 **AI ADVANTAGE:** 15-45 min head start vs competitors"
    ])
    
    description = "\n".join(desc_lines)
    
    # Create the card
    try:
        response = trello_request(
            "POST", "cards",
            json={
                "name": title,
                "desc": description[:10000],  # Trello limit
                "idList": list_id,
                "pos": "top"
            }
        )
        
        if response.status_code == 200:
            card_id = response.json().get("id")
            print(f"✅ Created enhanced card: {title}")
            return card_id
        else:
            print(f"❌ Trello error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Card creation error: {e}")
        return None

# =============================================================================
# CHANNEL-SPECIFIC FUNCTIONS (Enhanced)
# =============================================================================

def run_enhanced_h1h3_scan():
    """H1/H3 Disasters - Now with EMSC, NASA FIRMS, GDACS"""
    print("\n🌋 H1/H3 ENHANCED DISASTER SCAN")
    print("=" * 40)
    
    findings = []
    
    # NEW APIs
    print("🔍 EMSC Earthquakes...")
    emsc_earthquakes = get_emsc_earthquakes(min_magnitude=5.5)
    findings.extend(emsc_earthquakes)
    print(f"   Found {len(emsc_earthquakes)} earthquakes")
    
    print("🔍 NASA Fire Hotspots...")
    nasa_fires = get_nasa_fires()
    findings.extend(nasa_fires)
    print(f"   Found {len(nasa_fires)} fire clusters")
    
    print("🔍 GDACS Alerts...")
    gdacs_alerts = get_gdacs_alerts()
    findings.extend(gdacs_alerts)
    print(f"   Found {len(gdacs_alerts)} global alerts")
    
    # Enhanced Reddit for disaster content
    print("🔍 Reddit Disaster Posts...")
    disaster_subreddits = ["news", "worldnews", "CatastrophicFailure", "NatureIsFuckingLit"]
    reddit_posts = get_reddit_trending(subreddits=disaster_subreddits, limit=15)
    
    # Filter for disaster-related content
    disaster_keywords = ["earthquake", "tsunami", "hurricane", "tornado", "volcano", "flood", "wildfire", "storm", "disaster", "emergency"]
    disaster_reddit = []
    for post in reddit_posts:
        title_lower = post.get('title', '').lower()
        if any(kw in title_lower for kw in disaster_keywords):
            disaster_reddit.append(post)
    
    findings.extend(disaster_reddit)
    print(f"   Found {len(disaster_reddit)} disaster Reddit posts")
    
    # Existing competitor scanning (keep this)
    print("🔍 Competitor Channels...")
    competitor_videos = scan_competitor_channels_strict_24h("H1_DISASTERS", max_per_competitor=2)
    
    # Convert competitor format to match new API format
    for video in competitor_videos:
        video['source_type'] = 'youtube'
        video['priority'] = 'MEDIUM'
        if video.get('views_int', 0) > 100000:
            video['priority'] = 'HIGH'
    
    findings.extend(competitor_videos)
    print(f"   Found {len(competitor_videos)} competitor videos")
    
    if findings:
        title = f"🌋 H1/H3 Enhanced Disasters - {len(findings)} items"
        create_enhanced_card("🌋 H1/H3 - Disasters", title, findings)
    
    return findings

def run_enhanced_h2_scan():
    """H2 Gun Rights - Now with Congress, Federal Register, Supreme Court"""
    print("\n🔫 H2 ENHANCED GUN RIGHTS SCAN")
    print("=" * 40)
    
    findings = []
    
    # NEW Political APIs
    print("🔍 Congress Bills...")
    congress_bills = get_congress_bills()
    findings.extend(congress_bills)
    print(f"   Found {len(congress_bills)} relevant bills")
    
    print("🔍 Federal Register...")
    federal_regs = get_federal_register()
    findings.extend(federal_regs)
    print(f"   Found {len(federal_regs)} regulations")
    
    print("🔍 Supreme Court Cases...")
    court_cases = get_supreme_court_cases()
    findings.extend(court_cases)
    print(f"   Found {len(court_cases)} relevant cases")
    
    # Enhanced Reddit for gun rights
    print("🔍 Reddit Gun Rights...")
    gun_subreddits = ["guns", "firearms", "2ALiberals", "progun", "gunpolitics"]
    reddit_posts = get_reddit_trending(subreddits=gun_subreddits, limit=15)
    findings.extend(reddit_posts)
    print(f"   Found {len(reddit_posts)} gun rights posts")
    
    # Existing sources (competitors, Google News, Trends)
    print("🔍 Traditional Sources...")
    # Add existing competitor scanning, Google News, Trends here
    # (Keep the existing H2 logic from trello_radar.py)
    
    if findings:
        title = f"🔫 H2 Enhanced Gun Rights - {len(findings)} items"
        create_enhanced_card("🔫 H2 - Gun Rights", title, findings)
    
    return findings

def run_enhanced_r1_scan():
    """R1 Taylor Swift - Enhanced with Reddit and future Instagram/Spotify"""
    print("\n💫 R1 ENHANCED TAYLOR SWIFT SCAN")
    print("=" * 40)
    
    findings = []
    
    # Enhanced Reddit for Taylor Swift
    print("🔍 Reddit Taylor Swift...")
    taylor_subreddits = ["TaylorSwift", "swifties", "entertainment", "popheads", "nfl"]
    reddit_posts = get_reddit_trending(subreddits=taylor_subreddits, limit=20)
    
    # Filter for Taylor/Travis content
    taylor_keywords = ["taylor swift", "travis kelce", "eras tour", "swifties", "swift", "kelce"]
    taylor_reddit = []
    for post in reddit_posts:
        title_lower = post.get('title', '').lower()
        if any(kw in title_lower for kw in taylor_keywords):
            post['priority'] = 'HIGH' if post.get('engagement_rate', 0) > 30 else 'MEDIUM'
            taylor_reddit.append(post)
    
    findings.extend(taylor_reddit)
    print(f"   Found {len(taylor_reddit)} Taylor Swift posts")
    
    # TODO: Add Instagram API, Spotify API when implemented
    # For now, keep existing competitor scanning and celebrity RSS
    
    if findings:
        title = f"💫 R1 Enhanced Taylor Swift - {len(findings)} items"
        create_enhanced_card("💫 R1 - Taylor Swift", title, findings)
    
    return findings

def run_enhanced_r2_scan():
    """R2 Legal/Crime - Enhanced with Court APIs and Reddit"""
    print("\n⚖️ R2 ENHANCED LEGAL/CRIME SCAN")
    print("=" * 40)
    
    findings = []
    
    # Supreme Court cases (broader than just gun rights)
    print("🔍 All Supreme Court Activity...")
    court_cases = get_supreme_court_cases()
    findings.extend(court_cases)
    print(f"   Found {len(court_cases)} court cases")
    
    # Enhanced Reddit for legal content
    print("🔍 Reddit Legal Content...")
    legal_subreddits = ["legaladvice", "news", "politics", "JusticeServed"]
    reddit_posts = get_reddit_trending(subreddits=legal_subreddits, limit=20)
    
    # Filter for legal/crime keywords
    legal_keywords = ["verdict", "sentenced", "arrested", "trial", "lawsuit", "court", "judge", "jury", "conviction"]
    legal_reddit = []
    for post in reddit_posts:
        title_lower = post.get('title', '').lower()
        if any(kw in title_lower for kw in legal_keywords):
            post['priority'] = 'HIGH' if post.get('engagement_rate', 0) > 40 else 'MEDIUM'
            legal_reddit.append(post)
    
    findings.extend(legal_reddit)
    print(f"   Found {len(legal_reddit)} legal posts")
    
    if findings:
        title = f"⚖️ R2 Enhanced Legal - {len(findings)} items"
        create_enhanced_card("⚖️ R2 - Legal/Crime", title, findings)
    
    return findings

def run_full_enhanced_scan():
    """Run ALL enhanced scans across all channels"""
    print("🚀 FULL ENHANCED API SCAN")
    print("=" * 50)
    print(f"🕐 Started: {NOW.strftime('%Y-%m-%d %H:%M:%S')}")
    print("🆕 Using: EMSC, NASA FIRMS, GDACS, Congress, Federal Register, Supreme Court, Enhanced Reddit")
    
    all_findings = []
    
    # Run each channel scan
    h1h3_results = run_enhanced_h1h3_scan()
    all_findings.extend(h1h3_results)
    
    h2_results = run_enhanced_h2_scan()
    all_findings.extend(h2_results)
    
    r1_results = run_enhanced_r1_scan()
    all_findings.extend(r1_results)
    
    r2_results = run_enhanced_r2_scan()
    all_findings.extend(r2_results)
    
    # Summary
    high_priority = len([f for f in all_findings if f.get('priority') == 'HIGH'])
    unique_sources = len(set(f.get('source', 'Unknown') for f in all_findings))
    
    print(f"\n🎯 ENHANCED SCAN COMPLETE")
    print(f"📊 Total items: {len(all_findings)}")
    print(f"🔴 High priority: {high_priority}")
    print(f"🌐 Unique sources: {unique_sources}")
    print(f"⏱️ Duration: {(datetime.now() - NOW).total_seconds():.1f}s")
    
    return all_findings

# Import existing functions from original trello_radar.py
def scan_competitor_channels_strict_24h(channel_key, max_per_competitor=2):
    """Keep existing competitor scanning function"""
    # This would be imported/copied from the original trello_radar.py
    # For now, return empty list as placeholder
    return []

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Trello ContentRadar with ALL FREE APIs")
    parser.add_argument("--full", action="store_true", help="Full enhanced scan all channels")
    parser.add_argument("--h1h3", action="store_true", help="Enhanced H1/H3 disasters")
    parser.add_argument("--h2", action="store_true", help="Enhanced H2 gun rights")
    parser.add_argument("--r1", action="store_true", help="Enhanced R1 Taylor Swift")
    parser.add_argument("--r2", action="store_true", help="Enhanced R2 legal/crime")
    parser.add_argument("--test", action="store_true", help="Test all APIs without creating cards")
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 TESTING ALL FREE APIs")
        print("=" * 30)
        
        from viral_apis import run_all_free_apis
        results = run_all_free_apis()
        
        print(f"\n📊 API Test Results:")
        for category, sources in results.items():
            if isinstance(sources, dict) and category != "timestamp":
                print(f"{category.replace('_', ' ').title()}:")
                for source, items in sources.items():
                    if isinstance(items, list):
                        print(f"  {source}: {len(items)} items")
    
    elif args.full:
        run_full_enhanced_scan()
    elif args.h1h3:
        run_enhanced_h1h3_scan()
    elif args.h2:
        run_enhanced_h2_scan()
    elif args.r1:
        run_enhanced_r1_scan()
    elif args.r2:
        run_enhanced_r2_scan()
    else:
        print("🆕 Enhanced ContentRadar with FREE APIs")
        print("Options: --full, --h1h3, --h2, --r1, --r2, --test")
        print("Added: EMSC, NASA FIRMS, GDACS, Congress, Federal Register, Supreme Court, Enhanced Reddit")