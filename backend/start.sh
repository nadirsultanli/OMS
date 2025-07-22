#!/bin/bash

# Railway startup script for OMS Backend
set -e

echo "🚀 Starting OMS Backend for Railway deployment..."

# Set default values
export PORT=${PORT:-8000}
export ENVIRONMENT=${ENVIRONMENT:-production}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Validate required environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL environment variable is required"
    exit 1
fi

if [ -z "$SUPABASE_URL" ]; then
    echo "❌ Error: SUPABASE_URL environment variable is required"
    exit 1
fi

if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ Error: SUPABASE_ANON_KEY environment variable is required"
    exit 1
fi

echo "✅ Environment variables validated"
echo "📡 Starting server on port $PORT"
echo "🌍 Environment: $ENVIRONMENT"
echo "📋 Log level: $LOG_LEVEL"

# Start the application
exec python -m uvicorn app.cmd.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --access-log \
    --log-level info