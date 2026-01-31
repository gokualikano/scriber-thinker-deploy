#!/usr/bin/env python3

import json
import subprocess
from datetime import datetime
from pathlib import Path
import sys
import os

# Add venv packages
BASE_DIR = Path(__file__).parent
VENV_PATH = BASE_DIR / "venv" / "lib"
for p in VENV_PATH.glob("python*/site-packages"):
    sys.path.insert(0, str(p))

import requests
from urllib.parse import quote_plus

# Load Trello config
config = json.loads(Path('/Users/malikano/clawdbot_system/config.json').read_text())
API_KEY = config['trello_api_key']
TOKEN = config['trello_api_token']

LIST_ID = '697b21ceab07192676734906'  # Taylor Swift list

def search_taylor_swift_youtube():
    videos = []
    try:
        cmd = ['yt-dlp', '--flat-playlist', '--print', 'title,uploader,upload_date,webpage_url', 'ytsearch5:Taylor Swift news today January 2026']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for i in range(0, len(lines), 4):
                if i + 3 < len(lines):
                    videos.append({
                        'title': lines[i].strip(),
                        'channel': lines[i + 1].strip(), 
                        'date': lines[i + 2].strip(),
                        'url': lines[i + 3].strip()
                    })
    except Exception as e:
        print(f'YouTube search error: {e}')
    return videos[:3]

def search_google_news():
    try:
        import feedparser
        url = f"https://news.google.com/rss/search?q=Taylor+Swift+when:1d&hl=en-US&gl=US&ceid=US:en"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            articles = []
            
            for entry in feed.entries[:3]:
                articles.append({
                    'title': entry.title,
                    'source': entry.source.title if hasattr(entry, 'source') else 'Google News',
                    'url': entry.link,
                    'date': entry.published
                })
            return articles
    except Exception as e:
        print(f'Google News error: {e}')
    return []

# Search for content
print("🔍 Searching for Taylor Swift content...")
videos = search_taylor_swift_youtube()
articles = search_google_news()

# Create card description
description = f'🎤 **Taylor Swift News Update - {datetime.now().strftime("%B %d, %Y")}**\n\n'

if articles:
    description += '📰 **Recent News:**\n'
    for article in articles:
        description += f'• {article["title"]}\n'
        description += f'  Source: {article["source"]}\n'
        description += f'  {article["url"]}\n\n'

if videos:
    description += '📺 **Recent Videos:**\n'
    for video in videos:
        description += f'• **{video["title"]}**\n'
        description += f'  Channel: {video["channel"]} | {video["date"]}\n'
        description += f'  {video["url"]}\n\n'

if not articles and not videos:
    description += '🔍 **Manual Research Needed**\n\n'
    description += '**Search Terms:** Taylor Swift, Travis Kelce, Eras Tour, Swifties\n'
    description += '**Sources to Check:** TMZ, People, E! Online, US Weekly, Entertainment Tonight\n'
    description += '**Keywords:** Taylor Swift news, Travis Kelce relationship, Eras Tour updates'

# Create Trello card
print("📝 Creating Trello card...")
card_data = {
    'name': f'Taylor Swift News - {datetime.now().strftime("%m/%d %H:%M")}',
    'desc': description,
    'idList': LIST_ID,
    'pos': 'top'
}

response = requests.post(
    'https://api.trello.com/1/cards',
    params={'key': API_KEY, 'token': TOKEN},
    json=card_data
)

if response.status_code == 200:
    card = response.json()
    print(f'✅ Created Taylor Swift card: {card["shortUrl"]}')
    print(f'Card ID: {card["id"]}')
else:
    print(f'❌ Failed to create card: {response.status_code}')
    print(response.text)