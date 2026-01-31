#!/usr/bin/env python3
"""
Trello ContentRadar v4 - Multi-source search with strict 24h filtering
- H2: ONLY competitor channels + Google News + Google Trends (no generic YT search)
- All channels: Strict 24h date filtering, no old videos
"""

import json
import subprocess
import requests
import feedparser
from datetime import datetime, timedelta
from pathlib import Path
import sys
import re
from urllib.parse import quote_plus

# Add venv packages
VENV_PATH = Path(__file__).parent / "venv" / "lib"
for p in VENV_PATH.glob("python*/site-packages"):
    sys.path.insert(0, str(p))

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

# YouTube sensitive topics
SENSITIVE_KEYWORDS = [
    "shooting", "killed", "murder", "death", "dead", "dies",
    "suicide", "assault", "rape", "abuse", "racist", "racism",
    "terrorist", "terrorism", "massacre", "slaughter", "gun violence"
]

# Disaster Twitter accounts
DISASTER_TWITTER_ACCOUNTS = ["accuweather", "NWS", "USGSBigQuakes", "breakaborv"]


def is_sensitive_for_youtube(title):
    title_lower = title.lower()
    for kw in SENSITIVE_KEYWORDS:
        if kw in title_lower:
            return True
    return False


def trello_request(method, endpoint, **kwargs):
    url = f"https://api.trello.com/1/{endpoint}"
    params = kwargs.pop('params', {})
    params.update({"key": API_KEY, "token": TOKEN})
    return requests.request(method, url, params=params, **kwargs)


def create_consolidated_card(list_name, title, findings):
    """Create ONE card with ALL findings, flagging sensitive content"""
    list_id = LIST_IDS.get(list_name)
    if not list_id:
        return None
    
    desc_lines = [
        f"📅 Scan: {NOW.strftime('%Y-%m-%d %H:%M')}",
        "⏰ STRICT Last 24 hours only",
        ""
    ]
    
    # Group by source type
    google_news = [f for f in findings if f.get("source_type") == "google_news"]
    trends = [f for f in findings if f.get("source_type") == "trends"]
    twitter = [f for f in findings if f.get("source_type") == "twitter"]
    reddit = [f for f in findings if f.get("source_type") == "reddit"]
    youtube = [f for f in findings if f.get("source_type") == "youtube"]
    
    sensitive_count = 0
    
    def format_item(item):
        nonlocal sensitive_count
        sensitive = is_sensitive_for_youtube(item.get('title', ''))
        if sensitive:
            sensitive_count += 1
        flag = "⚠️ " if sensitive else ""
        source = f"[{item.get('source', '')}] " if item.get('source') else ""
        views = f" • {item['views']:,} views" if item.get('views') else ""
        return f"{flag}{source}{item['title'][:65]}{views}\n  🔗 {item['url']}"
    
    if google_news:
        desc_lines.append("📰 **GOOGLE NEWS:**")
        for item in google_news[:6]:
            desc_lines.append(f"▸ {format_item(item)}\n")
    
    if trends:
        desc_lines.append("📈 **GOOGLE TRENDS:**")
        for item in trends[:5]:
            desc_lines.append(f"▸ {format_item(item)}\n")
    
    if twitter:
        desc_lines.append("🐦 **X/TWITTER:**")
        for item in twitter[:6]:
            desc_lines.append(f"▸ {format_item(item)}\n")
    
    if reddit:
        desc_lines.append("💬 **REDDIT:**")
        for item in reddit[:5]:
            desc_lines.append(f"▸ {format_item(item)}\n")
    
    if youtube:
        desc_lines.append("🎬 **YOUTUBE (Competitors - 24h only):**")
        for item in sorted(youtube, key=lambda x: x.get('views', 0), reverse=True)[:8]:
            desc_lines.append(f"▸ {format_item(item)}\n")
    
    if sensitive_count > 0:
        desc_lines.insert(2, f"⚠️ {sensitive_count} items flagged as potentially sensitive for YouTube")
        desc_lines.insert(3, "")
    
    desc = "\n".join(desc_lines)
    
    total = len(findings)
    full_title = f"{title} ({total} results)"
    if sensitive_count > 0:
        full_title += f" ⚠️{sensitive_count} sensitive"
    
    params = {
        "idList": list_id,
        "name": full_title[:200],
        "desc": desc[:16384],
        "pos": "top"
    }
    
    resp = trello_request("POST", "cards", params=params)
    if resp.status_code == 200:
        print(f"  ✅ Created: {full_title[:60]}...")
        if sensitive_count > 0:
            print(f"  ⚠️  {sensitive_count} items flagged as sensitive")
        return resp.json()
    return None


