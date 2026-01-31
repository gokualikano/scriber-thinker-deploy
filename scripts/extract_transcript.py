#!/usr/bin/env python3
"""
YouTube Transcript Extractor
Extracts transcripts/captions from YouTube videos using yt-dlp.
Handles auto-generated and manual captions, with language preference.
"""

import subprocess
import json
import sys
import re
import os
from pathlib import Path

def get_video_info(url):
    """Get video info including available subtitles."""
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--skip-download",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to get video info: {result.stderr}")
    return json.loads(result.stdout)

def download_subtitles(url, output_dir, lang="en"):
    """Download subtitles in VTT format."""
    output_path = os.path.join(output_dir, "%(id)s")
    
    # Try manual subtitles first, then auto-generated
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", f"{lang}.*,{lang}",
        "--sub-format", "vtt",
        "--output", output_path,
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to download subtitles: {result.stderr}")
    
    return result

def parse_vtt(vtt_path):
    """Parse VTT file and extract clean text."""
    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove VTT header
    lines = content.split('\n')
    text_lines = []
    seen_lines = set()  # For deduplication
    
    for line in lines:
        # Skip headers, timestamps, and empty lines
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            continue
        if '-->' in line:  # Timestamp line
            continue
        if re.match(r'^\d+$', line.strip()):  # Cue number
            continue
        if not line.strip():
            continue
        
        # Clean up the line
        clean_line = line.strip()
        
        # Remove VTT tags like <c>, </c>, <00:00:00.000>
        clean_line = re.sub(r'<[^>]+>', '', clean_line)
        
        # Remove duplicate lines (common in auto-generated subs)
        if clean_line and clean_line not in seen_lines:
            seen_lines.add(clean_line)
            text_lines.append(clean_line)
    
    # Join and clean up
    text = ' '.join(text_lines)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_transcript(url, lang="en", output_file=None):
    """Main function to extract transcript from YouTube URL."""
    import tempfile
    
    print(f"Extracting transcript from: {url}")
    
    # Get video info first
    print("Getting video info...")
    info = get_video_info(url)
    video_id = info.get('id', 'unknown')
    title = info.get('title', 'Unknown Title')
    duration = info.get('duration', 0)
    
    print(f"Video: {title}")
    print(f"Duration: {duration // 60}m {duration % 60}s")
    
    # Check available subtitles
    subtitles = info.get('subtitles', {})
    auto_subs = info.get('automatic_captions', {})
    
    has_manual = lang in subtitles or any(k.startswith(lang) for k in subtitles.keys())
    has_auto = lang in auto_subs or any(k.startswith(lang) for k in auto_subs.keys())
    
    if has_manual:
        print(f"Found manual {lang} subtitles")
    elif has_auto:
        print(f"Found auto-generated {lang} subtitles")
    else:
        available = list(subtitles.keys()) + list(auto_subs.keys())
        raise Exception(f"No {lang} subtitles available. Available: {available[:10]}")
    
    # Download subtitles to temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        print("Downloading subtitles...")
        download_subtitles(url, tmpdir, lang)
        
        # Find the downloaded VTT file
        vtt_files = list(Path(tmpdir).glob("*.vtt"))
        if not vtt_files:
            raise Exception("No subtitle file downloaded")
        
        # Prefer manual subs over auto-generated
        vtt_file = vtt_files[0]
        for f in vtt_files:
            if 'auto' not in f.name.lower():
                vtt_file = f
                break
        
        print(f"Parsing: {vtt_file.name}")
        transcript = parse_vtt(vtt_file)
    
    # Output
    result = {
        "video_id": video_id,
        "title": title,
        "duration": duration,
        "language": lang,
        "transcript": transcript,
        "word_count": len(transcript.split())
    }
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Saved to: {output_file}")
    
    print(f"Word count: {result['word_count']}")
    
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_transcript.py <youtube_url> [language] [output_file]")
        print("Example: python extract_transcript.py 'https://youtube.com/watch?v=xyz' en transcript.json")
        sys.exit(1)
    
    url = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else "en"
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        result = extract_transcript(url, lang, output_file)
        
        # Print transcript preview
        preview = result['transcript'][:500]
        if len(result['transcript']) > 500:
            preview += "..."
        
        print("\n--- Transcript Preview ---")
        print(preview)
        print(f"\n--- Full transcript: {result['word_count']} words ---")
        
        # If no output file, print full transcript to stdout
        if not output_file:
            print("\n--- Full Transcript ---")
            print(result['transcript'])
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
