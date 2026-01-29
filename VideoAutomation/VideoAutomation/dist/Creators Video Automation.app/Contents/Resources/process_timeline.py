#!/usr/bin/env python3
"""
Premiere Pro XML Processor
Cuts all clips to 6 seconds and shuffles them
"""

import xml.etree.ElementTree as ET
import random
import copy
from pathlib import Path

def process_premiere_xml(input_xml_path, output_xml_path, clip_duration=6):
    """
    Process Premiere Pro XML: cut clips to specified duration and shuffle
    """
    
    print("=" * 70)
    print("PREMIERE PRO XML PROCESSOR - CUT & SHUFFLE")
    print("=" * 70)
    print(f"\nReading XML: {input_xml_path}")
    
    # Parse XML with namespace handling
    try:
        tree = ET.parse(input_xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"ERROR: Could not read XML file: {e}")
        return False
    
    # Register namespaces to preserve them
    namespaces = dict([node for _, node in ET.iterparse(input_xml_path, events=['start-ns'])])
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)
    
    # Find the sequence (timeline)
    sequence = root.find('.//sequence')
    if sequence is None:
        print("ERROR: No sequence found in XML")
        return False
    
    # Get frame rate
    rate_element = sequence.find('.//rate')
    if rate_element is None:
        print("WARNING: Could not find frame rate, using 25fps default")
        fps = 25
    else:
        timebase = rate_element.find('timebase')
        fps = int(timebase.text) if timebase is not None else 25
    
    print(f"Timeline frame rate: {fps} fps")
    
    # Convert clip duration to frames
    clip_duration_frames = clip_duration * fps
    
    # Find all video tracks
    video_element = sequence.find('.//video')
    if video_element is None:
        print("ERROR: No video element found")
        return False
    
    video_tracks = video_element.findall('track')
    if not video_tracks:
        print("ERROR: No video tracks found")
        return False
    
    print(f"Found {len(video_tracks)} video track(s)")
    
    # Collect all clips from all tracks
    all_clips = []
    for track_idx, track in enumerate(video_tracks):
        clips = track.findall('clipitem')
        print(f"Track {track_idx + 1}: {len(clips)} clips")
        all_clips.extend(clips)
    
    if not all_clips:
        print("ERROR: No clips found in timeline")
        return False
    
    print(f"\nTotal clips on timeline: {len(all_clips)}")
    
    # Premiere color labels - ONLY ADDITION
    PREMIERE_COLORS = [
        'Violet', 'Iris', 'Caribbean', 'Lavender', 'Cerulean',
        'Forest', 'Rose', 'Mango', 'Purple', 'Blue',
        'Teal', 'Magenta', 'Tan', 'Green', 'Brown', 'Yellow'
    ]
    
    # Create 6-second segments from each clip
    six_second_segments = []
    
    for clip_idx, clip in enumerate(all_clips):
        # Get clip in/out points
        in_elem = clip.find('in')
        out_elem = clip.find('out')
        
        if in_elem is None or out_elem is None:
            continue
        
        clip_in = int(in_elem.text)
        clip_out = int(out_elem.text)
        clip_total_frames = clip_out - clip_in
        
        # Calculate how many 6-second segments we can make
        num_segments = int(clip_total_frames / clip_duration_frames)
        
        # Assign color to this source clip - ONLY ADDITION
        color = PREMIERE_COLORS[clip_idx % len(PREMIERE_COLORS)]
        
        # Create segments
        for segment_idx in range(num_segments):
            # Deep copy the clip
            new_clip = copy.deepcopy(clip)
            
            # Calculate new in/out points
            segment_in = clip_in + (segment_idx * clip_duration_frames)
            segment_out = segment_in + clip_duration_frames
            
            # Update in/out points
            new_clip.find('in').text = str(segment_in)
            new_clip.find('out').text = str(segment_out)
            
            # Update duration
            duration_elem = new_clip.find('duration')
            if duration_elem is not None:
                duration_elem.text = str(clip_duration_frames)
            
            # Give unique ID
            clip_id = f"clipitem-{clip_idx + 1}-{segment_idx + 1}"
            id_elem = new_clip.find('masterclipid')
            if id_elem is not None:
                id_elem.text = clip_id
            
            # Add color label - ONLY ADDITION
            labels_elem = new_clip.find('labels')
            if labels_elem is None:
                labels_elem = ET.SubElement(new_clip, 'labels')
            label2_elem = labels_elem.find('label2')
            if label2_elem is None:
                label2_elem = ET.SubElement(labels_elem, 'label2')
            label2_elem.text = color
            
            six_second_segments.append(new_clip)
    
    print(f"Created {len(six_second_segments)} six-second clips")
    
    # Advanced shuffle: ensure no consecutive clips from same source
    def smart_shuffle(clips):
        """Shuffle clips ensuring no two consecutive clips are from the same source video"""
        if len(clips) < 2:
            return clips
        
        # Group clips by source (using file reference or name)
        clip_groups = {}
        for clip in clips:
            # Get the file reference to identify source video
            file_elem = clip.find('.//file')
            if file_elem is not None:
                file_id = file_elem.get('id', 'unknown')
            else:
                # Fallback to clip name
                name_elem = clip.find('name')
                file_id = name_elem.text if name_elem is not None else 'unknown'
            
            if file_id not in clip_groups:
                clip_groups[file_id] = []
            clip_groups[file_id].append(clip)
        
        # Shuffle within each group
        for group in clip_groups.values():
            random.shuffle(group)
        
        # Build result ensuring no consecutive clips from same source
        result = []
        source_ids = list(clip_groups.keys())
        random.shuffle(source_ids)
        
        # Create iterators for each source
        iterators = {src: iter(clip_groups[src]) for src in source_ids}
        last_used_source = None
        
        # Keep going until all clips are used
        attempts = 0
        max_attempts = len(clips) * 10
        
        while len(result) < len(clips) and attempts < max_attempts:
            attempts += 1
            
            # Get available sources (not the last one used and still have clips)
            available_sources = [
                src for src in source_ids 
                if src != last_used_source and src in iterators
            ]
            
            # If no available sources (shouldn't happen with good distribution), allow any
            if not available_sources:
                available_sources = [src for src in source_ids if src in iterators]
            
            if not available_sources:
                break
            
            # Pick random source from available
            chosen_source = random.choice(available_sources)
            
            try:
                # Get next clip from chosen source
                clip = next(iterators[chosen_source])
                result.append(clip)
                last_used_source = chosen_source
            except StopIteration:
                # This source is exhausted, remove it
                del iterators[chosen_source]
                source_ids.remove(chosen_source)
        
        return result
    
    six_second_segments = smart_shuffle(six_second_segments)
    print("Shuffled clips with smart algorithm (no consecutive clips from same source)")
    print("Color labels assigned to each source video") # ONLY ADDITION
    
    # Clear all video tracks
    for track in video_tracks:
        for clip in track.findall('clipitem'):
            track.remove(clip)
    
    # Put all shuffled clips on the first track
    first_track = video_tracks[0]
    current_position = 0
    
    for idx, clip in enumerate(six_second_segments):
        # Update start/end times on timeline
        start_elem = clip.find('start')
        end_elem = clip.find('end')
        
        if start_elem is not None:
            start_elem.text = str(current_position)
        if end_elem is not None:
            end_elem.text = str(current_position + clip_duration_frames)
        
        # Add to track
        first_track.append(clip)
        current_position += clip_duration_frames
    
    # Update sequence duration
    duration_elem = sequence.find('duration')
    if duration_elem is not None:
        duration_elem.text = str(current_position)
    
    # Save processed XML
    try:
        # Write with proper XML declaration and encoding
        tree.write(output_xml_path, 
                  encoding='utf-8', 
                  xml_declaration=True,
                  method='xml')
        
        print(f"\n✓ Processed XML saved to: {output_xml_path}")
        print(f"✓ Total clips: {len(six_second_segments)}")
        print(f"✓ Timeline duration: ~{len(six_second_segments) * clip_duration} seconds")
        return True
    except Exception as e:
        print(f"ERROR: Could not save XML: {e}")
        return False

