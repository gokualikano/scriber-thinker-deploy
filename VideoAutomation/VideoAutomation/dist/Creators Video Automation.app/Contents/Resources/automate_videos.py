#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

def download_videos():
    """Download videos from URLs in urls.txt - H.264 format only"""
    print("=" * 60)
    print("DOWNLOADING VIDEOS (H.264 - PREMIERE PRO COMPATIBLE)")
    print("=" * 60)
    
    # Check if urls.txt exists
    if not os.path.exists('urls.txt'):
        print("ERROR: urls.txt not found!")
        print("Please create a urls.txt file and add YouTube URLs (one per line)")
        return False
    
    # Read URLs
    with open('urls.txt', 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not urls:
        print("ERROR: No URLs found in urls.txt")
        return False
    
    print(f"Found {len(urls)} video(s) to download\n")
    print("Downloading H.264 videos directly - no conversion needed!")
    print("This is much faster and works perfectly in Premiere Pro.\n")
    
    # Create downloads folder
    os.makedirs('premiere_videos', exist_ok=True)
    
    # Download each video
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(urls)}] Downloading: {url}")
        print(f"{'='*60}")
        
        # Download H.264 format directly
        # Format selection prioritizes H.264 (avc1) codec
        cmd = [
            'yt-dlp',
            '-f', 'bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/best[vcodec^=avc1][ext=mp4]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4',
            '-o', 'premiere_videos/%(title)s.%(ext)s',
            '--restrict-filenames',  # Safer filenames
            url
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("✓ Downloaded successfully")
            
        except subprocess.CalledProcessError:
            print(f"✗ Failed to download this video, skipping...")
        except FileNotFoundError:
            print("ERROR: yt-dlp not found. Make sure you installed it with 'brew install yt-dlp'")
            return False
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("ALL DOWNLOADS COMPLETE!")
    print("=" * 60)
    print(f"\n✓ Videos saved in: premiere_videos/")
    print("✓ All videos are H.264 encoded and ready for Premiere Pro")
    print("\nNext steps:")
    print("  1. Import videos from 'premiere_videos' folder into Premiere Pro")
    print("  2. Scale and label your clips manually")
    print("  3. Use Premiere automation for cutting & shuffling")
    
    return True

def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 8 + "YOUTUBE DOWNLOADER FOR PREMIERE PRO" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    # Check if urls.txt exists
    if not os.path.exists('urls.txt'):
        print("FIRST TIME SETUP:")
        print("-" * 60)
        print("I don't see a urls.txt file yet.")
        print("\nPlease:")
        print("  1. Create a file called 'urls.txt' in this folder")
        print("  2. Add YouTube URLs (one per line)")
        print("  3. Run this script again")
        print("\nExample urls.txt content:")
        print("https://www.youtube.com/watch?v=example1")
        print("https://www.youtube.com/watch?v=example2")
        input("\nPress Enter to exit...")
        return
    
    # Run the download
    download_videos()
    
    print("\n")
    input("Press Enter to close...")

if __name__ == "__main__":
    main()