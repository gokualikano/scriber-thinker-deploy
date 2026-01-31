#!/bin/bash
# Extract YouTube channel IDs from competitor URLs

cd ~/clawd/content-radar
source venv/bin/activate

python3 << 'EOF'
import json
import subprocess
from pathlib import Path

competitors = json.loads(Path('../competitors.json').read_text())
channel_ids = {}

all_urls = []
for key, data in competitors.items():
    for url in data.get('competitors', []):
        all_urls.append(url)

print(f"Extracting channel IDs for {len(all_urls)} URLs...")

for i, url in enumerate(all_urls):
    try:
        result = subprocess.run(
            ['yt-dlp', '-J', '--flat-playlist', '--playlist-items', '1', url],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            cid = data.get('channel_id') or data.get('uploader_id')
            if cid:
                channel_ids[url] = cid
                print(f"[{i+1}/{len(all_urls)}] ✓ {url.split('/')[-1][:30]} -> {cid}")
            else:
                print(f"[{i+1}/{len(all_urls)}] ✗ {url.split('/')[-1][:30]} - no ID")
    except Exception as e:
        print(f"[{i+1}/{len(all_urls)}] ✗ {url.split('/')[-1][:30]} - {str(e)[:30]}")

Path('channel_ids.json').write_text(json.dumps({'channels': channel_ids}, indent=2))
print(f"\n✅ Saved {len(channel_ids)} channel IDs to channel_ids.json")
EOF
