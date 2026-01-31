#!/bin/bash
# Setup API Keys for Free Tier Services

echo "🔑 API Key Setup for Free Tier Services"
echo "========================================="
echo ""

echo "📝 Free API Keys Needed:"
echo ""

echo "1️⃣  NewsAPI.org (100 requests/day)"
echo "   • Sign up: https://newsapi.org/register"
echo "   • Get key: https://newsapi.org/account"
echo "   • Set: export NEWSAPI_KEY='your_key_here'"
echo ""

echo "2️⃣  GNews API (100 requests/day)" 
echo "   • Sign up: https://gnews.io/"
echo "   • Get key from dashboard"
echo "   • Set: export GNEWS_API_KEY='your_key_here'"
echo ""

echo "3️⃣  YouTube Data API (10,000 units/day)"
echo "   • Create project: https://console.developers.google.com"
echo "   • Enable YouTube Data API v3"
echo "   • Create credentials > API key"
echo "   • Set: export YOUTUBE_API_KEY='your_key_here'"
echo ""

echo "🆓 Already Working (No Keys Needed):"
echo "   ✅ Reddit API (rate limited)"
echo "   ✅ HackerNews API (unlimited)"
echo "   ✅ GDELT Project (unlimited)"
echo "   ✅ All previous APIs (EMSC, NASA, etc.)"
echo ""

echo "💾 To make permanent, add to ~/.zshrc:"
echo "echo 'export NEWSAPI_KEY=\"your_key\"' >> ~/.zshrc"
echo "echo 'export GNEWS_API_KEY=\"your_key\"' >> ~/.zshrc"
echo "echo 'export YOUTUBE_API_KEY=\"your_key\"' >> ~/.zshrc"
echo "source ~/.zshrc"
echo ""

echo "🧪 Test with keys:"
echo "cd ~/clawd/content-radar && source venv/bin/activate"
echo "python mega_viral_apis.py --news"
echo "python mega_viral_apis.py --tech"
echo "python mega_viral_apis.py --quotas"
echo ""

echo "🚀 Without keys, you still get:"
echo "   • All 7 previous free APIs"
echo "   • HackerNews trending"
echo "   • GDELT global events"
echo "   • Enhanced Reddit intelligence"