def main():
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PREMIERE PRO XML PROCESSOR" + " " * 27 + "║")
    print("║" + " " * 20 + "Cut & Shuffle Tool" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")
    
    # Get input file
    print("Step 1: Export XML from Premiere Pro")
    print("  File → Export → Final Cut Pro XML")
    print("  Save it in this folder as 'timeline.xml'\n")
    
    input_file = 'timeline.xml'
    
    if not Path(input_file).exists():
        print(f"ERROR: Could not find '{input_file}'")
        print("\nPlease:")
        print("  1. Export your Premiere timeline as Final Cut Pro XML")
        print("  2. Save it as 'timeline.xml' in the same folder as this script")
        print("  3. Run this script again")
        input("\nPress Enter to exit...")
        return
    
    # Settings
    print("Settings: Cutting all clips to 6 seconds and shuffling")
    print("-" * 70)
    print()
    
    # Process
    output_file = 'timeline_processed.xml'
    
    success = process_premiere_xml(input_file, output_file, clip_duration=6)
    
    if success:
        print("\n" + "=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Go to Premiere Pro")
        print("  2. File → Import → timeline_processed.xml")
        print("  3. Your clips are cut to 6 seconds and shuffled!")
        print("\nNote: All clips will be on a single video track")
    
    print("\n")
    input("Press Enter to close...")

if __name__ == "__main__":
    main()