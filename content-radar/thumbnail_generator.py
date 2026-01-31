#!/usr/bin/env python3
"""
Thumbnail Generator for H1/H3 Disaster Channels
Input: YouTube URL
Output: High-CTR titles + ImageFX prompt
"""

import subprocess
import json
import sys
import requests
from pathlib import Path

def extract_video_info(youtube_url):
    """Extract title and thumbnail from YouTube URL"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--print", "%(title)s|||%(thumbnail)s|||%(description)s", youtube_url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split("|||")
            return {
                "title": parts[0] if len(parts) > 0 else "",
                "thumbnail": parts[1] if len(parts) > 1 else "",
                "description": parts[2][:500] if len(parts) > 2 else ""
            }
    except Exception as e:
        print(f"Error extracting video info: {e}")
    return None

def download_thumbnail(thumbnail_url, output_path="/tmp/competitor_thumb.jpg"):
    """Download thumbnail for analysis"""
    try:
        resp = requests.get(thumbnail_url, timeout=15)
        if resp.status_code == 200:
            Path(output_path).write_bytes(resp.content)
            return output_path
    except:
        pass
    return None

def detect_disaster_type(title, description=""):
    """Detect the type of disaster from title/description"""
    text = (title + " " + description).lower()
    
    if any(w in text for w in ["flood", "dam", "water", "surge", "tsunami", "wave"]):
        return "flood"
    elif any(w in text for w in ["volcano", "eruption", "lava", "magma", "volcanic"]):
        return "volcano"
    elif any(w in text for w in ["earthquake", "quake", "seismic", "tremor", "magnitude"]):
        return "earthquake"
    elif any(w in text for w in ["hurricane", "cyclone", "typhoon", "storm", "tornado", "wind"]):
        return "storm"
    elif any(w in text for w in ["fire", "wildfire", "blaze", "burning", "inferno"]):
        return "wildfire"
    elif any(w in text for w in ["snow", "blizzard", "freeze", "ice", "cold", "winter"]):
        return "winter"
    elif any(w in text for w in ["landslide", "mudslide", "avalanche", "collapse"]):
        return "landslide"
    else:
        return "disaster"

# Disaster-specific style additions
DISASTER_STYLES = {
    "flood": "massive brown floodwaters engulfing buildings, cars floating and tumbling, people on rooftops waving for help, rescue helicopters in distance, muddy debris everywhere",
    "volcano": "violent volcanic eruption with massive lava fountains, glowing orange rivers of molten rock flowing downhill, thick black ash clouds billowing, pyroclastic flow approaching village",
    "earthquake": "buildings mid-collapse with concrete chunks falling, massive cracks splitting roads, dust clouds rising, tilted structures, people running in panic",
    "storm": "extreme hurricane winds bending palm trees horizontal, debris flying through air, massive waves crashing into coastal buildings, dark ominous sky with rotating clouds",
    "wildfire": "wall of orange flames engulfing forest and homes, thick smoke blocking sun creating orange apocalyptic sky, embers flying everywhere, firefighters silhouetted",
    "winter": "cars buried under massive snowdrifts, buildings collapsing under snow weight, whiteout blizzard conditions, frozen streets with abandoned vehicles",
    "landslide": "massive wall of mud and debris sliding down hillside, houses being swept away, trees tumbling, rocks and boulders rolling",
    "disaster": "massive destruction scene, buildings damaged, emergency vehicles, smoke and debris, chaotic aftermath"
}

def generate_imagefx_prompt(disaster_type, original_title):
    """Generate ImageFX prompt based on disaster type"""
    
    base_style = DISASTER_STYLES.get(disaster_type, DISASTER_STYLES["disaster"])
    
    prompt = f"""Dramatic amateur smartphone footage of {base_style}, captured from ground level by panicked bystander, motion blur from shaky hands, grainy low-resolution quality like 2015 phone camera, chaotic off-center composition, raw unedited look, no text or graphics, realistic news footage style, viral disaster video screenshot, high contrast dramatic lighting, 2024"""
    
    return prompt

def generate_title_options(original_title, disaster_type):
    """Generate high-CTR title variations"""
    # This would ideally use Claude to generate, but we can provide templates
    templates = {
        "flood": [
            "CATASTROPHIC Floods DEVASTATE {location} - {impact}",
            "{location} UNDERWATER: Massive Floods Leave {impact}",
            "BIBLICAL Flooding DESTROYS {location} - Residents Trapped",
            "BREAKING: {location} Dam FAILS - {impact} Evacuated",
            "NIGHTMARE Floods in {location} - Cars SWEPT Away Like Toys"
        ],
        "volcano": [
            "MASSIVE Eruption in {location} - Lava DESTROYS Everything",
            "{location} Volcano EXPLODES - {impact} Flee For Their Lives",
            "APOCALYPTIC Scenes as {location} Volcano Erupts",
            "TERRIFYING: {location} Volcano Sends Lava Rivers Through Towns",
            "BREAKING: {location} Eruption Turns Day Into NIGHT"
        ],
        "earthquake": [
            "DEVASTATING M{magnitude} Earthquake FLATTENS {location}",
            "{location} in RUINS After Catastrophic Earthquake",
            "MASSIVE Quake DESTROYS {location} - Buildings COLLAPSE",
            "BREAKING: {location} Earthquake Leaves {impact} Homeless",
            "TERRIFYING Footage: {location} Earthquake Caught on Camera"
        ],
        "storm": [
            "MONSTER Hurricane OBLITERATES {location}",
            "{location} DESTROYED by Category {category} Storm",
            "APOCALYPTIC Scenes as Hurricane Hits {location}",
            "BREAKING: {location} Torn Apart by {impact} MPH Winds",
            "NIGHTMARE Storm Leaves {location} Unrecognizable"
        ],
        "wildfire": [
            "INFERNO Engulfs {location} - {impact} Homes GONE",
            "{location} BURNING: Massive Wildfire Out of Control",
            "APOCALYPTIC Fire Turns {location} Sky ORANGE",
            "BREAKING: {location} Wildfire EXPLODES Overnight",
            "DEVASTATING Blaze DESTROYS Entire {location} Neighborhood"
        ],
        "winter": [
            "HISTORIC Blizzard BURIES {location} Under {amount} of Snow",
            "{location} PARALYZED by Extreme Winter Storm",
            "CATASTROPHIC Ice Storm DESTROYS {location}",
            "BREAKING: {location} Declares Emergency - {impact} Without Power",
            "BRUTAL Cold KILLS {impact} in {location}"
        ],
        "disaster": [
            "CATASTROPHIC Disaster DEVASTATES {location}",
            "BREAKING: {location} Declares State of Emergency",
            "APOCALYPTIC Scenes in {location} After Disaster Strikes",
            "NIGHTMARE in {location} - {impact} Affected",
            "DEVASTATING Footage From {location} Disaster Zone"
        ]
    }
    
    return templates.get(disaster_type, templates["disaster"])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python thumbnail_generator.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print("=" * 50)
    print("THUMBNAIL GENERATOR - H1/H3 Disaster Channels")
    print("=" * 50)
    
    # Extract video info
    print("\n📥 Extracting video info...")
    info = extract_video_info(url)
    
    if not info:
        print("❌ Failed to extract video info")
        sys.exit(1)
    
    print(f"📺 Original Title: {info['title']}")
    print(f"🖼️ Thumbnail: {info['thumbnail']}")
    
    # Detect disaster type
    disaster_type = detect_disaster_type(info['title'], info['description'])
    print(f"🔍 Detected Type: {disaster_type.upper()}")
    
    # Download thumbnail
    print("\n📥 Downloading thumbnail for reference...")
    thumb_path = download_thumbnail(info['thumbnail'])
    if thumb_path:
        print(f"✅ Saved to: {thumb_path}")
    
    # Generate ImageFX prompt
    print("\n" + "=" * 50)
    print("🎨 IMAGEFX PROMPT:")
    print("=" * 50)
    prompt = generate_imagefx_prompt(disaster_type, info['title'])
    print(prompt)
    
    # Generate title options
    print("\n" + "=" * 50)
    print("📝 HIGH-CTR TITLE TEMPLATES:")
    print("=" * 50)
    titles = generate_title_options(info['title'], disaster_type)
    for i, t in enumerate(titles, 1):
        print(f"{i}. {t}")
    
    print("\n💡 Replace {location}, {impact}, {magnitude}, etc. with actual details")
    print("=" * 50)
