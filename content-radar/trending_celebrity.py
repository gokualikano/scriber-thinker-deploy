#!/usr/bin/env python3

import json
import subprocess
from datetime import datetime
from pathlib import Path
import sys
import re

# Add venv packages
BASE_DIR = Path(__file__).parent
VENV_PATH = BASE_DIR / "venv" / "lib"
for p in VENV_PATH.glob("python*/site-packages"):
    sys.path.insert(0, str(p))

import requests
import feedparser

# Load Trello config
config = json.loads(Path('/Users/malikano/clawdbot_system/config.json').read_text())
API_KEY = config['trello_api_key']
TOKEN = config['trello_api_token']

HIGH_PRIORITY_LIST = '697b21cc2f0009bca194f59b'  # High Priority list

def search_trending_celebrities():
    """Search for trending celebrities on YouTube and Google News"""
    results = []
    
    # Search terms for trending celebrities
    search_terms = [
        "trending celebrity news today",
        "hollywood news breaking",
        "celebrity scandal today", 
        "celebrity drama 2026"
    ]
    
    print("🔍 Searching for trending celebrities...")
    
    # YouTube search
    for term in search_terms:
        try:
            cmd = ['yt-dlp', '--flat-playlist', '--print', 'title,uploader,upload_date,view_count,webpage_url', f'ytsearch3:{term}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for i in range(0, len(lines), 5):
                    if i + 4 < len(lines):
                        title = lines[i].strip()
                        channel = lines[i + 1].strip()
                        upload_date = lines[i + 2].strip()
                        view_count = lines[i + 3].strip()
                        url = lines[i + 4].strip()
                        
                        # Check if recent (today)
                        if upload_date.startswith('20260130') or upload_date.startswith('20260129'):
                            results.append({
                                'title': title,
                                'source': f'YouTube - {channel}',
                                'date': upload_date,
                                'url': url,
                                'views': view_count,
                                'type': 'video'
                            })
        except Exception as e:
            print(f"YouTube search error for '{term}': {e}")
    
    # Google News search for celebrity trending
    news_queries = [
        "trending celebrity news",
        "hollywood breaking news",
        "celebrity scandal today"
    ]
    
    for query in news_queries:
        try:
            url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}+when:1d&hl=en-US&gl=US&ceid=US:en"
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:5]:
                    results.append({
                        'title': entry.title,
                        'source': entry.source.title if hasattr(entry, 'source') else 'Google News',
                        'url': entry.link,
                        'date': entry.published,
                        'type': 'news'
                    })
        except Exception as e:
            print(f"Google News search error for '{query}': {e}")
    
    return results

def extract_celebrity_names(results):
    """Extract potential celebrity names from results"""
    celebrity_keywords = [
        'taylor swift', 'travis kelce', 'justin bieber', 'selena gomez', 'kim kardashian',
        'kanye west', 'ariana grande', 'dua lipa', 'billie eilish', 'rihanna',
        'beyonce', 'jennifer lopez', 'brad pitt', 'leonardo dicaprio', 'tom cruise',
        'will smith', 'jennifer lawrence', 'emma stone', 'ryan reynolds', 'blake lively',
        'ryan gosling', 'margot robbie', 'zendaya', 'timothee chalamet', 'anya taylor-joy'
    ]
    
    celebrity_mentions = {}
    
    for result in results:
        title_lower = result['title'].lower()
        for celebrity in celebrity_keywords:
            if celebrity in title_lower:
                if celebrity not in celebrity_mentions:
                    celebrity_mentions[celebrity] = []
                celebrity_mentions[celebrity].append(result)
    
    return celebrity_mentions

# Search for trending content
results = search_trending_celebrities()

# Extract celebrity mentions
celebrity_mentions = extract_celebrity_names(results)

# Find most mentioned/trending celebrity
top_celebrity = None
top_count = 0
top_results = []

for celebrity, mentions in celebrity_mentions.items():
    if len(mentions) > top_count:
        top_count = len(mentions)
        top_celebrity = celebrity
        top_results = mentions

# Create card description
if top_celebrity and top_results:
    description = f'🎬 **TRENDING CELEBRITY: {top_celebrity.title()}**\n\n'
    description += f'📊 **{len(top_results)} recent mentions across platforms**\n\n'
    
    description += '🔥 **Latest Coverage:**\n'
    for result in top_results[:5]:  # Top 5 mentions
        description += f'• **{result["title"]}**\n'
        description += f'  Source: {result["source"]} | {result.get("date", "Recent")}\n'
        description += f'  {result["url"]}\n\n'
    
    card_title = f'🔥 {top_celebrity.title()} TRENDING'
    
else:
    # Fallback - general trending content
    description = '🎬 **TRENDING HOLLYWOOD CONTENT**\n\n'
    description += '📺 **Recent Trending Videos & News:**\n\n'
    
    for result in results[:8]:  # Top 8 overall results
        description += f'• **{result["title"]}**\n'
        description += f'  Source: {result["source"]}\n'
        if 'views' in result and result['views']:
            description += f'  Views: {result["views"]}\n'
        description += f'  {result["url"]}\n\n'
    
    card_title = f'🔥 Hollywood Trending - {datetime.now().strftime("%m/%d")}'

# Add search strategy
description += '\n---\n'
description += '🎯 **Action Items:**\n'
description += '• Analyze top performing content\n'
description += '• Check competitor response\n'
description += '• Create similar angle for our channels\n'
description += '• Monitor for updates/developments'

# Create Trello card
print("📝 Creating HIGH PRIORITY card...")
card_data = {
    'name': card_title,
    'desc': description,
    'idList': HIGH_PRIORITY_LIST,
    'pos': 'top'
}

response = requests.post(
    'https://api.trello.com/1/cards',
    params={'key': API_KEY, 'token': TOKEN},
    json=card_data
)

if response.status_code == 200:
    card = response.json()
    print(f'✅ Created HIGH PRIORITY card: {card["shortUrl"]}')
    if top_celebrity:
        print(f'🎬 Top trending celebrity: {top_celebrity.title()} ({top_count} mentions)')
    else:
        print(f'📊 Found {len(results)} trending entertainment items')
else:
    print(f'❌ Failed to create card: {response.status_code}')
    print(response.text)