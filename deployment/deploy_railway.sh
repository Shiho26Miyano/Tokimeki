#!/bin/bash

# Railway Deployment Script for Tokimeki
echo "🚀 Starting Railway deployment for Tokimeki..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run this from your project root."
    exit 1
fi

# Check if there are uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  There are uncommitted changes. Committing them..."
    git add .
    git commit -m "Auto-commit before Railway deployment"
fi

# Check if we're linked to a Railway project
if ! railway status &> /dev/null; then
    echo "🔗 Linking to Railway project..."
    railway link
fi

# Deploy to Railway
echo "📦 Deploying to Railway..."
railway up

echo "✅ Deployment completed!"
echo "🌐 Check your Railway dashboard for deployment status"
echo "🔍 Monitor logs with: railway logs"
