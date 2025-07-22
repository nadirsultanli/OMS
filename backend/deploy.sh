#!/bin/bash

# Railway Deployment Script for OMS Backend

set -e

echo "🚀 Starting Railway deployment..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please login first:"
    echo "   railway login"
    exit 1
fi

# Build and deploy
echo "📦 Building and deploying to Railway..."
railway up

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
sleep 10

# Check health
echo "🏥 Checking application health..."
HEALTH_URL=$(railway status --json | jq -r '.services[0].url')/health

if curl -f "$HEALTH_URL" > /dev/null 2>&1; then
    echo "✅ Deployment successful! Application is healthy."
    echo "🌐 Your app is available at: $(railway status --json | jq -r '.services[0].url')"
else
    echo "❌ Health check failed. Check logs with: railway logs"
    exit 1
fi

echo "🎉 Deployment completed successfully!" 