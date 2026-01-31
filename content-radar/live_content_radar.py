#!/usr/bin/env python3
"""
Live Content Radar - Find latest news/videos for all channels (last 24hrs)
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

# Import APIs
from mega_viral_apis import get_hackernews_trending
from simple_google_trends import get_simple_trends
from viral_apis import get_emsc_earthquakes, get_gdacs_alerts

BASE_DIR = Path(__file__).parent
NOW = datetime.now()
CUTOFF_24H = NOW - timedelta(hours=24)

RSS_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

def search_youtube_videos(query, max_results=5):
    """Search for recent YouTube videos using yt-dlp"""
    videos = []
    
    try:
        # Use yt-dlp to search YouTube
        search_url = f"ytsearch{max_results}:{query}"
        
        cmd = [
            "yt-dlp", 
            "--flat-playlist",
            "--print", "title,uploader,upload_date,view_count,webpage_url",
            search_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            
            for i in range(0, len(lines), 5):  # Process in groups of 5
                if i + 4 < len(lines):
                    title = lines[i].strip()
                    uploader = lines[i + 1].strip()
                    upload_date = lines[i + 2].strip()
                    view_count = lines[i + 3].strip()
                    url = lines[i + 4].strip()
                    
                    # Parse upload date
                    try:
                        upload_datetime = datetime.strptime(upload_date, '%Y%m%d')
                        if upload_datetime > CUTOFF_24H:
                            videos.append({
                                "title": title,
                                "channel": uploader,
                                "upload_date": upload_date,
                                "view_count": view_count,
                                "url": url,
                                "source": "YouTube",
                                "age_hours": (NOW - upload_datetime).total_seconds() / 3600
                            })
                    except ValueError:
                        # If date parsing fails, include it anyway
                        videos.append({
                            "title": title,
                            "channel": uploader,
                            "upload_date": upload_date,
                            "view_count": view_count,
                            "url": url,
                            "source": "YouTube",
                            "age_hours": 0
                        })
    
    except Exception as e:
        print(f"YouTube search error for '{query}': {e}")
    
    return videos

def get_google_news(query, max_results=5):
    """Get Google News results for query"""
    articles = []
    
    try:
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}+when:1d&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, headers=RSS_HEADERS, timeout=15)
        
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            
            for entry in feed.entries[:max_results]:
                pub_date = datetime(*entry.published_parsed[:6])
                if pub_date > CUTOFF_24H:
                    articles.append({
                        "title": entry.title,
                        "url": entry.link,
                        "published": pub_date.strftime("%Y-%m-%d %H:%M"),
                        "source": "Google News",
                        "age_hours": (NOW - pub_date).total_seconds() / 3600,
                        "query": query
                    })
    
    except Exception as e:
        print(f"Google News error for '{query}': {e}")
    
    return articles

def scan_disasters():
    """Scan H1/H3 - Disasters"""
    print("\n🌋 H1/H3 - DISASTERS SCAN")
    print("=" * 35)
    
    content = []
    
    # Real earthquake data
    print("🔍 Checking EMSC earthquakes...")
    earthquakes = get_emsc_earthquakes(min_magnitude=5.0)  # Lower threshold for more results
    for eq in earthquakes:
        content.append({
            "type": "earthquake",
            "title": f"M{eq['magnitude']} Earthquake - {eq['location']}",
            "details": f"Magnitude {eq['magnitude']} at {eq['time']}",
            "url": eq.get('url', 'https://emsc-csem.org'),
            "priority": "🔴 HIGH" if eq['magnitude'] >= 6.0 else "🟡 MEDIUM",
            "source": "EMSC"
        })
    
    print(f"   Found {len(earthquakes)} earthquakes")
    
    # GDACS disaster alerts
    print("🔍 Checking GDACS alerts...")
    gdacs_alerts = get_gdacs_alerts()
    for alert in gdacs_alerts:
        content.append({
            "type": "disaster_alert",
            "title": alert['title'][:80],
            "details": alert.get('description', '')[:100],
            "url": alert.get('url', 'https://gdacs.org'),
            "priority": "🟡 MEDIUM",
            "source": "GDACS"
        })
    
    print(f"   Found {len(gdacs_alerts)} GDACS alerts")
    
    # YouTube disaster videos
    print("🔍 Searching YouTube for disaster content...")
    disaster_queries = ["earthquake today", "wildfire breaking", "hurricane news", "tornado damage"]
    
    for query in disaster_queries[:2]:  # Limit to avoid timeouts
        videos = search_youtube_videos(query, 3)
        for video in videos:
            content.append({
                "type": "youtube_video",
                "title": video['title'],
                "details": f"Channel: {video['channel']} • {video['view_count']} views",
                "url": video['url'],
                "priority": "🟡 MEDIUM",
                "source": f"YouTube ({query})"
            })
        print(f"   YouTube '{query}': {len(videos)} videos")
    
    # Google News disaster stories
    print("🔍 Searching Google News...")
    news_queries = ["earthquake", "wildfire", "severe weather"]
    
    for query in news_queries:
        articles = get_google_news(query, 3)
        for article in articles:
            content.append({
                "type": "news_article",
                "title": article['title'][:80],
                "details": f"Published {article['published']} ({article['age_hours']:.1f}h ago)",
                "url": article['url'],
                "priority": "🟡 MEDIUM",
                "source": "Google News"
            })
        print(f"   News '{query}': {len(articles)} articles")
    
    return content

def scan_gun_rights():
    """Scan H2 - Gun Rights"""
    print("\n🔫 H2 - GUN RIGHTS SCAN")
    print("=" * 30)
    
    content = []
    
    # YouTube gun rights videos
    print("🔍 Searching YouTube for gun rights content...")
    gun_queries = ["second amendment news", "ATF ruling", "gun rights case"]
    
    for query in gun_queries[:2]:
        videos = search_youtube_videos(query, 3)
        for video in videos:
            content.append({
                "type": "youtube_video",
                "title": video['title'],
                "details": f"Channel: {video['channel']} • {video['view_count']} views",
                "url": video['url'],
                "priority": "🟡 MEDIUM",
                "source": f"YouTube ({query})"
            })
        print(f"   YouTube '{query}': {len(videos)} videos")
    
    # Google News gun rights
    print("🔍 Searching Google News...")
    news_queries = ["gun rights", "second amendment", "ATF ruling"]
    
    for query in news_queries:
        articles = get_google_news(query, 2)
        for article in articles:
            content.append({
                "type": "news_article", 
                "title": article['title'][:80],
                "details": f"Published {article['published']} ({article['age_hours']:.1f}h ago)",
                "url": article['url'],
                "priority": "🟡 MEDIUM",
                "source": "Google News"
            })
        print(f"   News '{query}': {len(articles)} articles")
    
    return content

def scan_taylor_swift():
    """Scan R1 - Taylor Swift"""
    print("\n💫 R1 - TAYLOR SWIFT SCAN")
    print("=" * 35)
    
    content = []
    
    # YouTube Taylor Swift videos
    print("🔍 Searching YouTube for Taylor Swift content...")
    taylor_queries = ["Taylor Swift news", "Travis Kelce Taylor", "Eras Tour"]
    
    for query in taylor_queries[:2]:
        videos = search_youtube_videos(query, 3)
        for video in videos:
            content.append({
                "type": "youtube_video",
                "title": video['title'],
                "details": f"Channel: {video['channel']} • {video['view_count']} views",
                "url": video['url'],
                "priority": "🟡 MEDIUM",
                "source": f"YouTube ({query})"
            })
        print(f"   YouTube '{query}': {len(videos)} videos")
    
    # Google News Taylor Swift
    print("🔍 Searching Google News...")
    news_queries = ["Taylor Swift", "Travis Kelce"]
    
    for query in news_queries:
        articles = get_google_news(query, 3)
        for article in articles:
            content.append({
                "type": "news_article",
                "title": article['title'][:80],
                "details": f"Published {article['published']} ({article['age_hours']:.1f}h ago)",
                "url": article['url'],
                "priority": "🔴 HIGH" if "taylor swift" in article['title'].lower() else "🟡 MEDIUM",
                "source": "Google News"
            })
        print(f"   News '{query}': {len(articles)} articles")
    
    return content

def scan_legal_crime():
    """Scan R2 - Legal/Crime"""
    print("\n⚖️ R2 - LEGAL/CRIME SCAN")
    print("=" * 32)
    
    content = []
    
    # YouTube legal content
    print("🔍 Searching YouTube for legal content...")
    legal_queries = ["court verdict", "trial news", "Supreme Court"]
    
    for query in legal_queries[:2]:
        videos = search_youtube_videos(query, 3)
        for video in videos:
            content.append({
                "type": "youtube_video",
                "title": video['title'],
                "details": f"Channel: {video['channel']} • {video['view_count']} views",
                "url": video['url'],
                "priority": "🟡 MEDIUM",
                "source": f"YouTube ({query})"
            })
        print(f"   YouTube '{query}': {len(videos)} videos")
    
    # Google News legal
    print("🔍 Searching Google News...")
    news_queries = ["Supreme Court", "court verdict", "trial"]
    
    for query in news_queries:
        articles = get_google_news(query, 2)
        for article in articles:
            content.append({
                "type": "news_article",
                "title": article['title'][:80],
                "details": f"Published {article['published']} ({article['age_hours']:.1f}h ago)",
                "url": article['url'],
                "priority": "🟡 MEDIUM",
                "source": "Google News"
            })
        print(f"   News '{query}': {len(articles)} articles")
    
    return content

def scan_tech():
    """Scan N1 - Tech"""
    print("\n💻 N1 - TECH SCAN")
    print("=" * 25)
    
    content = []
    
    # HackerNews (perfect for tech)
    print("🔍 Getting HackerNews trending...")
    hn_stories = get_hackernews_trending()
    for story in hn_stories[:8]:  # Top 8 stories
        content.append({
            "type": "hackernews",
            "title": story['title'][:80],
            "details": f"{story['score']} points • {story.get('comments', 0)} comments",
            "url": story['url'],
            "priority": "🔴 HIGH" if story['score'] > 400 else "🟡 MEDIUM",
            "source": "HackerNews"
        })
    
    print(f"   Found {len(hn_stories)} HackerNews stories")
    
    # YouTube tech content
    print("🔍 Searching YouTube for tech content...")
    tech_queries = ["Elon Musk news", "ChatGPT OpenAI", "AI breakthrough"]
    
    for query in tech_queries[:2]:
        videos = search_youtube_videos(query, 3)
        for video in videos:
            content.append({
                "type": "youtube_video",
                "title": video['title'],
                "details": f"Channel: {video['channel']} • {video['view_count']} views",
                "url": video['url'],
                "priority": "🟡 MEDIUM",
                "source": f"YouTube ({query})"
            })
        print(f"   YouTube '{query}': {len(videos)} videos")
    
    # Google News tech
    print("🔍 Searching Google News...")
    news_queries = ["Elon Musk", "OpenAI", "artificial intelligence"]
    
    for query in news_queries:
        articles = get_google_news(query, 2)
        for article in articles:
            content.append({
                "type": "news_article",
                "title": article['title'][:80],
                "details": f"Published {article['published']} ({article['age_hours']:.1f}h ago)",
                "url": article['url'],
                "priority": "🔴 HIGH" if any(x in article['title'].lower() for x in ['musk', 'openai', 'chatgpt']) else "🟡 MEDIUM",
                "source": "Google News"
            })
        print(f"   News '{query}': {len(articles)} articles")
    
    return content

def run_live_radar():
    """Execute live radar for all channels"""
    print("🚀 LIVE CONTENT RADAR - ALL CHANNELS")
    print("=" * 60)
    print(f"🕐 Started: {NOW.strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Finding latest news & videos (last 24 hours)")
    
    all_content = {}
    
    # Scan each channel
    all_content["H1/H3 - Disasters"] = scan_disasters()
    all_content["H2 - Gun Rights"] = scan_gun_rights() 
    all_content["R1 - Taylor Swift"] = scan_taylor_swift()
    all_content["R2 - Legal/Crime"] = scan_legal_crime()
    all_content["N1 - Tech"] = scan_tech()
    
    # Display results
    print(f"\n🎯 LIVE RADAR RESULTS")
    print("=" * 40)
    
    for channel, content in all_content.items():
        if content:
            print(f"\n{channel} ({len(content)} items):")
            print("-" * 50)
            
            # Sort by priority (HIGH first)
            content.sort(key=lambda x: x['priority'].startswith('🔴'), reverse=True)
            
            for item in content[:8]:  # Show top 8 per channel
                print(f"{item['priority']} {item['title']}")
                print(f"   {item['details']}")
                print(f"   Source: {item['source']}")
                print(f"   🔗 {item['url']}")
                print()
        else:
            print(f"\n{channel}: No recent content found")
    
    # Summary
    total_items = sum(len(content) for content in all_content.values())
    high_priority = sum(len([item for item in content if item['priority'].startswith('🔴')]) for content in all_content.values())
    
    print(f"📊 SUMMARY:")
    print(f"• Total items found: {total_items}")
    print(f"• High priority items: {high_priority}")
    print(f"• Channels scanned: {len(all_content)}")
    print(f"• Time period: Last 24 hours")
    print(f"⏱️ Scan duration: {(datetime.now() - NOW).total_seconds():.1f}s")
    
    return all_content

if __name__ == "__main__":
    run_live_radar()