# ============ SEARCH FUNCTIONS ============

def search_google_news(query, max_results=6):
    """Google News - Last 24h"""
    articles = []
    try:
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}+when:1d&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(requests.get(url, headers=RSS_HEADERS, timeout=15).content)
        
        for entry in feed.entries[:max_results]:
            title = entry.get("title", "")
            source = "News"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                if len(parts) == 2:
                    title, source = parts
            
            articles.append({
                "title": title[:100],
                "url": entry.get("link", ""),
                "source": source,
                "source_type": "google_news"
            })
    except Exception as e:
        print(f"      Google News error: {e}")
    return articles


def search_google_trends_rss():
    """Google Trends via RSS - No rate limits"""
    trends = []
    try:
        url = "https://trends.google.com/trending/rss?geo=US"
        resp = requests.get(url, headers=RSS_HEADERS, timeout=10)
        feed = feedparser.parse(resp.content)
        
        for entry in feed.entries[:8]:
            title = entry.get("title", "")
            traffic = entry.get("ht_approx_traffic", "")
            link = f"https://trends.google.com/trends/explore?q={quote_plus(title)}&geo=US"
            
            trends.append({
                "title": f"🔥 {title} ({traffic})",
                "url": link,
                "source": "Google Trends",
                "source_type": "trends"
            })
    except Exception as e:
        print(f"      Trends error: {e}")
    return trends


