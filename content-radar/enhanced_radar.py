#!/usr/bin/env python3
"""
Enhanced ContentRadar - Multi-source monitoring for YouTube content creation
Uses: YouTube RSS, Google Trends, Celebrity News RSS, USGS, NOAA
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

# Add venv packages to path
VENV_PATH = Path(__file__).parent / "venv" / "lib"
for p in VENV_PATH.glob("python*/site-packages"):
    sys.path.insert(0, str(p))

import feedparser
import requests
from bs4 import BeautifulSoup

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

# Paths
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
COMPETITORS_PATH = BASE_DIR.parent / "competitors.json"
STATE_PATH = BASE_DIR / "radar_state.json"
ALERTS_PATH = BASE_DIR / "alerts.json"

# Celebrity news RSS feeds (working ones)
CELEBRITY_RSS_FEEDS = {
    "eonline": "https://www.eonline.com/syndication/rss/popular",
    "usweekly": "https://www.usmagazine.com/feed/",
    "pagesix": "https://pagesix.com/feed/",
    "accesshollywood": "https://www.accesshollywood.com/feed/",
    "extratv": "https://extratv.com/feed/",
}

# HTTP headers for RSS fetching
RSS_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

# Taylor Swift related keywords for filtering
TAYLOR_SWIFT_KEYWORDS = [
    "taylor swift", "travis kelce", "swifties", "eras tour",
    "taylor and travis", "kelce swift", "chiefs taylor",
    "taylor boyfriend", "swift relationship", "taylor travis",
    "tayvis", "traylor", "swift kelce", "taylor nfl",
    "taylor super bowl", "taylor concert", "swift dating",
    "taylor grammy", "taylor album", "reputation tour",
    "midnights tour", "swift family", "taylor parents"
]


def load_state():
    """Load or create state file"""
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {
        "seen_videos": {},
        "seen_articles": {},
        "last_trends_check": None,
        "last_check": {}
    }


def save_state(state):
    """Save state file"""
    STATE_PATH.write_text(json.dumps(state, indent=2, default=str))


def load_config():
    """Load config file"""
    return json.loads(CONFIG_PATH.read_text())


def load_competitors():
    """Load competitors file"""
    return json.loads(COMPETITORS_PATH.read_text())


def get_channel_id_from_url(url):
    """Extract channel ID from YouTube URL using yt-dlp"""
    try:
        # Handle different URL formats
        if "@" in url:
            # Modern @handle format
            result = subprocess.run(
                ["yt-dlp", "--flat-playlist", "-J", url],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("channel_id") or data.get("uploader_id")
        elif "channel/" in url:
            # Direct channel ID
            match = re.search(r"channel/([^/?\s]+)", url)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Error getting channel ID for {url}: {e}")
    return None


def get_youtube_rss_videos(channel_url, limit=5):
    """Get recent videos from YouTube channel via RSS feed"""
    videos = []
    
    # Try to get channel ID
    channel_id = get_channel_id_from_url(channel_url)
    if not channel_id:
        # Fallback: try to scrape channel page for ID
        try:
            resp = requests.get(channel_url, timeout=10)
            match = re.search(r'"channelId":"([^"]+)"', resp.text)
            if match:
                channel_id = match.group(1)
        except:
            pass
    
    if not channel_id:
        return videos
    
    # YouTube RSS feed URL
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:limit]:
            videos.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
                "channel": feed.feed.get("title", "Unknown"),
                "channel_id": channel_id,
                "video_id": entry.get("yt_videoid", ""),
                "views": entry.get("media_statistics", {}).get("views", 0) if hasattr(entry, "media_statistics") else 0
            })
    except Exception as e:
        print(f"Error fetching RSS for {channel_url}: {e}")
    
    return videos


def get_celebrity_news(keywords=None, limit=10):
    """Fetch celebrity news from RSS feeds, optionally filtered by keywords"""
    if keywords is None:
        keywords = TAYLOR_SWIFT_KEYWORDS
    
    articles = []
    
    for source, url in CELEBRITY_RSS_FEEDS.items():
        try:
            # Use requests with headers to avoid blocks
            resp = requests.get(url, headers=RSS_HEADERS, timeout=15)
            feed = feedparser.parse(resp.content)
            
            for entry in feed.entries[:30]:  # Check more entries for filtering
                title = entry.get("title", "").lower()
                summary = entry.get("summary", "").lower()
                
                # Check if any keyword matches
                if keywords:
                    if not any(kw.lower() in title or kw.lower() in summary for kw in keywords):
                        continue
                
                articles.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "source": source,
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", "")[:200] if entry.get("summary") else ""
                })
                
                if len(articles) >= limit * 2:  # Get extras before dedup
                    break
        except Exception as e:
            print(f"Error fetching {source}: {e}")
    
    return articles[:limit]


def get_google_trends(keywords=None):
    """Get Google Trends data for keywords"""
    if not PYTRENDS_AVAILABLE:
        return {"error": "pytrends not installed"}
    
    if keywords is None:
        keywords = ["taylor swift", "travis kelce", "eras tour", "swifties", "taylor swift news"]
    
    # Limit to 5 keywords (Google Trends limit)
    keywords = keywords[:5]
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        pytrends.build_payload(keywords, timeframe='now 1-d', geo='US')
        
        # Get interest over time
        interest = pytrends.interest_over_time()
        
        # Get related queries
        related = pytrends.related_queries()
        
        # Get trending searches
        trending = pytrends.trending_searches(pn='united_states')
        
        return {
            "interest": interest.to_dict() if not interest.empty else {},
            "related_queries": {k: v.get("top", {}).to_dict() if v.get("top") is not None else {} for k, v in related.items()},
            "trending_now": trending.values.flatten().tolist()[:20] if not trending.empty else []
        }
    except Exception as e:
        return {"error": str(e)}


def check_usgs_earthquakes(min_magnitude=5.5):
    """Check USGS for recent significant earthquakes"""
    alerts = []
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            mag = props.get("mag", 0)
            
            if mag >= min_magnitude:
                alerts.append({
                    "type": "earthquake",
                    "magnitude": mag,
                    "place": props.get("place", "Unknown"),
                    "time": datetime.fromtimestamp(props.get("time", 0) / 1000).isoformat(),
                    "url": props.get("url", ""),
                    "tsunami": props.get("tsunami", 0) == 1
                })
    except Exception as e:
        print(f"USGS error: {e}")
    
    return alerts


def check_noaa_weather(severity=["Extreme", "Severe"]):
    """Check NOAA for severe weather alerts"""
    alerts = []
    try:
        url = "https://api.weather.gov/alerts/active"
        headers = {"User-Agent": "ContentRadar/1.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            sev = props.get("severity", "")
            
            if sev in severity:
                alerts.append({
                    "type": "weather",
                    "severity": sev,
                    "event": props.get("event", ""),
                    "headline": props.get("headline", ""),
                    "areas": props.get("areaDesc", ""),
                    "effective": props.get("effective", ""),
                    "expires": props.get("expires", "")
                })
    except Exception as e:
        print(f"NOAA error: {e}")
    
    return alerts


def scan_competitors(channel_key, limit_per_channel=3):
    """Scan competitor channels for new videos"""
    competitors = load_competitors()
    state = load_state()
    
    new_videos = []
    channel_data = competitors.get(channel_key, {})
    
    for url in channel_data.get("competitors", []):
        videos = get_youtube_rss_videos(url, limit=limit_per_channel)
        for video in videos:
            video_id = video.get("video_id")
            if video_id and video_id not in state.get("seen_videos", {}):
                new_videos.append(video)
                state.setdefault("seen_videos", {})[video_id] = {
                    "first_seen": datetime.now().isoformat(),
                    "channel_key": channel_key
                }
    
    save_state(state)
    return new_videos


def run_full_scan(channel_keys=None):
    """Run a full scan of all sources"""
    config = load_config()
    competitors = load_competitors()
    
    if channel_keys is None:
        channel_keys = list(competitors.keys())
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "channels": {},
        "alerts": {
            "earthquakes": [],
            "weather": []
        },
        "celebrity_news": [],
        "trends": {}
    }
    
    # Scan each channel's competitors
    for key in channel_keys:
        if key in competitors:
            print(f"Scanning {key}...")
            results["channels"][key] = {
                "niche": competitors[key].get("niche", ""),
                "new_videos": scan_competitors(key, limit_per_channel=3)
            }
    
    # Check disaster alerts for H1/H3
    disaster_channels = ["H1_Decryptify", "H3_AI_Decoded"]
    if any(k in channel_keys for k in disaster_channels):
        print("Checking USGS earthquakes...")
        results["alerts"]["earthquakes"] = check_usgs_earthquakes()
        print("Checking NOAA weather...")
        results["alerts"]["weather"] = check_noaa_weather()[:10]  # Limit weather alerts
    
    # Check Taylor Swift news for R1
    if "R1_JUST_HAPPENED" in channel_keys:
        print("Checking celebrity news...")
        results["celebrity_news"] = get_celebrity_news(TAYLOR_SWIFT_KEYWORDS)
        
        if PYTRENDS_AVAILABLE:
            print("Checking Google Trends...")
            results["trends"] = get_google_trends()
    
    # Save results
    ALERTS_PATH.write_text(json.dumps(results, indent=2, default=str))
    
    return results


def format_summary(results):
    """Format scan results as a readable summary"""
    lines = [f"📡 ContentRadar Scan - {results['timestamp'][:16]}"]
    lines.append("=" * 40)
    
    # Disaster alerts
    quakes = results.get("alerts", {}).get("earthquakes", [])
    if quakes:
        lines.append(f"\n🌋 EARTHQUAKES ({len(quakes)}):")
        for q in quakes[:5]:
            tsunami = " ⚠️TSUNAMI WARNING" if q.get("tsunami") else ""
            lines.append(f"  • M{q['magnitude']} - {q['place']}{tsunami}")
    
    weather = results.get("alerts", {}).get("weather", [])
    if weather:
        lines.append(f"\n🌪️ SEVERE WEATHER ({len(weather)}):")
        for w in weather[:5]:
            lines.append(f"  • {w['severity']}: {w['event']} - {w['areas'][:50]}...")
    
    # Celebrity news (for R1)
    news = results.get("celebrity_news", [])
    if news:
        lines.append(f"\n💫 TAYLOR SWIFT NEWS ({len(news)}):")
        for n in news[:5]:
            lines.append(f"  • [{n['source'].upper()}] {n['title'][:60]}...")
    
    # New competitor videos
    for channel, data in results.get("channels", {}).items():
        videos = data.get("new_videos", [])
        if videos:
            lines.append(f"\n📺 {channel} - NEW VIDEOS ({len(videos)}):")
            for v in videos[:5]:
                lines.append(f"  • {v['channel']}: {v['title'][:50]}...")
    
    # Trends
    trends = results.get("trends", {})
    if trends and not trends.get("error"):
        trending = trends.get("trending_now", [])[:10]
        if trending:
            lines.append(f"\n📈 TRENDING NOW (US):")
            lines.append(f"  {', '.join(trending[:5])}")
    
    return "\n".join(lines)


# Dashboard integration
def add_to_dashboard(item_type, title, source, url, priority="high", 
                     views=None, subscribers=None, posted_at=None, tags=None):
    """Add an item to the dashboard"""
    try:
        from dashboard_manager import add_card
        add_card(
            title=title,
            content_type=item_type,
            source=source,
            url=url,
            priority=priority,
            views=views,
            subscribers=subscribers,
            posted_at=posted_at,
            tags=tags
        )
        return True
    except Exception as e:
        print(f"Dashboard error: {e}")
        return False


def scan_and_add_to_dashboard(channel_key=None, add_dashboard=True):
    """Scan sources and automatically add to dashboard"""
    results = {
        "news_added": 0,
        "videos_added": 0,
        "news": [],
        "videos": []
    }
    
    # If R1 (Taylor Swift), get celebrity news
    if channel_key is None or "R1" in str(channel_key):
        news = get_celebrity_news(TAYLOR_SWIFT_KEYWORDS, limit=10)
        for n in news:
            results["news"].append(n)
            if add_dashboard:
                # First news item is HIGH priority, rest are MEDIUM
                priority = "high" if results["news_added"] == 0 else "medium"
                if add_to_dashboard(
                    "news",
                    n["title"],
                    n["source"],
                    n["url"],
                    priority=priority,
                    tags=["taylor-swift", "celebrity"]
                ):
                    results["news_added"] += 1
    
    # Scan competitor videos for outliers
    if channel_key:
        competitors = load_competitors()
        channel_data = competitors.get(channel_key, {})
        state = load_state()
        
        for url in channel_data.get("competitors", [])[:10]:
            videos = get_youtube_rss_videos(url, limit=3)
            for video in videos:
                video_id = video.get("video_id")
                if video_id and video_id not in state.get("seen_videos", {}):
                    results["videos"].append(video)
                    
                    # Mark as seen
                    state.setdefault("seen_videos", {})[video_id] = {
                        "first_seen": datetime.now().isoformat()
                    }
                    
                    if add_dashboard:
                        # First video is HIGH, rest are MEDIUM
                        priority = "high" if results["videos_added"] == 0 else "medium"
                        if add_to_dashboard(
                            "video",
                            video["title"],
                            video.get("channel", "Unknown"),
                            video["url"],
                            priority=priority,
                            views=video.get("views"),
                            posted_at=video.get("published"),
                            tags=[channel_key.split("_")[0].lower()]
                        ):
                            results["videos_added"] += 1
        
        save_state(state)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced ContentRadar")
    parser.add_argument("--channels", nargs="*", help="Specific channels to scan")
    parser.add_argument("--taylor", action="store_true", help="Only Taylor Swift news")
    parser.add_argument("--disasters", action="store_true", help="Only disaster alerts")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--dashboard", action="store_true", help="Add results to dashboard")
    
    args = parser.parse_args()
    
    if args.taylor:
        print("Fetching Taylor Swift news...")
        if args.dashboard:
            results = scan_and_add_to_dashboard("R1_JUST_HAPPENED", add_dashboard=True)
            print(f"Added {results['news_added']} news, {results['videos_added']} videos to dashboard")
        else:
            news = get_celebrity_news(TAYLOR_SWIFT_KEYWORDS, limit=20)
            if args.json:
                print(json.dumps(news, indent=2))
            else:
                for n in news:
                    print(f"[{n['source'].upper()}] {n['title']}")
                    print(f"  {n['url']}\n")
    elif args.disasters:
        print("Checking disaster alerts...")
        quakes = check_usgs_earthquakes()
        weather = check_noaa_weather()
        
        if args.dashboard:
            # Add significant quakes to dashboard
            for q in quakes[:3]:
                add_to_dashboard(
                    "news",
                    f"M{q['magnitude']} Earthquake - {q['place']}",
                    "USGS",
                    q.get("url", "https://earthquake.usgs.gov"),
                    priority="high" if q['magnitude'] >= 6.0 else "medium",
                    tags=["earthquake", "disaster"]
                )
            print(f"Added {min(3, len(quakes))} earthquake alerts to dashboard")
        
        if args.json:
            print(json.dumps({"earthquakes": quakes, "weather": weather}, indent=2))
        else:
            print(f"\n🌋 Earthquakes: {len(quakes)}")
            for q in quakes:
                print(f"  M{q['magnitude']} - {q['place']}")
            print(f"\n🌪️ Severe Weather: {len(weather)}")
            for w in weather[:10]:
                print(f"  {w['event']} - {w['areas'][:50]}")
    else:
        if args.dashboard:
            for ch in (args.channels or ["R1_JUST_HAPPENED", "H1_Decryptify", "H3_AI_Decoded"]):
                results = scan_and_add_to_dashboard(ch, add_dashboard=True)
                print(f"{ch}: Added {results['news_added']} news, {results['videos_added']} videos")
        else:
            results = run_full_scan(args.channels)
            if args.json:
                print(json.dumps(results, indent=2, default=str))
            else:
                print(format_summary(results))
