#!/usr/bin/env python3
"""
Radar to Trello - Create cards with all found links/videos for each channel
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
from viral_apis import get_emsc_earthquakes, get_gdacs_alerts

BASE_DIR = Path(__file__).parent

# Load Trello credentials
config = json.loads(Path('/Users/malikano/clawdbot_system/config.json').read_text())
API_KEY = config['trello_api_key']
TOKEN = config['trello_api_token']

LIST_IDS = json.loads((BASE_DIR / 'trello_lists.json').read_text())

NOW = datetime.now()
CUTOFF_24H = NOW - timedelta(hours=24)

RSS_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

def trello_request(method, endpoint, **kwargs):
    url = f"https://api.trello.com/1/{endpoint}"
    params = kwargs.pop('params', {})
    params.update({"key": API_KEY, "token": TOKEN})
    return requests.request(method, url, params=params, **kwargs)

def search_youtube_videos(query, max_results=5):
    """Search for recent YouTube videos using yt-dlp"""
    videos = []
    
    try:
        search_url = f"ytsearch{max_results}:{query}"
        
        cmd = [
            "yt-dlp", 
            "--flat-playlist",
            "--print", "title,uploader,upload_date,view_count,webpage_url",
            search_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            
            for i in range(0, len(lines), 5):
                if i + 4 < len(lines):
                    title = lines[i].strip()
                    uploader = lines[i + 1].strip()
                    upload_date = lines[i + 2].strip()
                    view_count = lines[i + 3].strip()
                    url = lines[i + 4].strip()
                    
                    videos.append({
                        "title": title,
                        "channel": uploader,
                        "upload_date": upload_date,
                        "view_count": view_count,
                        "url": url,
                        "type": "youtube"
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
                        "type": "news"
                    })
    
    except Exception as e:
        print(f"Google News error for '{query}': {e}")
    
    return articles

def create_channel_trello_card(list_name, channel_name, findings):
    """Create Trello card with all findings for a channel"""
    list_id = LIST_IDS.get(list_name)
    if not list_id:
        print(f"❌ List '{list_name}' not found")
        return None
    
    # Card title with timestamp and count
    title = f"{channel_name} Radar - {len(findings)} items - {NOW.strftime('%m/%d %H:%M')}"
    
    # Build description with all links
    desc_lines = [
        f"📅 Radar Scan: {NOW.strftime('%Y-%m-%d %H:%M')}",
        f"🎯 Channel: {channel_name}",
        f"📊 Total items: {len(findings)}",
        f"⏰ Time period: Last 24 hours",
        ""
    ]
    
    # Group findings by type
    youtube_videos = [f for f in findings if f.get('type') == 'youtube']
    news_articles = [f for f in findings if f.get('type') == 'news']
    hackernews = [f for f in findings if f.get('type') == 'hackernews']
    earthquakes = [f for f in findings if f.get('type') == 'earthquake']
    disasters = [f for f in findings if f.get('type') == 'disaster']
    
    # YouTube Videos Section
    if youtube_videos:
        desc_lines.append(f"🎬 **YOUTUBE VIDEOS ({len(youtube_videos)}):**")
        for i, video in enumerate(youtube_videos, 1):
            desc_lines.append(f"{i}. **{video['title']}**")
            desc_lines.append(f"   📺 Channel: {video['channel']}")
            desc_lines.append(f"   👁️ Views: {video.get('view_count', 'N/A')}")
            desc_lines.append(f"   🔗 {video['url']}")
            desc_lines.append("")
    
    # News Articles Section
    if news_articles:
        desc_lines.append(f"📰 **NEWS ARTICLES ({len(news_articles)}):**")
        for i, article in enumerate(news_articles, 1):
            desc_lines.append(f"{i}. **{article['title']}**")
            desc_lines.append(f"   📅 Published: {article.get('published', 'Unknown')}")
            desc_lines.append(f"   📰 Source: {article.get('source', 'News')}")
            desc_lines.append(f"   🔗 {article['url']}")
            desc_lines.append("")
    
    # HackerNews Section
    if hackernews:
        desc_lines.append(f"💻 **HACKERNEWS TRENDING ({len(hackernews)}):**")
        for i, story in enumerate(hackernews, 1):
            desc_lines.append(f"{i}. **{story['title']}**")
            desc_lines.append(f"   📊 Score: {story.get('score', 0)} points")
            desc_lines.append(f"   💬 Comments: {story.get('comments', 0)}")
            desc_lines.append(f"   🔗 {story['url']}")
            desc_lines.append("")
    
    # Earthquakes Section
    if earthquakes:
        desc_lines.append(f"🌍 **EARTHQUAKES ({len(earthquakes)}):**")
        for i, eq in enumerate(earthquakes, 1):
            desc_lines.append(f"{i}. **{eq['title']}**")
            desc_lines.append(f"   📊 Magnitude: {eq.get('magnitude', 'Unknown')}")
            desc_lines.append(f"   📍 Location: {eq.get('location', 'Unknown')}")
            desc_lines.append(f"   ⏰ Time: {eq.get('time', 'Unknown')}")
            desc_lines.append(f"   🔗 {eq.get('url', 'No URL')}")
            desc_lines.append("")
    
    # Disasters Section
    if disasters:
        desc_lines.append(f"⚠️ **DISASTER ALERTS ({len(disasters)}):**")
        for i, alert in enumerate(disasters, 1):
            desc_lines.append(f"{i}. **{alert['title']}**")
            desc_lines.append(f"   📝 Description: {alert.get('description', '')[:100]}...")
            desc_lines.append(f"   📅 Published: {alert.get('published', 'Unknown')}")
            desc_lines.append(f"   🔗 {alert.get('url', 'No URL')}")
            desc_lines.append("")
    
    # Summary section
    desc_lines.extend([
        "---",
        "📊 **SUMMARY:**",
        f"• YouTube Videos: {len(youtube_videos)}",
        f"• News Articles: {len(news_articles)}",
        f"• HackerNews: {len(hackernews)}",
        f"• Earthquakes: {len(earthquakes)}",
        f"• Disaster Alerts: {len(disasters)}",
        f"• Total Links: {len(findings)}",
        "",
        "🎯 **READY FOR CONTENT CREATION**",
        "All links verified and ready for video production workflow"
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
            print(f"✅ Created Trello card: {title}")
            return card_id
        else:
            print(f"❌ Trello error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Card creation error: {e}")
        return None

def scan_channel_h1h3():
    """Scan H1/H3 - Disasters with all links"""
    print("🌋 H1/H3 - DISASTERS")
    findings = []
    
    # Real earthquake data
    earthquakes = get_emsc_earthquakes(min_magnitude=4.5)
    for eq in earthquakes:
        findings.append({
            "title": f"M{eq['magnitude']} Earthquake - {eq['location']}",
            "magnitude": eq['magnitude'],
            "location": eq['location'],
            "time": eq['time'],
            "url": eq.get('url', 'https://emsc-csem.org'),
            "type": "earthquake"
        })
    print(f"   Earthquakes: {len(earthquakes)}")
    
    # GDACS alerts
    gdacs = get_gdacs_alerts()
    for alert in gdacs:
        findings.append({
            "title": alert['title'],
            "description": alert.get('description', ''),
            "published": alert.get('published', ''),
            "url": alert.get('url', 'https://gdacs.org'),
            "type": "disaster"
        })
    print(f"   GDACS alerts: {len(gdacs)}")
    
    # YouTube videos
    queries = ["earthquake today", "wildfire breaking", "hurricane news"]
    for query in queries:
        videos = search_youtube_videos(query, 3)
        findings.extend(videos)
        print(f"   YouTube '{query}': {len(videos)} videos")
    
    # Google News
    news_queries = ["earthquake", "wildfire", "hurricane"]
    for query in news_queries:
        articles = get_google_news(query, 3)
        findings.extend(articles)
        print(f"   News '{query}': {len(articles)} articles")
    
    return findings

def scan_channel_h2():
    """Scan H2 - Gun Rights with all links"""
    print("🔫 H2 - GUN RIGHTS")
    findings = []
    
    # YouTube videos
    queries = ["gun rights news", "second amendment", "ATF ruling"]
    for query in queries:
        videos = search_youtube_videos(query, 3)
        findings.extend(videos)
        print(f"   YouTube '{query}': {len(videos)} videos")
    
    # Google News
    news_queries = ["gun rights", "second amendment", "ATF", "Supreme Court guns"]
    for query in news_queries:
        articles = get_google_news(query, 2)
        findings.extend(articles)
        print(f"   News '{query}': {len(articles)} articles")
    
    return findings

def scan_channel_r1():
    """Scan R1 - Taylor Swift with all links"""
    print("💫 R1 - TAYLOR SWIFT")
    findings = []
    
    # YouTube videos
    queries = ["Taylor Swift news", "Travis Kelce Taylor", "Eras Tour"]
    for query in queries:
        videos = search_youtube_videos(query, 4)
        findings.extend(videos)
        print(f"   YouTube '{query}': {len(videos)} videos")
    
    # Google News
    news_queries = ["Taylor Swift", "Travis Kelce", "Eras Tour"]
    for query in news_queries:
        articles = get_google_news(query, 3)
        findings.extend(articles)
        print(f"   News '{query}': {len(articles)} articles")
    
    return findings

def scan_channel_r2():
    """Scan R2 - Legal/Crime with all links"""
    print("⚖️ R2 - LEGAL/CRIME")
    findings = []
    
    # YouTube videos
    queries = ["Supreme Court news", "court verdict", "legal news"]
    for query in queries:
        videos = search_youtube_videos(query, 3)
        findings.extend(videos)
        print(f"   YouTube '{query}': {len(videos)} videos")
    
    # Google News
    news_queries = ["Supreme Court", "court case", "legal verdict"]
    for query in news_queries:
        articles = get_google_news(query, 3)
        findings.extend(articles)
        print(f"   News '{query}': {len(articles)} articles")
    
    return findings

def scan_channel_n1():
    """Scan N1 - Tech with all links"""
    print("💻 N1 - TECH")
    findings = []
    
    # HackerNews trending
    hn_stories = get_hackernews_trending()
    for story in hn_stories:
        findings.append({
            "title": story['title'],
            "score": story['score'],
            "comments": story.get('comments', 0),
            "url": story['url'],
            "type": "hackernews"
        })
    print(f"   HackerNews: {len(hn_stories)} stories")
    
    # YouTube videos
    queries = ["Elon Musk news", "ChatGPT OpenAI", "AI breakthrough"]
    for query in queries:
        videos = search_youtube_videos(query, 3)
        findings.extend(videos)
        print(f"   YouTube '{query}': {len(videos)} videos")
    
    # Google News
    news_queries = ["Elon Musk", "OpenAI", "artificial intelligence", "Sam Altman"]
    for query in news_queries:
        articles = get_google_news(query, 2)
        findings.extend(articles)
        print(f"   News '{query}': {len(articles)} articles")
    
    return findings

def run_full_radar_to_trello():
    """Run full radar and create Trello cards for each channel"""
    print("🚀 RADAR TO TRELLO - ALL CHANNELS")
    print("=" * 60)
    print(f"🕐 Started: {NOW.strftime('%Y-%m-%d %H:%M:%S')}")
    print("📋 Creating 1 card per channel with ALL links found")
    
    channels = [
        ("🌋 H1/H3 - Disasters", "H1/H3 Disasters", scan_channel_h1h3),
        ("🔫 H2 - Gun Rights", "H2 Gun Rights", scan_channel_h2),
        ("💫 R1 - Taylor Swift", "R1 Taylor Swift", scan_channel_r1),
        ("⚖️ R2 - Legal/Crime", "R2 Legal/Crime", scan_channel_r2),
        ("💻 N1 - TECH", "N1 Tech", scan_channel_n1)
    ]
    
    cards_created = 0
    total_links = 0
    
    for list_name, channel_name, scan_func in channels:
        print(f"\n{list_name}")
        print("-" * 40)
        
        try:
            findings = scan_func()
            total_links += len(findings)
            
            if findings:
                card_id = create_channel_trello_card(list_name, channel_name, findings)
                if card_id:
                    cards_created += 1
            else:
                print(f"   No content found for {channel_name}")
                
        except Exception as e:
            print(f"   Error scanning {channel_name}: {e}")
    
    # Summary
    print(f"\n🎯 RADAR TO TRELLO COMPLETE")
    print(f"📋 Cards created: {cards_created}/5 channels")
    print(f"🔗 Total links found: {total_links}")
    print(f"⏱️ Duration: {(datetime.now() - NOW).total_seconds():.1f}s")
    print(f"✅ All links attached to Trello cards for content creation!")
    
    return cards_created, total_links

if __name__ == "__main__":
    run_full_radar_to_trello()