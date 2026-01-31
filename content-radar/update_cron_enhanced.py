#!/usr/bin/env python3
"""
Update existing cron jobs to use enhanced APIs
"""

import json
import subprocess

def update_cron_jobs():
    print("🔄 Updating cron jobs to use enhanced APIs...")
    
    # Update the 4AM scan to use enhanced system
    enhanced_message = """Run ENHANCED ContentRadar scan with ALL FREE APIs. Use ~/clawd/content-radar/enhanced_trello_radar.py --full. 

NEW APIs include:
🌋 EMSC earthquakes (5-15 min before USGS)
🔥 NASA FIRMS wildfire hotspots  
🌍 GDACS global disaster alerts
🏛️ Congress.gov bills & activities
📋 Federal Register ATF regulations
⚖️ Supreme Court cases
📱 Enhanced Reddit trending

This gives us 15-45 minute head start vs competitors. Send WhatsApp summary of high-priority findings."""

    print("Enhanced ContentRadar is ready!")
    print("")
    print("📋 Manual cron update needed:")
    print("Run: clawdbot cron update f15e2300-6de4-46ce-9a1c-d2746364c613")
    print("Then paste this message:")
    print("-" * 50)
    print(enhanced_message)
    print("-" * 50)

if __name__ == "__main__":
    update_cron_jobs()