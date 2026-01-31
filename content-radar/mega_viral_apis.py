#!/usr/bin/env python3
"""
Mega Viral APIs - Extended free API collection for maximum content intelligence
Includes: All previous + NewsAPI, GNews, HackerNews, GDELT, Enhanced Reddit/YouTube
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

# Import our previous viral APIs
from viral_apis import (
    get_emsc_earthquakes, get_nasa_fires, get_gdacs_alerts,
    get_congress_bills, get_federal_register, get_supreme_court_cases,
    get_reddit_trending
)

# Import Google Trends (simple version)
from simple_google_trends import get_channel_trends

# Paths
BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "mega_api_state.json"

# HTTP headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Time filtering
NOW = datetime.now()
CUTOFF_24H = NOW - timedelta(hours=24)
CUTOFF_1H = NOW - timedelta(hours=1)

# API Keys (add to clawdbot config later)
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', '')  # Free: 100 req/day
GNEWS_API_KEY = os.getenv('GNEWS_API_KEY', '')  # Free: 100 req/day  
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')  # Free: 10k units/day

def load_state():
    """Load last check timestamps"""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_checks": {}, "used_quotas": {}}

def save_state(state):
    """Save current timestamps and quota usage"""
    STATE_FILE.write_text(json.dumps(state, indent=2))

# =============================================================================
# NEWS APIs (All Channels)
# =============================================================================

def get_newsapi_headlines(categories=["general"], countries=["us"], page_size=20):
    """NewsAPI.org - Free tier: 100 requests/day"""
    articles = []
    
    if not NEWSAPI_KEY:
        print("⚠️  NewsAPI key not set (export NEWSAPI_KEY=your_key)")
        return articles
    
    try:
        state = load_state()
        daily_usage = state["used_quotas"].get("newsapi", {})
        today = NOW.strftime("%Y-%m-%d")
        
        if daily_usage.get(today, 0) >= 90:  # Leave buffer of 10
            print("⚠️  NewsAPI quota exhausted for today")
            return articles
        
        for category in categories:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'apiKey': NEWSAPI_KEY,
                'country': 'us',
                'category': category,
                'pageSize': min(page_size, 20),
                'sortBy': 'publishedAt'
            }
            
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Update quota usage
                state["used_quotas"]["newsapi"] = state["used_quotas"].get("newsapi", {})
                state["used_quotas"]["newsapi"][today] = daily_usage.get(today, 0) + 1
                save_state(state)
                
                for article in data.get('articles', []):
                    pub_date_str = article.get('publishedAt', '')
                    if pub_date_str:
                        pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        if pub_date > CUTOFF_24H.replace(tzinfo=timezone.utc):
                            articles.append({
                                "title": article.get('title', ''),
                                "description": article.get('description', '')[:200],
                                "url": article.get('url', ''),
                                "source": article.get('source', {}).get('name', 'NewsAPI'),
                                "published": pub_date.strftime("%Y-%m-%d %H:%M UTC"),
                                "source_type": "news",
                                "category": category,
                                "priority": "MEDIUM"
                            })
            elif resp.status_code == 429:
                print("⚠️  NewsAPI rate limit hit")
                break
                
    except Exception as e:
        print(f"NewsAPI error: {e}")
    
    return articles

def get_gnews_api(queries=["breaking news", "emergency", "disaster"], max_per_query=10):
    """GNews API - Free tier: 100 requests/day"""
    articles = []
    
    if not GNEWS_API_KEY:
        print("⚠️  GNews API key not set (export GNEWS_API_KEY=your_key)")
        return articles
    
    try:
        state = load_state()
        daily_usage = state["used_quotas"].get("gnews", {})
        today = NOW.strftime("%Y-%m-%d")
        
        if daily_usage.get(today, 0) >= 90:  # Leave buffer
            print("⚠️  GNews quota exhausted for today")
            return articles
        
        for query in queries:
            url = "https://gnews.io/api/v4/search"
            params = {
                'q': query,
                'token': GNEWS_API_KEY,
                'lang': 'en',
                'country': 'us',
                'max': max_per_query,
                'sortby': 'publishedAt'
            }
            
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Update quota usage
                state["used_quotas"]["gnews"] = state["used_quotas"].get("gnews", {})
                state["used_quotas"]["gnews"][today] = daily_usage.get(today, 0) + 1
                save_state(state)
                
                for article in data.get('articles', []):
                    pub_date_str = article.get('publishedAt', '')
                    if pub_date_str:
                        pub_date = datetime.fromisoformat(pub_date_str)
                        if pub_date > CUTOFF_24H.replace(tzinfo=timezone.utc):
                            articles.append({
                                "title": article.get('title', ''),
                                "description": article.get('description', '')[:200],
                                "url": article.get('url', ''),
                                "source": article.get('source', {}).get('name', 'GNews'),
                                "published": pub_date.strftime("%Y-%m-%d %H:%M UTC"),
                                "source_type": "news",
                                "query": query,
                                "priority": "HIGH" if "breaking" in query.lower() else "MEDIUM"
                            })
            elif resp.status_code == 429:
                print("⚠️  GNews rate limit hit")
                break
                
    except Exception as e:
        print(f"GNews API error: {e}")
    
    return articles

def get_hackernews_trending():
    """HackerNews API - Completely free, no limits"""
    stories = []
    
    try:
        # Get top stories
        top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        resp = requests.get(top_stories_url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            story_ids = resp.json()[:30]  # Top 30 stories
            
            for story_id in story_ids[:15]:  # Check first 15 for speed
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                story_resp = requests.get(story_url, headers=HEADERS, timeout=10)
                
                if story_resp.status_code == 200:
                    story = story_resp.json()
                    
                    # Check if story is recent (last 24h)
                    story_time = datetime.fromtimestamp(story.get('time', 0))
                    if story_time > CUTOFF_24H:
                        
                        # Tech/startup stories often predict mainstream trends
                        title = story.get('title', '')
                        score = story.get('score', 0)
                        comments = story.get('descendants', 0)
                        
                        stories.append({
                            "title": title,
                            "url": story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                            "score": score,
                            "comments": comments,
                            "published": story_time.strftime("%Y-%m-%d %H:%M"),
                            "source": "HackerNews",
                            "source_type": "tech_news",
                            "priority": "HIGH" if score > 200 else "MEDIUM"
                        })
                        
                time.sleep(0.1)  # Be nice to their API
                
    except Exception as e:
        print(f"HackerNews API error: {e}")
    
    return sorted(stories, key=lambda x: x.get('score', 0), reverse=True)

def get_gdelt_events(themes=["DISASTER", "CRISIS", "PROTEST"]):
    """GDELT Project - Free global event database"""
    events = []
    
    try:
        # Use GDELT GKG (Global Knowledge Graph) API
        for theme in themes:
            url = "http://api.gdeltproject.org/api/v2/doc/doc"
            params = {
                'query': f'theme:{theme}',
                'mode': 'TimelineVol',
                'timespan': '1d',
                'format': 'json',
                'maxrecords': 20
            }
            
            resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
            
            if resp.status_code == 200:
                data = resp.json()
                
                for event in data.get('timeline', [])[:10]:
                    # GDELT has complex data structure, extract key fields
                    if isinstance(event, dict):
                        events.append({
                            "title": f"GDELT {theme}: Global event detected",
                            "description": str(event)[:200],
                            "url": "https://www.gdeltproject.org",
                            "source": "GDELT",
                            "source_type": "global_events",
                            "theme": theme,
                            "priority": "MEDIUM"
                        })
                        
    except Exception as e:
        print(f"GDELT API error: {e}")
    
    return events

def get_youtube_trending_videos(channel_ids=[], region_code='US'):
    """YouTube Data API v3 - Free quota: 10,000 units/day"""
    videos = []
    
    if not YOUTUBE_API_KEY:
        print("⚠️  YouTube API key not set (export YOUTUBE_API_KEY=your_key)")
        return videos
    
    try:
        state = load_state()
        daily_usage = state["used_quotas"].get("youtube", {})
        today = NOW.strftime("%Y-%m-%d")
        
        if daily_usage.get(today, 0) >= 9000:  # Leave buffer
            print("⚠️  YouTube API quota near limit for today")
            return videos
        
        # Get trending videos (costs 1 unit per request)
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'snippet,statistics',
            'chart': 'mostPopular',
            'regionCode': region_code,
            'maxResults': 25,
            'key': YOUTUBE_API_KEY
        }
        
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            
            # Update quota usage (trending videos = 1 unit)
            state["used_quotas"]["youtube"] = state["used_quotas"].get("youtube", {})
            state["used_quotas"]["youtube"][today] = daily_usage.get(today, 0) + 1
            save_state(state)
            
            for video in data.get('items', []):
                snippet = video.get('snippet', {})
                stats = video.get('statistics', {})
                
                pub_date_str = snippet.get('publishedAt', '')
                if pub_date_str:
                    pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                    if pub_date > CUTOFF_24H.replace(tzinfo=timezone.utc):
                        
                        view_count = int(stats.get('viewCount', 0))
                        like_count = int(stats.get('likeCount', 0))
                        
                        videos.append({
                            "title": snippet.get('title', ''),
                            "description": snippet.get('description', '')[:200],
                            "url": f"https://www.youtube.com/watch?v={video.get('id')}",
                            "channel": snippet.get('channelTitle', ''),
                            "views": view_count,
                            "likes": like_count,
                            "published": pub_date.strftime("%Y-%m-%d %H:%M UTC"),
                            "source": "YouTube Trending",
                            "source_type": "youtube",
                            "priority": "HIGH" if view_count > 500000 else "MEDIUM"
                        })
                        
        elif resp.status_code == 403:
            print("⚠️  YouTube API quota exhausted")
            
    except Exception as e:
        print(f"YouTube API error: {e}")
    
    return sorted(videos, key=lambda x: x.get('views', 0), reverse=True)

def get_enhanced_reddit_all_channels():
    """Enhanced Reddit for ALL channel types"""
    posts = []
    
    # Channel-specific subreddit mapping
    channel_subreddits = {
        "disasters": ["news", "worldnews", "CatastrophicFailure", "NatureIsFuckingLit", "climate"],
        "gun_rights": ["guns", "firearms", "2ALiberals", "progun", "gunpolitics", "liberalgunowners"],
        "taylor_swift": ["TaylorSwift", "swifties", "popheads", "entertainment", "nfl", "KansasCityChiefs"],
        "legal_crime": ["legaladvice", "news", "JusticeServed", "TrueCrime", "politics"]
    }
    
    all_results = {}
    
    for channel, subreddits in channel_subreddits.items():
        channel_posts = []
        
        for subreddit in subreddits[:3]:  # Limit to 3 subreddits per channel
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=15"
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
                            
                            # Calculate engagement rate
                            age_hours = (NOW - created_time).total_seconds() / 3600
                            engagement_rate = (score + num_comments * 2) / max(age_hours, 1)
                            
                            channel_posts.append({
                                "title": post.get('title', '')[:100],
                                "url": f"https://reddit.com{post.get('permalink', '')}",
                                "subreddit": subreddit,
                                "score": score,
                                "comments": num_comments,
                                "engagement_rate": engagement_rate,
                                "created": created_time.strftime("%Y-%m-%d %H:%M"),
                                "source": f"r/{subreddit}",
                                "source_type": "reddit",
                                "channel": channel,
                                "priority": "HIGH" if engagement_rate > 50 else "MEDIUM"
                            })
                            
                time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                print(f"Reddit r/{subreddit} error: {e}")
        
        # Sort by engagement and keep top posts
        all_results[channel] = sorted(channel_posts, key=lambda x: x.get('engagement_rate', 0), reverse=True)[:10]
        posts.extend(all_results[channel])
    
    return posts, all_results

# =============================================================================
# MEGA SCAN FUNCTIONS
# =============================================================================

def run_mega_free_apis():
    """Run ALL free APIs including new ones"""
    print("🚀 MEGA API SCAN - All Free Sources")
    print("=" * 50)
    
    all_results = {
        "timestamp": NOW.strftime("%Y-%m-%d %H:%M:%S"),
        "previous_apis": {
            "emsc_earthquakes": get_emsc_earthquakes(),
            "nasa_fires": get_nasa_fires(),
            "gdacs_alerts": get_gdacs_alerts(),
            "congress_bills": get_congress_bills(),
            "federal_register": get_federal_register(),
            "supreme_court": get_supreme_court_cases()
        },
        "new_apis": {
            "newsapi_headlines": get_newsapi_headlines(),
            "gnews_breaking": get_gnews_api(),
            "hackernews_trending": get_hackernews_trending(),
            "gdelt_events": get_gdelt_events(),
            "youtube_trending": get_youtube_trending_videos()
        },
        "enhanced_social": {}
    }
    
    # Enhanced Reddit by channel
    reddit_posts, reddit_by_channel = get_enhanced_reddit_all_channels()
    all_results["enhanced_social"]["reddit_by_channel"] = reddit_by_channel
    
    # Google Trends analysis (simplified)
    print("📈 Running Google Trends analysis...")
    google_trends_data = get_channel_trends()
    all_results["google_trends"] = google_trends_data
    
    # Count results
    total_items = 0
    for category in all_results.values():
        if isinstance(category, dict):
            for items in category.values():
                if isinstance(items, list):
                    total_items += len(items)
                elif isinstance(items, dict):
                    for sub_items in items.values():
                        if isinstance(sub_items, list):
                            total_items += len(sub_items)
    
    print(f"✅ MEGA SCAN COMPLETE: {total_items} items from {len(all_results)} API categories")
    
    return all_results

def get_mega_high_priority():
    """Get high priority alerts from ALL sources"""
    all_data = run_mega_free_apis()
    high_priority = []
    
    def extract_high_priority(data, path=""):
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get('priority') == 'HIGH':
                    item['api_source'] = path
                    high_priority.append(item)
        elif isinstance(data, dict):
            for key, value in data.items():
                extract_high_priority(value, f"{path}/{key}" if path else key)
    
    extract_high_priority(all_data)
    
    # Sort by various metrics
    def sort_key(item):
        return (
            item.get('magnitude', 0) * 10 +  # Earthquakes
            item.get('score', 0) / 100 +      # Reddit/HN scores
            item.get('views', 0) / 1000000 +  # YouTube views
            item.get('engagement_rate', 0)    # Reddit engagement
        )
    
    return sorted(high_priority, key=sort_key, reverse=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Mega Viral APIs - Maximum free content intelligence")
    parser.add_argument("--mega", action="store_true", help="Run ALL APIs (old + new)")
    parser.add_argument("--high-priority", action="store_true", help="High priority from ALL sources")
    parser.add_argument("--news", action="store_true", help="News APIs only (NewsAPI, GNews)")
    parser.add_argument("--tech", action="store_true", help="Tech APIs (HackerNews, YouTube)")
    parser.add_argument("--social", action="store_true", help="Enhanced social (Reddit by channel)")
    parser.add_argument("--trends", action="store_true", help="Google Trends analysis only")
    parser.add_argument("--quotas", action="store_true", help="Show API quota usage")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if args.quotas:
        state = load_state()
        quotas = state.get("used_quotas", {})
        today = NOW.strftime("%Y-%m-%d")
        
        print("📊 API QUOTA USAGE (Today)")
        print("=" * 30)
        print(f"NewsAPI: {quotas.get('newsapi', {}).get(today, 0)}/100 requests")
        print(f"GNews: {quotas.get('gnews', {}).get(today, 0)}/100 requests")  
        print(f"YouTube: {quotas.get('youtube', {}).get(today, 0)}/10,000 units")
        print(f"Reddit: Unlimited (rate limited)")
        print(f"HackerNews: Unlimited")
        print(f"GDELT: Unlimited")
    
    elif args.high_priority:
        results = get_mega_high_priority()
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"\n🚨 MEGA HIGH PRIORITY ALERTS ({len(results)} items)")
            print("=" * 60)
            for item in results[:15]:  # Top 15
                title = item.get('title', 'No title')[:80]
                source = item.get('source', 'Unknown')
                api_source = item.get('api_source', '')
                
                # Show relevant metric
                metric = ""
                if item.get('magnitude'):
                    metric = f" • M{item['magnitude']}"
                elif item.get('score'):
                    metric = f" • {item['score']} score"
                elif item.get('views'):
                    metric = f" • {item['views']:,} views"
                elif item.get('engagement_rate'):
                    metric = f" • {item['engagement_rate']:.1f} rate"
                
                print(f"🔴 {title}")
                print(f"   {source} ({api_source}){metric}")
                print(f"   🔗 {item.get('url', 'No URL')}")
                print()
    
    elif args.news:
        print("📰 NEWS APIs")
        print("=" * 20)
        
        newsapi = get_newsapi_headlines()
        print(f"NewsAPI: {len(newsapi)} headlines")
        
        gnews = get_gnews_api()
        print(f"GNews: {len(gnews)} breaking stories")
        
        for article in (newsapi + gnews)[:5]:
            print(f"  • {article['title'][:60]}... ({article['source']})")
    
    elif args.tech:
        print("💻 TECH APIs")
        print("=" * 20)
        
        hn = get_hackernews_trending()
        print(f"HackerNews: {len(hn)} trending stories")
        for story in hn[:3]:
            print(f"  • {story['title'][:60]}... ({story['score']} pts)")
        
        yt = get_youtube_trending_videos()
        print(f"YouTube Trending: {len(yt)} videos")
        for video in yt[:3]:
            print(f"  • {video['title'][:60]}... ({video['views']:,} views)")
    
    elif args.social:
        print("📱 ENHANCED SOCIAL")
        print("=" * 30)
        
        posts, by_channel = get_enhanced_reddit_all_channels()
        
        for channel, channel_posts in by_channel.items():
            if channel_posts:
                print(f"\n{channel.upper().replace('_', ' ')}:")
                for post in channel_posts[:3]:
                    print(f"  • {post['title'][:50]}... ({post['source']})")
    
    elif args.trends:
        print("📈 GOOGLE TRENDS")
        print("=" * 30)
        
        trends_data = get_channel_trends()
        
        for channel, channel_trends in trends_data.items():
            if channel_trends:
                print(f"\n{channel.upper().replace('_', ' ')}:")
                for trend in channel_trends[:3]:
                    direction = "📈" if trend['trend'] == 'rising' else "📉" if trend['trend'] == 'falling' else "➡️"
                    print(f"  {direction} {trend['keyword']} - Interest: {trend['interest']}")
    
    else:
        # Default: mega scan
        results = run_mega_free_apis()
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("🚀 MEGA API RESULTS")
            print("=" * 40)
            
            # Summary by category
            for category, sources in results.items():
                if isinstance(sources, dict) and category != "timestamp":
                    print(f"\n{category.upper().replace('_', ' ')}:")
                    for source, items in sources.items():
                        if isinstance(items, list):
                            print(f"  {source}: {len(items)} items")
                        elif isinstance(items, dict):
                            for sub_source, sub_items in items.items():
                                if isinstance(sub_items, list):
                                    print(f"  {source}/{sub_source}: {len(sub_items)} items")