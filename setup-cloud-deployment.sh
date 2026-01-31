#!/bin/bash
# Setup Scriber & Thinker for Cloud Deployment

echo "🚀 PREPARING SCRIBER & THINKER FOR CLOUD DEPLOYMENT..."

# Create deployment packages
echo "📦 Creating deployment packages..."

# Scriber package
mkdir -p deploy/scriber
cp scriber/server.py deploy/scriber/
cp scriber/index.html deploy/scriber/
cp scriber/requirements.txt deploy/scriber/
cp scriber/Procfile deploy/scriber/

# Thinker package  
mkdir -p deploy/thinker
cp thinker/server.py deploy/thinker/
cp thinker/index.html deploy/thinker/
cp thinker/requirements.txt deploy/thinker/
cp thinker/Procfile deploy/thinker/
mkdir -p deploy/thinker/generated_images

# Create README files
cat > deploy/scriber/README.md << 'EOF'
# 🔥 SCRIBER - YouTube SEO Optimizer

**AI-powered YouTube description, tags, and disclaimer generator**

## Features:
- Extract YouTube transcripts & metadata
- Generate SEO-optimized descriptions  
- Create professional disclaimers
- Optimize tags for maximum reach
- Claude AI powered analysis

## Deploy to Railway:
1. Upload this folder to Railway
2. Connect custom domain
3. Access at: https://yourdomain.com

Runs on Python Flask + Claude AI
EOF

cat > deploy/thinker/README.md << 'EOF'
# 🧠 THINKER - YouTube Thumbnail Analyzer

**AI-powered YouTube thumbnail analysis and content generation**

## Features:
- Analyze YouTube thumbnails
- Generate title suggestions
- Create caption ideas
- ImageFX prompt generation
- Claude AI powered insights

## Deploy to Railway:
1. Upload this folder to Railway  
2. Connect custom domain
3. Access at: https://yourdomain.com

Runs on Python Flask + Claude AI
EOF

echo "✅ Deployment packages created in ./deploy/"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Go to https://railway.app and sign up"
echo "2. Create new project → Deploy from folder"
echo "3. Upload deploy/scriber folder → Deploy"
echo "4. Upload deploy/thinker folder → Deploy"
echo "5. Add custom domains in Railway dashboard"
echo "6. Update GoDaddy DNS with CNAME records"
echo ""
echo "🌐 FINAL RESULT:"
echo "- https://scriber.yourdomain.com (SEO optimizer)"
echo "- https://thinker.yourdomain.com (Thumbnail analyzer)"
echo "- Available 24/7 from anywhere!"