def search_twitter_bird(query, max_results=6):
    """Twitter/X via bird CLI"""
    tweets = []
    try:
        result = subprocess.run(
            ["bird", "search", query, "-n", str(max_results), "--plain"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            current_tweet = {}
            for line in result.stdout.split('\n'):
                if line.startswith('@'):
                    if current_tweet.get('title') and current_tweet.get('url'):
                        tweets.append(current_tweet)
                    match = re.match(r'@(\w+)\s*\(([^)]+)\):', line)
                    if match:
                        current_tweet = {"source": f"@{match.group(1)}", "source_type": "twitter"}
                elif line.startswith('url: '):
                    current_tweet["url"] = line[5:].strip()
                elif not line.startswith(('date:', '>', 'PHOTO:', '─', '[')) and line.strip() and 'title' not in current_tweet:
                    current_tweet["title"] = line.strip()[:100]
            
            if current_tweet.get('title') and current_tweet.get('url'):
                tweets.append(current_tweet)
    except Exception as e:
        print(f"      Bird error: {e}")
    return tweets[:max_results]


def search_twitter_account_bird(accounts, max_per=2):
    """Get recent tweets from specific accounts via bird"""
    tweets = []
    for account in accounts[:4]:
        try:
            result = subprocess.run(
                ["bird", "user-tweets", f"@{account}", "-n", str(max_per), "--plain"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                current_tweet = {}
                for line in result.stdout.split('\n'):
                    if line.startswith('@'):
                        if current_tweet.get('title') and current_tweet.get('url'):
                            tweets.append(current_tweet)
                        current_tweet = {"source": f"@{account}", "source_type": "twitter"}
                    elif line.startswith('url: '):
                        current_tweet["url"] = line[5:].strip()
                    elif not line.startswith(('date:', '>', 'PHOTO:', '─', '[')) and line.strip() and 'title' not in current_tweet:
                        current_tweet["title"] = line.strip()[:100]
                
                if current_tweet.get('title') and current_tweet.get('url'):
                    tweets.append(current_tweet)
        except:
            pass
    return tweets


def search_reddit(query, max_results=5):
    """Reddit - Last 24h"""
    posts = []
    try:
        url = f"https://www.reddit.com/search.json?q={quote_plus(query)}&sort=new&t=day&limit={max_results}"
        resp = requests.get(url, headers={**RSS_HEADERS, 'User-Agent': 'ContentRadar/1.0'}, timeout=15)
        data = resp.json()
        
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            created = post.get("created_utc", 0)
            if created < CUTOFF_TIMESTAMP:
                continue
            
            posts.append({
                "title": post.get("title", "")[:100],
                "url": f"https://reddit.com{post.get('permalink', '')}",
                "source": f"r/{post.get('subreddit', 'reddit')}",
                "source_type": "reddit"
            })
    except Exception as e:
        print(f"      Reddit error: {e}")
    return posts


def scan_competitor_channels_strict_24h(channel_key, max_per_competitor=2):
    """
    Scan competitor YouTube channels - STRICT 24h filtering
    Only returns videos uploaded in last 24 hours
    """
    videos = []
    data = COMPETITORS.get(channel_key, {})
    
    for url in data.get("competitors", [])[:10]:
        try:
            result = subprocess.run(
                ["yt-dlp", "--flat-playlist", "-j", 
                 "--dateafter", YESTERDAY,
                 "--playlist-items", f"1:{max_per_competitor * 2}",
                 url],
                capture_output=True, text=True, timeout=45
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        video_id = entry.get("id")
                        if not video_id or len(video_id) != 11:
                            continue
                        
                        # STRICT date check - reject if no date or old
                        upload_date = entry.get("upload_date", "")
                        if not upload_date or upload_date < YESTERDAY:
                            continue
                        
                        videos.append({
                            "title": entry.get("title", "")[:100],
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "views": entry.get("view_count") or 0,
                            "channel": entry.get("channel") or entry.get("uploader") or "",
                            "source": entry.get("channel", "YouTube")[:30],
                            "source_type": "youtube",
                            "upload_date": upload_date
                        })
                    except:
                        pass
        except:
            pass
    
    return videos


def scan_earthquakes_24h():
    """USGS earthquakes - last 24h"""
    alerts = []
    try:
        resp = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson", timeout=10)
        
        for f in resp.json().get("features", []):
            props = f.get("properties", {})
            if props.get("time", 0) / 1000 < CUTOFF_TIMESTAMP:
                continue
            mag = props.get("mag", 0)
            if mag >= 5.0:
                alerts.append({
                    "title": f"M{mag} Earthquake - {props.get('place', 'Unknown')}",
                    "url": props.get("url", ""),
                    "source": "USGS",
                    "source_type": "google_news",
                    "magnitude": mag
                })
    except:
        pass
    return alerts


def scan_weather_24h():
    """NOAA severe weather"""
    alerts = []
    try:
        resp = requests.get("https://api.weather.gov/alerts/active?status=actual&severity=Extreme,Severe",
                          headers={"User-Agent": "ContentRadar/1.0"}, timeout=10)
        for f in resp.json().get("features", [])[:8]:
            props = f.get("properties", {})
            alerts.append({
                "title": f"{props.get('event', '')} - {props.get('areaDesc', '')[:50]}",
                "url": "https://www.weather.gov/alerts",
                "source": f"NOAA {props.get('severity', '')}",
                "source_type": "google_news"
            })
    except:
        pass
    return alerts


# ============ CHANNEL SCANS ============

def run_h1h3_scan():
    """H1/H3 - Disasters: All sources + competitors + Twitter accounts"""
    print(f"\n{'='*55}")
    print("🌋 H1/H3 - DISASTERS SCAN")
    print(f"⏰ STRICT 24 hours only")
    print(f"{'='*55}")
    
    findings = []
    
    # USGS + NOAA
    print("  📡 USGS earthquakes...")
    findings.extend(scan_earthquakes_24h())
    print("  📡 NOAA weather...")
    findings.extend(scan_weather_24h())
    
    # Google News
    print("  📰 Google News...")
    for q in ["earthquake today", "severe weather storm"]:
        findings.extend(search_google_news(q, 4))
    
    # Google Trends
    print("  📈 Google Trends...")
    findings.extend(search_google_trends_rss())
    
    # Twitter via bird
    print("  🐦 Twitter search...")
    findings.extend(search_twitter_bird("earthquake OR severe weather OR tornado", 4))
    print("  🐦 Twitter accounts (@accuweather, @NWS)...")
    findings.extend(search_twitter_account_bird(DISASTER_TWITTER_ACCOUNTS, 2))
    
    # Reddit
    print("  💬 Reddit...")
    findings.extend(search_reddit("earthquake severe weather", 4))
    
    # Competitor channels (strict 24h)
    print("  🎬 Competitor channels (24h only)...")
    findings.extend(scan_competitor_channels_strict_24h("H1_Decryptify", 2))
    findings.extend(scan_competitor_channels_strict_24h("H3_AI_Decoded", 2))
    
    if findings:
        create_consolidated_card("🌋 H1/H3 - Disasters", f"🌋 Disasters - {NOW.strftime('%b %d %H:%M')}", findings)


def run_h2_scan():
    """
    H2 - Gun Rights: ONLY competitors + Google News + Google Trends
    NO generic YouTube searches
    """
    print(f"\n{'='*55}")
    print("🔫 H2 - GUN RIGHTS SCAN")
    print("⏰ STRICT 24 hours | Competitors ONLY (no generic YT)")
    print(f"{'='*55}")
    
    findings = []
    
    # Google News for gun rights
    print("  📰 Google News...")
    for q in ["second amendment", "gun rights", "ATF firearms"]:
        findings.extend(search_google_news(q, 3))
    
    # Google Trends
    print("  📈 Google Trends...")
    trends = search_google_trends_rss()
    # Filter trends for gun-related
    gun_keywords = ["gun", "firearm", "amendment", "atf", "nra", "rifle", "pistol", "carry"]
    gun_trends = [t for t in trends if any(kw in t.get("title", "").lower() for kw in gun_keywords)]
    findings.extend(gun_trends)
    if gun_trends:
        print(f"      Found {len(gun_trends)} gun-related trends")
    
    # Twitter search
    print("  🐦 Twitter...")
    findings.extend(search_twitter_bird("second amendment OR gun rights OR ATF", 4))
    
    # Reddit
    print("  💬 Reddit...")
    findings.extend(search_reddit("gun rights second amendment", 3))
    
    # ONLY competitor channels (strict 24h) - NO generic YouTube search
    print("  🎬 H2 Competitor channels ONLY (24h)...")
    competitor_videos = scan_competitor_channels_strict_24h("H2", 2)
    findings.extend(competitor_videos)
    print(f"      Found {len(competitor_videos)} videos from H2 competitors")
    
    if findings:
        create_consolidated_card("🔫 H2 - Gun Rights", f"🔫 Gun Rights - {NOW.strftime('%b %d %H:%M')}", findings)


def run_r1_scan():
    """R1 - Taylor Swift"""
    print(f"\n{'='*55}")
    print("💫 R1 - TAYLOR SWIFT SCAN")
    print(f"⏰ STRICT 24 hours only")
    print(f"{'='*55}")
    
    findings = []
    
    # Google News
    print("  📰 Google News...")
    for q in ["taylor swift", "travis kelce"]:
        findings.extend(search_google_news(q, 4))
    
    # Google Trends
    print("  📈 Google Trends...")
    trends = search_google_trends_rss()
    taylor_keywords = ["taylor", "swift", "kelce", "travis", "eras"]
    taylor_trends = [t for t in trends if any(kw in t.get("title", "").lower() for kw in taylor_keywords)]
    findings.extend(taylor_trends)
    
    # Twitter
    print("  🐦 Twitter...")
    findings.extend(search_twitter_bird("taylor swift OR travis kelce", 4))
    
    # Reddit
    print("  💬 Reddit...")
    findings.extend(search_reddit("taylor swift travis kelce", 3))
    
    # Competitors
    print("  🎬 Competitor channels (24h)...")
    findings.extend(scan_competitor_channels_strict_24h("R1_JUST_HAPPENED", 2))
    
    if findings:
        create_consolidated_card("💫 R1 - Taylor Swift", f"💫 Taylor Swift - {NOW.strftime('%b %d %H:%M')}", findings)


def run_r2_scan():
    """R2 - Legal/Crime"""
    print(f"\n{'='*55}")
    print("⚖️ R2 - LEGAL/CRIME SCAN")
    print(f"⏰ STRICT 24 hours only")
    print(f"{'='*55}")
    
    findings = []
    
    # Google News
    print("  📰 Google News...")
    for q in ["court verdict today", "crime trial"]:
        findings.extend(search_google_news(q, 4))
    
    # Google Trends
    print("  📈 Google Trends...")
    findings.extend(search_google_trends_rss())
    
    # Twitter
    print("  🐦 Twitter...")
    findings.extend(search_twitter_bird("court verdict OR trial OR crime news", 4))
    
    # Reddit
    print("  💬 Reddit...")
    findings.extend(search_reddit("court trial verdict crime", 3))
    
    # Competitors
    print("  🎬 Competitor channels (24h)...")
    findings.extend(scan_competitor_channels_strict_24h("R2_CAUGHT_NOW", 2))
    
    if findings:
        create_consolidated_card("⚖️ R2 - Legal/Crime", f"⚖️ Legal/Crime - {NOW.strftime('%b %d %H:%M')}", findings)


def run_full_scan():
    """Run all channel scans"""
    print("=" * 55)
    print(f"CONTENTADAR FULL SCAN - {NOW.strftime('%Y-%m-%d %H:%M')}")
    print("⏰ STRICT 24 hours | H2: Competitors only")
    print("=" * 55)
    
    run_h1h3_scan()
    run_h2_scan()
    run_r1_scan()
    run_r2_scan()
    
    print("\n" + "=" * 55)
    print("✅ FULL SCAN COMPLETE")
    print("=" * 55)


def search_and_add(list_name, card_title, search_queries, twitter_accounts=None):
    """Custom search"""
    print(f"\n{'='*55}")
    print(f"🔍 {card_title}")
    print(f"⏰ STRICT 24 hours only")
    print(f"{'='*55}")
    
    findings = []
    
    for query in search_queries:
        print(f"  🔍 '{query}':")
        
        findings.extend(search_google_news(query, 5))
        print(f"      📰 Google News: {len([f for f in findings if f.get('source_type')=='google_news'])}")
        
        findings.extend(search_twitter_bird(query, 4))
        print(f"      🐦 Twitter: done")
        
        findings.extend(search_reddit(query, 4))
        print(f"      💬 Reddit: done")
    
    # Add trends
    findings.extend(search_google_trends_rss())
    
    if twitter_accounts:
        findings.extend(search_twitter_account_bird(twitter_accounts, 2))
    
    if findings:
        create_consolidated_card(list_name, card_title, findings)
    else:
        print("  ⚠️ No results found in last 24 hours")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Full scan all channels")
    parser.add_argument("--h1h3", action="store_true", help="Scan H1/H3 disasters")
    parser.add_argument("--h2", action="store_true", help="Scan H2 gun rights (competitors only)")
    parser.add_argument("--r1", action="store_true", help="Scan R1 Taylor Swift")
    parser.add_argument("--r2", action="store_true", help="Scan R2 legal/crime")
    parser.add_argument("--search", nargs="+", help="Custom search queries")
    parser.add_argument("--channel", default="⚖️ R2 - Legal/Crime")
    parser.add_argument("--title", help="Card title")
    parser.add_argument("--twitter", nargs="+", help="Twitter accounts to check")
    
    args = parser.parse_args()
    
    if args.full:
        run_full_scan()
    elif args.h1h3:
        run_h1h3_scan()
    elif args.h2:
        run_h2_scan()
    elif args.r1:
        run_r1_scan()
    elif args.r2:
        run_r2_scan()
    elif args.search:
        title = args.title or f"Research - {NOW.strftime('%b %d %H:%M')}"
        search_and_add(args.channel, title, args.search, args.twitter)
    else:
        run_full_scan()
