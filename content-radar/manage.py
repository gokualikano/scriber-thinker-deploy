#!/usr/bin/env python3
"""
ContentRadar Manager - Add/remove competitors, view status
Usage:
  python manage.py list                    # List all competitors
  python manage.py add H1 @channelname     # Add competitor to H1
  python manage.py remove H2 @channelname  # Remove competitor
  python manage.py discover H1             # Find new competitors
  python manage.py status                  # Show radar status
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
COMPETITORS_FILE = BASE_DIR.parent / "competitors.json"

def load_competitors():
    if COMPETITORS_FILE.exists():
        with open(COMPETITORS_FILE) as f:
            return json.load(f)
    return {}

def save_competitors(data):
    with open(COMPETITORS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def list_competitors():
    data = load_competitors()
    for channel, info in data.items():
        print(f"\n📺 {channel} ({info.get('niche', 'unknown')})")
        print(f"   Competitors: {len(info.get('competitors', []))}")
        for comp in info.get('competitors', [])[:5]:
            handle = comp.split('/@')[-1].split('/')[0] if '/@' in comp else comp
            print(f"   • {handle}")
        if len(info.get('competitors', [])) > 5:
            print(f"   ... and {len(info['competitors']) - 5} more")

def add_competitor(channel, handle):
    data = load_competitors()
    
    # Normalize channel name
    channel_keys = {k.split('_')[0]: k for k in data.keys()}
    if channel not in data and channel in channel_keys:
        channel = channel_keys[channel]
    
    if channel not in data:
        data[channel] = {"niche": "unknown", "competitors": []}
    
    # Normalize URL
    if not handle.startswith('http'):
        handle = f"https://www.youtube.com/@{handle.lstrip('@')}/videos"
    
    if handle not in data[channel]['competitors']:
        data[channel]['competitors'].append(handle)
        save_competitors(data)
        print(f"✅ Added {handle} to {channel}")
    else:
        print(f"⚠️ Already exists in {channel}")

def remove_competitor(channel, handle):
    data = load_competitors()
    
    channel_keys = {k.split('_')[0]: k for k in data.keys()}
    if channel not in data and channel in channel_keys:
        channel = channel_keys[channel]
    
    if channel not in data:
        print(f"❌ Channel {channel} not found")
        return
    
    # Find and remove
    handle_lower = handle.lower().lstrip('@')
    removed = False
    for comp in data[channel]['competitors'][:]:
        if handle_lower in comp.lower():
            data[channel]['competitors'].remove(comp)
            removed = True
            print(f"✅ Removed {comp} from {channel}")
    
    if removed:
        save_competitors(data)
    else:
        print(f"⚠️ {handle} not found in {channel}")

def show_status():
    data = load_competitors()
    state_file = BASE_DIR / "state.json"
    report_file = BASE_DIR / "latest_report.json"
    
    print("\n🛰️ CONTENT RADAR STATUS")
    print("=" * 40)
    
    # Competitor stats
    total_comps = sum(len(c.get('competitors', [])) for c in data.values())
    print(f"📊 Channels tracked: {len(data)}")
    print(f"📊 Total competitors: {total_comps}")
    
    # Last run
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        last_check = state.get('last_competitor_check', 0)
        if last_check:
            from datetime import datetime
            dt = datetime.fromtimestamp(last_check)
            print(f"⏰ Last competitor check: {dt.strftime('%Y-%m-%d %H:%M')}")
    
    # Latest alerts
    if report_file.exists():
        with open(report_file) as f:
            report = json.load(f)
        alerts = report.get('alerts', [])
        trending = report.get('trending', [])
        print(f"🚨 Active alerts: {len(alerts)}")
        print(f"📈 Trending videos: {len(trending)}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'list':
        list_competitors()
    elif cmd == 'add' and len(sys.argv) >= 4:
        add_competitor(sys.argv[2].upper(), sys.argv[3])
    elif cmd == 'remove' and len(sys.argv) >= 4:
        remove_competitor(sys.argv[2].upper(), sys.argv[3])
    elif cmd == 'status':
        show_status()
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
