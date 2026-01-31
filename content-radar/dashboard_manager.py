#!/usr/bin/env python3
"""
Dashboard Manager - Auto-manages content cards with priority system
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
import sys

# Add venv packages
VENV_PATH = Path(__file__).parent / "venv" / "lib"
for p in VENV_PATH.glob("python*/site-packages"):
    sys.path.insert(0, str(p))

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "dashboard_data.json"


def load_data():
    """Load dashboard data"""
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text())
    return {"lastUpdated": "", "cards": []}


def save_data(data):
    """Save dashboard data"""
    data["lastUpdated"] = datetime.now().isoformat()
    DATA_PATH.write_text(json.dumps(data, indent=2))


def demote_high_priority():
    """Demote all HIGH priority cards to MEDIUM"""
    data = load_data()
    changed = False
    for card in data["cards"]:
        if card.get("priority") == "high":
            card["priority"] = "medium"
            card["demotedAt"] = datetime.now().isoformat()
            changed = True
    if changed:
        save_data(data)
    return changed


def add_card(title, content_type, source, url, priority="high", 
             views=None, subscribers=None, posted_at=None, 
             channel=None, summary=None, tags=None):
    """
    Add a new card to the dashboard
    
    Args:
        title: Card title
        content_type: 'news' or 'video'
        source: Source name (e.g., 'US Weekly', 'TMZ', channel name)
        url: Link to content
        priority: 'high', 'medium', 'low'
        views: Video view count (for videos)
        subscribers: Channel subscriber count (for videos)
        posted_at: When the content was posted
        channel: YouTube channel name (for videos)
        summary: Brief description
        tags: List of tags
    """
    data = load_data()
    
    # Check for duplicate URLs
    existing_urls = [c.get("url") for c in data["cards"]]
    if url in existing_urls:
        print(f"Card with URL already exists: {url}")
        return None
    
    # If new card is HIGH priority, demote existing HIGH cards to MEDIUM
    if priority == "high":
        demote_high_priority()
        data = load_data()  # Reload after demotion
    
    card = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "type": content_type,
        "source": source,
        "url": url,
        "priority": priority,
        "createdAt": datetime.now().isoformat(),
        "views": views,
        "subscribers": subscribers,
        "postedAt": posted_at,
        "channel": channel,
        "summary": summary,
        "tags": tags or [],
        "status": "new"  # new, working, done, skipped
    }
    
    # Insert at beginning (newest first)
    data["cards"].insert(0, card)
    save_data(data)
    
    print(f"✅ Added card: [{priority.upper()}] {title}")
    return card


def update_card(card_id, **kwargs):
    """Update a card's fields"""
    data = load_data()
    for card in data["cards"]:
        if card["id"] == card_id:
            for key, value in kwargs.items():
                if value is not None:
                    card[key] = value
            card["updatedAt"] = datetime.now().isoformat()
            save_data(data)
            print(f"✅ Updated card {card_id}")
            return card
    print(f"❌ Card not found: {card_id}")
    return None


def set_priority(card_id, priority):
    """Set a card's priority"""
    if priority == "high":
        demote_high_priority()
    return update_card(card_id, priority=priority)


def set_status(card_id, status):
    """Set a card's status (new, working, done, skipped)"""
    return update_card(card_id, status=status)


def remove_card(card_id):
    """Remove a card"""
    data = load_data()
    data["cards"] = [c for c in data["cards"] if c["id"] != card_id]
    save_data(data)
    print(f"✅ Removed card {card_id}")


def list_cards(priority=None, status=None, limit=20):
    """List cards with optional filters"""
    data = load_data()
    cards = data["cards"]
    
    if priority:
        cards = [c for c in cards if c.get("priority") == priority]
    if status:
        cards = [c for c in cards if c.get("status") == status]
    
    return cards[:limit]


def clear_old_cards(days=7):
    """Remove cards older than X days"""
    data = load_data()
    cutoff = datetime.now().timestamp() - (days * 86400)
    
    original_count = len(data["cards"])
    data["cards"] = [
        c for c in data["cards"]
        if datetime.fromisoformat(c["createdAt"]).timestamp() > cutoff
    ]
    removed = original_count - len(data["cards"])
    
    if removed:
        save_data(data)
        print(f"✅ Removed {removed} old cards")
    
    return removed


def add_news(title, source, url, priority="high", summary=None, tags=None):
    """Shortcut to add a news card"""
    return add_card(
        title=title,
        content_type="news",
        source=source,
        url=url,
        priority=priority,
        summary=summary,
        tags=tags
    )


def add_video(title, channel, url, views, subscribers=None, 
              posted_at=None, priority="high", tags=None):
    """Shortcut to add a video card"""
    return add_card(
        title=title,
        content_type="video",
        source=channel,
        url=url,
        priority=priority,
        views=views,
        subscribers=subscribers,
        posted_at=posted_at,
        channel=channel,
        tags=tags
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Dashboard Manager")
    subparsers = parser.add_subparsers(dest="command")
    
    # List command
    list_p = subparsers.add_parser("list", help="List cards")
    list_p.add_argument("--priority", choices=["high", "medium", "low"])
    list_p.add_argument("--status", choices=["new", "working", "done", "skipped"])
    list_p.add_argument("--limit", type=int, default=20)
    
    # Add news command
    news_p = subparsers.add_parser("add-news", help="Add news card")
    news_p.add_argument("title")
    news_p.add_argument("--source", required=True)
    news_p.add_argument("--url", required=True)
    news_p.add_argument("--priority", default="high", choices=["high", "medium", "low"])
    news_p.add_argument("--summary")
    news_p.add_argument("--tags", nargs="*")
    
    # Add video command
    video_p = subparsers.add_parser("add-video", help="Add video card")
    video_p.add_argument("title")
    video_p.add_argument("--channel", required=True)
    video_p.add_argument("--url", required=True)
    video_p.add_argument("--views", type=int, required=True)
    video_p.add_argument("--subscribers", type=int)
    video_p.add_argument("--posted", help="Posted time")
    video_p.add_argument("--priority", default="high", choices=["high", "medium", "low"])
    video_p.add_argument("--tags", nargs="*")
    
    # Update command
    update_p = subparsers.add_parser("update", help="Update card")
    update_p.add_argument("card_id")
    update_p.add_argument("--priority", choices=["high", "medium", "low"])
    update_p.add_argument("--status", choices=["new", "working", "done", "skipped"])
    
    # Remove command
    remove_p = subparsers.add_parser("remove", help="Remove card")
    remove_p.add_argument("card_id")
    
    # Clear old command
    clear_p = subparsers.add_parser("clear-old", help="Clear old cards")
    clear_p.add_argument("--days", type=int, default=7)
    
    args = parser.parse_args()
    
    if args.command == "list":
        cards = list_cards(priority=args.priority, status=args.status, limit=args.limit)
        for c in cards:
            prio = c.get("priority", "?")[0].upper()
            status = c.get("status", "new")[:4]
            print(f"[{prio}] [{status}] {c['id']} | {c['title'][:50]}")
    
    elif args.command == "add-news":
        add_news(args.title, args.source, args.url, args.priority, args.summary, args.tags)
    
    elif args.command == "add-video":
        add_video(args.title, args.channel, args.url, args.views, 
                  args.subscribers, args.posted, args.priority, args.tags)
    
    elif args.command == "update":
        update_card(args.card_id, priority=args.priority, status=args.status)
    
    elif args.command == "remove":
        remove_card(args.card_id)
    
    elif args.command == "clear-old":
        clear_old_cards(args.days)
    
    else:
        parser.print_help()
