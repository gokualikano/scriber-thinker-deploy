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

## Content Radar - MEGA UPGRADE (2026-01-30)
**Status:** ✅ COMPLETE - 15+ APIs integrated, all channels operational

### New Capabilities Added:
- **15+ Free APIs:** HackerNews, Google Trends, GDELT, NewsAPI, GNews, YouTube API
- **N1 - TECH Channel:** Elon Musk, Sam Altman, AI news focus
- **Auto Trello Cards:** `radar_to_trello.py` creates cards with ALL links found
- **115+ links per execution** across 5 channels
- **Google Trends Integration:** pytrends working (AI=67 rising, Taylor Swift=13 falling)
- **HackerNews Perfect for N1:** 12+ tech stories (Claude benchmarks=543pts)

### Services Running:
- **Thinker:** https://kills-publicly-far-olympic.trycloudflare.com ✅
- **Scriber:** https://total-mayor-steady-television.trycloudflare.com ✅  
- **All APIs:** Monitoring 24/7, 15-60 min head start vs competitors
- **Cost:** Still $0.00/month

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

- **ImageBoost** (`~/clawd/image-boost/`) - NEW 2026-01-31
  - 4x smart upscale + AI background removal tool
  - Pure Pillow processing (zero ongoing costs)
  - Bulk processing with individual downloads
  - Color-preserving algorithm using corner detection
  - External access via cloudflare tunnels
  - Built in 3 hours (~$0.70 development cost)
  - Production ready, works like Thinker for images

## Thinker - Thumbnail Generator Workflow (H1 & H3)
**Input:** YouTube link (competitor video)
**Output:**
1. 🎨 **ImageFX Prompt** (Malik's style)
2. 📝 **5 Titles** (80-100 characters each)
3. 🔥 **10 Thumbnail Captions** (3-5 words, urgent news-style)

### ImageFX Prompt Style (CRITICAL)
- Similar scene to competitor but **DIFFERENT PERSPECTIVE** (rotate: ground level, aerial, dashcam, overpass, roadside, crowd POV, fishing boat, rooftop, etc.)
- **MORE chaos/destruction** than original
- Topic-specific enhancements:
  - Ice storm → more crashed trucks, black ice, chain reaction pileups
  - Floods → huge waves crashing into buildings, cars floating
  - Volcano → more lava erupting, flowing downhill, destroying structures
  - Earthquake → collapsed buildings, rubble, cracks in ground
- **ALWAYS include:** motion blur, shaky hands, low resolution, grainy footage, compression artifacts, realistic raw cellphone video screenshot
- **NO text** in the image

### Thumbnail Captions Style
- 10 captions per video (MIX of both styles)
- **Topic-specific:** Relates to the actual disaster (FROZEN CHAOS, COASTLINE CRUMBLING, ETNA AWAKENS, 40 MILES TRAPPED, LAVA FLOWING, TOWN UNDERWATER, etc.)
- **Urgent news-style:** General high-CTR urgency (NO ONE EXPECTED THIS, IT HAPPENED SO FAST, SITUATION CRITICAL, OFFICIAL WARNING ISSUED, BREAKING RIGHT NOW, THIS IS SHOCKING, etc.)
- Always mix ~5 topic-specific + ~5 urgent news-style for variety

### Script Location
`~/clawd/scripts/extract_transcript.py` - extracts YouTube transcripts (built 2026-01-29)

### Scriber - YouTube SEO Optimizer
**Location:** `~/clawd/scriber/`
**Local URL:** http://localhost:8586
**Remote URL:** https://tim-puerto-seniors-refresh.trycloudflare.com
**Start server:** `cd ~/clawd/scriber && source venv/bin/activate && python server.py`
**Features:** Extracts transcript/description/tags → generates SEO description, disclaimer, optimized tags

### Thinker Dashboard
**Location:** `~/clawd/thinker/`
**Local URL:** http://localhost:8585
**Remote URL:** https://msgstr-dat-replies-charleston.trycloudflare.com (via cloudflared tunnel)
**Start server:** `cd ~/clawd/thinker && source venv/bin/activate && python server.py`
**Start tunnel:** `cloudflared tunnel --url http://localhost:8585` (gets new URL each time)

**Features:**
- Enter YouTube URL → fetches thumbnail + video info
- Paste Jarvis response → parses into prompts/titles/captions
- Copy buttons for everything
- ImageFX tab with "Open ImageFX" button
- History of previous generations

### PRGrabber - Premiere Pro Image Grabber (2026-01-31)
**Goal:** Copy web images → paste directly in Premiere Pro timeline (no manual save/drag)
**Solution:** Adobe CEP extension running INSIDE Premiere Pro

**Status:** ✅ Installed, CEP developer mode enabled - needs Premiere restart
**Location:** `/Users/malikano/Library/Application Support/Adobe/CEP/extensions/com.prgrabber.premiere/`

**Usage:**
1. Restart Premiere Pro → Window → Extensions → PRGrabber
2. Copy image URL from any website (Google Images, etc.)
3. Paste URL in PRGrabber panel → Click "Import to Timeline"
4. Image downloads & imports directly to timeline at playhead position

**Works with:** Cracked Premiere Pro 2022 (no licensing checks)
**Workflow:** Copy URL → Paste → Import (2 steps vs traditional 6+ steps)

## Permanent Cloud Hosting Setup (2026-02-01)
**Problem:** Scriber/Thinker not working on other laptop, need 24/7 access
**Solution:** Railway + GoDaddy domain with password protection

**Deployment Status:** Ready for deployment
- `deploy/scriber/` & `deploy/thinker/` packages created
- Railway hosting (FREE tier - 500 hours/month)
- Simple password authentication for private access
- Multiple concurrent users supported

**Target URLs:** 
- https://scriber.yourdomain.com (password protected)
- https://thinker.yourdomain.com (password protected)
- Cost: $0/month

**Files Created:**
- Complete deployment packages with requirements.txt, Procfile
- `GODADDY-DOMAIN-SETUP.md` - step-by-step guide
- `private-hosting-setup.md` - authentication options

## YouTube Niche Research (2026-02-01)
**High-Success Video-Rich Niches:** (Content exists for fair use commentary)
1. **Airline Passenger Freakout Breakdowns** - 85% success probability
2. **Food Safety Violation Breakdowns** - 82%
3. **Cryptocurrency Rug Pull Exposés** - 78%
4. **HOA Meeting Meltdowns** - 75%
5. **Workplace Harassment Caught on Camera** - 73%

**Key Requirements:** Abundant footage available, fair use friendly, high engagement potential

## Intelligent Video Editing Concept
**Goal:** Smart visual-audio matching for 6-second rule compliance
**System Design:**
- Parse voiceover transcript for subjects/actions/timeframes
- Analyze footage library with face detection & content recognition
- Intelligent matching: "Taylor Swift went to restaurant" → restaurant footage of Taylor
- Fallback hierarchy: Perfect match → Related → Context → Generic B-roll

**Video Analysis:** Studied Taylor Swift/Travis Kelce format (11m 25s)
- Multi-topic teaser opening, 2-5min story blocks, quote integration
- Highly templatable structure perfect for automation

## Lead Generation Strategy
**Investment Leads ($1500+ passive income partnerships):**
- BiggerPockets real estate investors
- Reddit: r/passive_income, r/investing, r/sidehustle
- Target: 25-45 professionals, small business owners

**Video Editing Clients:**
- YouTubers 10K-100K subs (have budget, scaling needs)
- Business channels, educational creators, real estate
- Platforms: Upwork, Fiverr, LinkedIn targeted outreach

**Approach:** Content-first marketing vs direct cold outreach for compliance
