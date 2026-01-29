#!/usr/bin/env python3
"""
ContentRadar - YouTube Content Intelligence System
Monitors alerts, competitors, and trending topics
"""

import json
import os
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
COMPETITORS_FILE = BASE_DIR.parent / "competitors.json"
STATE_FILE = BASE_DIR / "state.json"
ALERTS_LOG = BASE_DIR / "alerts.json"

def load_json(path):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_config():
    return load_json(CONFIG_FILE)

def load_state():
    return load_json(STATE_FILE)

def save_state(state):
    save_json(STATE_FILE, state)

# ============== ALERT MONITORS ==============

def check_usgs_earthquakes(config):
    """Check USGS for significant earthquakes"""
    alerts = []
    try:
        url = config['alert_sources']['usgs']['url']
        min_mag = config['alert_sources']['usgs']['min_magnitude']
        
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        for feature in data.get('features', []):
            props = feature['properties']
            mag = props.get('mag', 0)
            place = props.get('place', 'Unknown')
            event_time = props.get('time', 0)
            
            if mag >= min_mag:
                alerts.append({
                    'type': 'earthquake',
                    'source': 'usgs',
                    'magnitude': mag,
                    'location': place,
                    'timestamp': event_time,
                    'priority': 'HIGH' if mag >= 6.5 else 'MEDIUM',
                    'channels': ['H1', 'H3'],
                    'message': f"🚨 M{mag} EARTHQUAKE - {place}"
                })
    except Exception as e:
        print(f"USGS check failed: {e}")
    
    return alerts

def check_noaa_alerts(config):
    """Check NOAA for severe weather alerts"""
    alerts = []
    try:
        url = config['alert_sources']['noaa']['url']
        severities = config['alert_sources']['noaa']['severity']
        
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'ContentRadar/1.0'})
        data = resp.json()
        
        for feature in data.get('features', []):
            props = feature['properties']
            severity = props.get('severity', '')
            event = props.get('event', '')
            headline = props.get('headline', '')
            
            if severity in severities:
                alerts.append({
                    'type': 'weather',
                    'source': 'noaa',
                    'event': event,
                    'severity': severity,
                    'headline': headline,
                    'priority': 'HIGH' if severity == 'Extreme' else 'MEDIUM',
                    'channels': ['H1', 'H3'],
                    'message': f"⛈️ {severity.upper()} WEATHER - {event}: {headline[:100]}"
                })
    except Exception as e:
        print(f"NOAA check failed: {e}")
    
    return alerts

def check_supreme_court(config):
    """Check for Supreme Court decisions (placeholder - needs proper RSS)"""
    alerts = []
    # TODO: Implement Supreme Court RSS monitoring
    # For now, we'll use a news API or scraping
    return alerts

def check_all_alerts(config):
    """Run all alert checks"""
    all_alerts = []
    all_alerts.extend(check_usgs_earthquakes(config))
    all_alerts.extend(check_noaa_alerts(config))
    all_alerts.extend(check_supreme_court(config))
    return all_alerts

# ============== COMPETITOR TRACKING ==============

def get_channel_id_from_url(url):
    """Extract channel handle from URL"""
    if '/@' in url:
        return url.split('/@')[1].split('/')[0]
    return url

def get_latest_videos_innertube(channel_handle, max_results=5):
    """
    Get latest videos using YouTube's innertube API (no API key needed)
    """
    videos = []
    try:
        # First, get the channel page to find channel ID
        url = f"https://www.youtube.com/@{channel_handle}/videos"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        resp = requests.get(url, headers=headers, timeout=15)
        html = resp.text
        
        # Extract video IDs from the page (simple regex approach)
        import re
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        video_ids = list(dict.fromkeys(video_ids))[:max_results]  # Remove duplicates
        
        # Extract titles
        titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"\}\]', html)
        
        # Extract view counts
        views = re.findall(r'"viewCountText":\{"simpleText":"([^"]+)"\}', html)
        
        for i, vid in enumerate(video_ids[:max_results]):
            title = titles[i] if i < len(titles) else "Unknown"
            view_count = views[i] if i < len(views) else "0"
            
            videos.append({
                'video_id': vid,
                'title': title,
                'url': f"https://www.youtube.com/watch?v={vid}",
                'views': view_count,
                'channel': channel_handle
            })
            
    except Exception as e:
        print(f"Failed to get videos for {channel_handle}: {e}")
    
    return videos

