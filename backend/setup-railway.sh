#!/bin/bash

# Railway Setup Script for OMS Backend

set -e

echo "🔧 Setting up Railway configuration..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway:"
    railway login
fi

# Initialize Railway project if not already done
if [ ! -f "railway.toml" ]; then
    echo "🚀 Initializing Railway project..."
    railway init
fi

# Set up environment variables
echo "⚙️ Setting up environment variables..."
echo "Please set the following environment variables in Railway Dashboard:"
echo ""
echo "Required:"
echo "- ENVIRONMENT=production"
echo "- LOG_LEVEL=INFO"
echo "- PORT=8000"
echo "- DATABASE_URL=your_railway_postgresql_url"
echo "- SUPABASE_URL=your_supabase_url"
echo "- SUPABASE_KEY=your_supabase_anon_key"
echo "- SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key"
echo ""
echo "Optional:"
echo "- ALLOWED_ORIGINS=https://your-frontend-domain.com"
echo "- API_HOST=0.0.0.0"
echo "- API_PORT=8000"
echo ""

# Test local build
echo "🧪 Testing local build..."
docker build -t oms-backend-test .

echo "✅ Setup completed!"
echo ""
echo "Next steps:"
echo "1. Set environment variables in Railway Dashboard"
echo "2. Run: ./deploy.sh"
echo "3. Or deploy manually: railway up" 