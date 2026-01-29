# MEMORY.md - Long-Term Memory

## About Malik
- **Name:** Malik Hassan
- **Location:** Pakistan → targets US audience
- **X/Twitter:** @MAlikanoHassan
- **Channels:** H1 (DECRYPT NEWS), H2 (Locked & LAWFUL), H3 (QUAKED)
- **Style:** Talks less, action-oriented, cost-conscious

## YouTube Automation Pipeline
**Status:** ~60% complete  
**Location:** `~/Documents/clawdbot_safe_backup/clawdbot_system/`

### Completed
- Transcript extraction
- Script generation (1400-1900 words, Malik's narrative style)
- Title generation (high-CTR)
- Trello integration (cards with labels)
- Local .docx file creation & attachment

### Missing
- Voiceover system (ElevenLabs ready)
- Thumbnail generation (H1/H3 disasters, H2 politicians)
- Competitor analysis (Bing API)
- WhatsApp automation triggers

### Key Files
- `video_orchestrator.py` - main pipeline
- `script_generator.py` - multi-step generation
- `config.json` - all API keys

### Script Style (Critical)
- Opens: "X people are dead, thousands trapped..."
- NO quotes or interviews
- Ends: "That's it for today folks, see you in the next video."

## Other Projects
- **X Viral Bot** (`~/clawd/x-viral-bot/`) - PAUSED, needs auth tokens
- **Planka** - localhost:3000, admin/admin123

## Preferences
- Ask permission before long explanations
- Real testing > theory
- Cost: <$46/month AI tokens
- Sleep: 3-5 AM PKT

## Session: 2026-01-29
- Built ContentRadar (competitor + alert monitoring)
- Set up cron: 10 AM daily WhatsApp summary
- Business pivot: YouTube monetization service ($5K, 4mo)
- Found investor leads on X (@LeanderHofkes, @jansousek1)
- 2-week roadmap created for client acquisition

## Tools Built
- **ContentRadar** (`~/clawd/content-radar/`)
  - USGS earthquakes, NOAA weather alerts
  - Competitor tracking for H1, H2, H3, R1, R2
  - Daily 10 AM cron job to WhatsApp