def analyze_competitors(config, competitors_data):
    """Analyze all competitor channels"""
    results = {}
    
    for channel_key, channel_data in competitors_data.items():
        results[channel_key] = []
        
        for comp_url in channel_data.get('competitors', [])[:10]:  # Limit to 10 per channel
            handle = get_channel_id_from_url(comp_url)
            videos = get_latest_videos_innertube(handle, max_results=3)
            
            for video in videos:
                video['source_channel'] = channel_key
                results[channel_key].append(video)
            
            time.sleep(1)  # Rate limiting
    
    return results

def find_trending_videos(competitor_results, threshold=5000):
    """Find videos that are trending (high view velocity)"""
    trending = []
    
    for channel_key, videos in competitor_results.items():
        for video in videos:
            # Parse view count
            views_str = video.get('views', '0')
            try:
                views = int(''.join(filter(str.isdigit, views_str.split()[0])))
            except:
                views = 0
            
            video['views_int'] = views
            
            # Simple trending detection: videos with high views
            # In production, we'd track view velocity over time
            if views >= threshold:
                trending.append(video)
    
    # Sort by views
    trending.sort(key=lambda x: x.get('views_int', 0), reverse=True)
    return trending[:10]

# ============== NOTIFICATION ==============

def format_alert_message(alerts, trending):
    """Format message for WhatsApp"""
    lines = []
    
    if alerts:
        lines.append("🚨 *PRIORITY ALERTS*")
        for alert in alerts[:5]:
            lines.append(f"• {alert['message']}")
        lines.append("")
    
    if trending:
        lines.append("📈 *TRENDING FROM COMPETITORS*")
        for video in trending[:5]:
            lines.append(f"• {video['title'][:50]}...")
            lines.append(f"  {video['views']} - {video['channel']}")
        lines.append("")
    
    if not alerts and not trending:
        return None
    
    lines.append(f"_Updated: {datetime.now().strftime('%H:%M')}_")
    return "\n".join(lines)

# ============== MAIN ==============

def run_radar():
    """Main radar loop"""
    print("🛰️ ContentRadar Starting...")
    
    config = load_config()
    competitors = load_json(COMPETITORS_FILE)
    state = load_state()
    
    # Check alerts
    print("Checking alerts...")
    alerts = check_all_alerts(config)
    
    # Filter out already-seen alerts
    seen_alerts = set(state.get('seen_alerts', []))
    new_alerts = [a for a in alerts if a.get('message') not in seen_alerts]
    
    # Update seen alerts
    for alert in new_alerts:
        seen_alerts.add(alert['message'])
    state['seen_alerts'] = list(seen_alerts)[-100:]  # Keep last 100
    
    # Check competitors (less frequently)
    last_competitor_check = state.get('last_competitor_check', 0)
    competitor_results = {}
    trending = []
    
    if time.time() - last_competitor_check > 3600:  # Every hour
        print("Analyzing competitors...")
        competitor_results = analyze_competitors(config, competitors)
        trending = find_trending_videos(competitor_results)
        state['last_competitor_check'] = time.time()
        state['last_trending'] = trending
    else:
        trending = state.get('last_trending', [])
    
    # Save state
    save_state(state)
    
    # Generate report
    message = format_alert_message(new_alerts, trending)
    
    if message:
        print("\n" + "="*50)
        print(message)
        print("="*50)
        
        # Save for WhatsApp sending
        report = {
            'timestamp': datetime.now().isoformat(),
            'alerts': new_alerts,
            'trending': trending,
            'message': message
        }
        save_json(BASE_DIR / "latest_report.json", report)
        
    return {
        'alerts': new_alerts,
        'trending': trending,
        'message': message
    }

if __name__ == "__main__":
    run_radar()
