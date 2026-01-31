#!/usr/bin/env python3
"""
Full Channel Radar - All channels including new N1 - TECH
H1/H3: Disasters, H2: Gun Rights, R1: Taylor Swift, R2: Legal/Crime, N1: Tech
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

# Import our APIs
from mega_viral_apis import (
    get_newsapi_headlines, get_gnews_api, get_hackernews_trending,
    get_gdelt_events, get_enhanced_reddit_all_channels
)
from simple_google_trends import get_channel_trends
from viral_apis import (
    get_emsc_earthquakes, get_nasa_fires, get_gdacs_alerts,
    get_congress_bills, get_federal_register, get_supreme_court_cases
)

BASE_DIR = Path(__file__).parent

# Load Trello credentials
config = json.loads(Path('/Users/malikano/clawdbot_system/config.json').read_text())
API_KEY = config['trello_api_key']
TOKEN = config['trello_api_token']

LIST_IDS = json.loads((BASE_DIR / 'trello_lists.json').read_text())

# Time filters
NOW = datetime.now()
CUTOFF_24H = NOW - timedelta(hours=24)

RSS_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

def trello_request(method, endpoint, **kwargs):
    url = f"https://api.trello.com/1/{endpoint}"
    params = kwargs.pop('params', {})
    params.update({"key": API_KEY, "token": TOKEN})
    return requests.request(method, url, params=params, **kwargs)

def get_tech_news_content():
    """Get tech-focused content for N1 channel"""
    tech_content = []
    
    # Tech personalities to monitor
    tech_keywords = [
        "Elon Musk", "Sam Altman", "OpenAI", "Tesla", "SpaceX", "Neuralink",
        "ChatGPT", "GPT", "artificial intelligence", "AI breakthrough",
        "machine learning", "neural network", "AGI", "AI safety",
        "tech startup", "Silicon Valley", "venture capital", "IPO tech",
        "cryptocurrency", "blockchain", "Bitcoin", "Ethereum",
        "Apple", "Google", "Microsoft", "Amazon", "Meta", "Netflix",
        "tech stock", "tech earnings", "tech acquisition", "tech layoffs",
        "quantum computing", "robotics", "autonomous vehicles", "EV",
        "cloud computing", "cybersecurity", "data breach", "tech regulation"
    ]
    
    print("🔍 Getting tech news content...")
    
    # HackerNews (perfect for tech)
    try:
        hn_stories = get_hackernews_trending()
        for story in hn_stories:
            story['channel'] = 'tech'
            story['priority'] = 'HIGH' if story.get('score', 0) > 300 else 'MEDIUM'
            tech_content.append(story)
        print(f"   HackerNews: {len(hn_stories)} stories")
    except Exception as e:
        print(f"   HackerNews error: {e}")
    
    # Google News for tech keywords
    try:
        for keyword in tech_keywords[:10]:  # Top 10 to avoid rate limits
            try:
                url = f"https://news.google.com/rss/search?q={quote_plus(keyword)}+when:1d&hl=en-US&gl=US&ceid=US:en"
                resp = requests.get(url, headers=RSS_HEADERS, timeout=10)
                
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.content)
                    
                    for entry in feed.entries[:3]:  # Top 3 per keyword
                        pub_date = datetime(*entry.published_parsed[:6])
                        if pub_date > CUTOFF_24H:
                            tech_content.append({
                                "title": entry.title,
                                "url": entry.link,
                                "published": pub_date.strftime("%Y-%m-%d %H:%M"),
                                "source": "Google News",
                                "keyword": keyword,
                                "source_type": "tech_news",
                                "channel": "tech",
                                "priority": "HIGH" if any(x in keyword.lower() for x in ['musk', 'altman', 'openai', 'chatgpt']) else "MEDIUM"
                            })
            except Exception as e:
                continue
                
        print(f"   Google News: Found tech stories")
        
    except Exception as e:
        print(f"   Google News error: {e}")
    
    # Reddit tech communities
    try:
        tech_subreddits = ["technology", "artificial", "MachineLearning", "singularity", "Futurology", "startups", "tech"]
        for subreddit in tech_subreddits:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
                resp = requests.get(url, headers=RSS_HEADERS, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    
                    for child in data.get('data', {}).get('children', []):
                        post = child.get('data', {})
                        created_utc = post.get('created_utc', 0)
                        created_time = datetime.fromtimestamp(created_utc)
                        
                        if created_time > CUTOFF_24H:
                            score = post.get('score', 0)
                            num_comments = post.get('num_comments', 0)
                            
                            tech_content.append({
                                "title": post.get('title', '')[:100],
                                "url": f"https://reddit.com{post.get('permalink', '')}",
                                "subreddit": subreddit,
                                "score": score,
                                "comments": num_comments,
                                "created": created_time.strftime("%Y-%m-%d %H:%M"),
                                "source": f"r/{subreddit}",
                                "source_type": "reddit",
                                "channel": "tech",
                                "priority": "HIGH" if score > 500 else "MEDIUM"
                            })
            except Exception as e:
                continue
                
        print(f"   Reddit tech: Found posts")
        
    except Exception as e:
        print(f"   Reddit tech error: {e}")
    
    return tech_content

def create_channel_card(list_name, title, findings):
    """Create Trello card for specific channel"""
    list_id = LIST_IDS.get(list_name)
    if not list_id:
        print(f"❌ List '{list_name}' not found in Trello")
        return None
    
    desc_lines = [
        f"📅 Full Radar Scan: {NOW.strftime('%Y-%m-%d %H:%M')}",
        f"🎯 Channel: {list_name}",
        f"📊 Items found: {len(findings)}",
        "⏰ Last 24 hours only",
        ""
    ]
    
    # Group by source type
    sources = {}
    for item in findings:
        source = item.get('source', 'Unknown')
        if source not in sources:
            sources[source] = []
        sources[source].append(item)
    
    # Format by priority first
    high_priority = [f for f in findings if f.get('priority') == 'HIGH']
    if high_priority:
        desc_lines.append("🔴 **HIGH PRIORITY:**")
        for item in high_priority[:5]:
            title_text = item.get('title', 'No title')[:70]
            source_text = item.get('source', 'Unknown')
            
            # Add relevant metrics
            metrics = []
            if item.get('magnitude'):
                metrics.append(f"M{item['magnitude']}")
            if item.get('score'):
                metrics.append(f"{item['score']} pts")
            if item.get('views'):
                metrics.append(f"{item['views']:,} views")
            
            metric_str = " • " + " • ".join(metrics) if metrics else ""
            
            desc_lines.append(f"🔴 [{source_text}] {title_text}{metric_str}")
            desc_lines.append(f"🔗 {item.get('url', 'No URL')}")
            desc_lines.append("")
        
        desc_lines.append("")
    
    # Group by source
    for source, items in sources.items():
        if len(items) > 0:
            desc_lines.append(f"📌 **{source.upper()}:** ({len(items)} items)")
            
            # Sort by priority/score within source
            items.sort(key=lambda x: (x.get('priority') == 'HIGH', x.get('score', x.get('magnitude', 0))), reverse=True)
            
            for item in items[:4]:  # Top 4 per source
                title_text = item.get('title', 'No title')[:60]
                priority_emoji = "🔴" if item.get('priority') == 'HIGH' else "🟡"
                desc_lines.append(f"  {priority_emoji} {title_text}...")
                desc_lines.append(f"     🔗 {item.get('url', 'No URL')}")
            
            desc_lines.append("")
    
    # Summary
    high_count = len(high_priority)
    total_sources = len(sources)
    
    desc_lines.extend([
        "📊 **SUMMARY:**",
        f"• Total items: {len(findings)}",
        f"• High priority: {high_count}",
        f"• Sources: {total_sources}",
        ""
    ])
    
    # Channel-specific insights
    if "TECH" in list_name:
        tech_keywords_found = []
        for item in findings:
            title_lower = item.get('title', '').lower()
            if any(kw.lower() in title_lower for kw in ['musk', 'altman', 'openai', 'ai', 'chatgpt']):
                tech_keywords_found.append(item.get('title', '')[:40])
        
        if tech_keywords_found:
            desc_lines.extend([
                "🤖 **KEY TECH TOPICS:**",
                f"• AI/ML stories: {len([t for t in tech_keywords_found if 'ai' in t.lower() or 'ml' in t.lower()])}",
                f"• Big tech figures: {len([t for t in tech_keywords_found if any(name in t.lower() for name in ['musk', 'altman'])])}",
                ""
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
            print(f"✅ Created card: {title}")
            return card_id
        else:
            print(f"❌ Trello error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Card creation error: {e}")
        return None

def run_full_channel_radar():
    """Run comprehensive radar for ALL channels"""
    print("🚀 FULL CHANNEL RADAR - ALL CHANNELS")
    print("=" * 60)
    print(f"🕐 Started: {NOW.strftime('%Y-%m-%d %H:%M:%S')}")
    print("📡 Channels: H1/H3 (Disasters), H2 (Gun Rights), R1 (Taylor Swift), R2 (Legal), N1 (Tech)")
    print("🌐 APIs: 15+ sources including Google Trends, HackerNews, GDELT, NASA, etc.")
    
    all_findings = {}
    
    # H1/H3 - Disasters
    print("\n🌋 SCANNING H1/H3 - DISASTERS")
    disaster_findings = []
    
    # Earthquake APIs
    emsc_earthquakes = get_emsc_earthquakes(min_magnitude=5.5)
    disaster_findings.extend(emsc_earthquakes)
    print(f"   EMSC Earthquakes: {len(emsc_earthquakes)}")
    
    # NASA Fire hotspots
    nasa_fires = get_nasa_fires()
    disaster_findings.extend(nasa_fires)
    print(f"   NASA Fires: {len(nasa_fires)}")
    
    # GDACS alerts
    gdacs_alerts = get_gdacs_alerts()
    disaster_findings.extend(gdacs_alerts)
    print(f"   GDACS Alerts: {len(gdacs_alerts)}")
    
    all_findings["🌋 H1/H3 - Disasters"] = disaster_findings
    
    # H2 - Gun Rights
    print("\n🔫 SCANNING H2 - GUN RIGHTS")
    gun_findings = []
    
    congress_bills = get_congress_bills()
    gun_findings.extend(congress_bills)
    print(f"   Congress Bills: {len(congress_bills)}")
    
    federal_regs = get_federal_register()
    gun_findings.extend(federal_regs)
    print(f"   Federal Register: {len(federal_regs)}")
    
    court_cases = get_supreme_court_cases()
    gun_findings.extend(court_cases)
    print(f"   Supreme Court: {len(court_cases)}")
    
    all_findings["🔫 H2 - Gun Rights"] = gun_findings
    
    # R1 - Taylor Swift  
    print("\n💫 SCANNING R1 - TAYLOR SWIFT")
    taylor_findings = []
    
    # Celebrity RSS feeds (from existing system)
    celebrity_feeds = {
        "eonline": "https://www.eonline.com/syndication/rss/popular",
        "usweekly": "https://www.usmagazine.com/feed/",
        "pagesix": "https://pagesix.com/feed/"
    }
    
    taylor_keywords = ["taylor swift", "travis kelce", "eras tour", "swifties"]
    
    for feed_name, feed_url in celebrity_feeds.items():
        try:
            resp = requests.get(feed_url, headers=RSS_HEADERS, timeout=10)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.content)
                
                for entry in feed.entries[:10]:
                    title_lower = entry.title.lower()
                    summary_lower = entry.get('description', '').lower()
                    
                    if any(kw in title_lower or kw in summary_lower for kw in taylor_keywords):
                        pub_date = datetime(*entry.published_parsed[:6])
                        if pub_date > CUTOFF_24H:
                            taylor_findings.append({
                                "title": entry.title,
                                "url": entry.link,
                                "source": feed_name.title(),
                                "published": pub_date.strftime("%Y-%m-%d %H:%M"),
                                "source_type": "celebrity_news",
                                "priority": "HIGH" if "taylor swift" in title_lower else "MEDIUM"
                            })
        except Exception as e:
            print(f"   {feed_name} error: {e}")
    
    print(f"   Celebrity News: {len(taylor_findings)}")
    all_findings["💫 R1 - Taylor Swift"] = taylor_findings
    
    # R2 - Legal/Crime
    print("\n⚖️ SCANNING R2 - LEGAL/CRIME")
    legal_findings = []
    
    # Use court cases from H2 + legal news searches
    legal_findings.extend(court_cases)  # Reuse Supreme Court data
    
    # Google News for legal terms
    legal_keywords = ["verdict", "sentenced", "trial", "lawsuit", "court ruling", "conviction"]
    for keyword in legal_keywords[:5]:
        try:
            url = f"https://news.google.com/rss/search?q={quote_plus(keyword)}+when:1d&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(url, headers=RSS_HEADERS, timeout=10)
            
            if resp.status_code == 200:
                feed = feedparser.parse(resp.content)
                
                for entry in feed.entries[:3]:
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date > CUTOFF_24H:
                        legal_findings.append({
                            "title": entry.title,
                            "url": entry.link,
                            "source": "Google News",
                            "keyword": keyword,
                            "published": pub_date.strftime("%Y-%m-%d %H:%M"),
                            "source_type": "legal_news",
                            "priority": "MEDIUM"
                        })
        except Exception as e:
            continue
    
    print(f"   Legal News: {len(legal_findings)}")
    all_findings["⚖️ R2 - Legal/Crime"] = legal_findings
    
    # N1 - TECH (NEW!)
    print("\n💻 SCANNING N1 - TECH")
    tech_findings = get_tech_news_content()
    print(f"   Tech Content: {len(tech_findings)}")
    all_findings["💻 N1 - TECH"] = tech_findings
    
    # Create Trello cards for each channel
    print(f"\n📋 CREATING TRELLO CARDS")
    created_cards = 0
    
    for list_name, findings in all_findings.items():
        if findings:
            high_priority = len([f for f in findings if f.get('priority') == 'HIGH'])
            title = f"{list_name.split(' - ')[0]} Full Radar - {len(findings)} items ({high_priority} high)"
            
            card_id = create_channel_card(list_name, title, findings)
            if card_id:
                created_cards += 1
    
    # Summary
    total_findings = sum(len(findings) for findings in all_findings.values())
    total_high_priority = sum(len([f for f in findings if f.get('priority') == 'HIGH']) for findings in all_findings.values())
    
    print(f"\n🎯 FULL RADAR COMPLETE")
    print(f"📊 Total intelligence: {total_findings} items")
    print(f"🔴 High priority: {total_high_priority}")
    print(f"📋 Trello cards: {created_cards}")
    print(f"📡 Channels covered: {len(all_findings)}")
    print(f"⏱️ Duration: {(datetime.now() - NOW).total_seconds():.1f}s")
    print(f"🚀 New N1 - TECH channel included!")
    
    return all_findings

if __name__ == "__main__":
    run_full_channel_radar()