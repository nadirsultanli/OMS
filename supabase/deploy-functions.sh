#!/bin/bash

# Supabase Edge Functions Deployment Script
# Deploys the audit-logger function for high-volume audit logging

set -e

echo "🚀 Deploying Supabase Edge Functions for OMS Audit System"

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Please install it first:"
    echo "   npm install -g supabase"
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f "config.toml" ]; then
    echo "❌ config.toml not found. Make sure you're in the supabase directory."
    exit 1
fi

# Login to Supabase (if not already logged in)
echo "🔐 Checking Supabase authentication..."
if ! supabase status &> /dev/null; then
    echo "📝 Please login to Supabase:"
    supabase login
fi

# Link to your project (if not already linked)
echo "🔗 Linking to Supabase project..."
if [ -z "$SUPABASE_PROJECT_REF" ]; then
    echo "⚠️  SUPABASE_PROJECT_REF environment variable not set."
    echo "   Please set it to your project reference (found in your Supabase dashboard URL)"
    echo "   Example: export SUPABASE_PROJECT_REF=your-project-ref"
    echo "   Or run: supabase link --project-ref your-project-ref"
    read -p "Enter your project reference: " project_ref
    supabase link --project-ref "$project_ref"
else
    supabase link --project-ref "$SUPABASE_PROJECT_REF"
fi

# Deploy the audit-logger function
echo "📦 Deploying audit-logger Edge Function..."
supabase functions deploy audit-logger --no-verify-jwt

# Set environment variables for the function
echo "🔧 Setting up environment variables..."

# Check if environment variables are set
if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "⚠️  SUPABASE_SERVICE_ROLE_KEY not set in environment"
    echo "   Please set this environment variable with your service role key"
    echo "   You can find it in: Supabase Dashboard → Settings → API → service_role"
    read -s -p "Enter your service role key: " service_key
    echo
    supabase secrets set SUPABASE_SERVICE_ROLE_KEY="$service_key"
else
    supabase secrets set SUPABASE_SERVICE_ROLE_KEY="$SUPABASE_SERVICE_ROLE_KEY"
fi

# Optional: Set other environment variables if needed
if [ -n "$GOOGLE_CLIENT_ID" ]; then
    supabase secrets set GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID"
fi

if [ -n "$GOOGLE_CLIENT_SECRET" ]; then
    supabase secrets set GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET"
fi

echo "✅ Edge Functions deployed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Test the function: supabase functions serve"
echo "2. Update your backend environment variables:"
echo "   - SUPABASE_URL=https://your-project-ref.supabase.co"
echo "   - SUPABASE_ANON_KEY=your-anon-key"
echo "3. Use the high-volume audit logging in your application"
echo ""
echo "🔗 Function URL: https://your-project-ref.supabase.co/functions/v1/audit-logger"
echo ""
echo "📖 For more information, see: functions/audit-logger/README.md"