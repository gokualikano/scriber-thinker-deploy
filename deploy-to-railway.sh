#!/bin/bash

echo "🚀 Railway Deployment Script"
echo "============================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

echo "🔐 Step 1: Login to Railway"
railway login

echo ""
echo "📝 Step 2: Deploy Scriber"
echo "------------------------"
cd scriber
railway init
echo "Enter project name: scriber-app"
railway variables set ACCESS_PASSWORD=scriber2024
railway variables set SECRET_KEY=your-super-secret-key-for-scriber-production-$(date +%s)
railway deploy

echo ""
echo "📝 Step 3: Deploy Thinker"  
echo "------------------------"
cd ../thinker
railway init
echo "Enter project name: thinker-app"
railway variables set ACCESS_PASSWORD=thinker2024
railway variables set SECRET_KEY=your-super-secret-key-for-thinker-production-$(date +%s)
railway deploy

echo ""
echo "✅ Deployment Complete!"
echo "======================="
echo ""
echo "Your apps are now live on Railway:"
echo "📝 Scriber: Check Railway dashboard for URL"
echo "🎨 Thinker: Check Railway dashboard for URL"
echo ""
echo "Default passwords:"
echo "• Scriber: scriber2024"
echo "• Thinker: thinker2024"
echo ""
echo "Next steps:"
echo "1. Go to Railway dashboard (railway.app)"
echo "2. Configure custom domains if needed"
echo "3. Update passwords by running:"
echo "   railway variables set ACCESS_PASSWORD=your-new-password"