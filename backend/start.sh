#!/bin/bash

# Railway startup script for OMS Backend
set -e

echo "🚀 Starting OMS Backend for Railway deployment..."

# Set default values
export PORT=${PORT:-8000}
export ENVIRONMENT=${ENVIRONMENT:-production}
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export USE_RAILWAY_MODE=true

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

if [ -z "$SUPABASE_KEY" ] && [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ Error: SUPABASE_KEY or SUPABASE_ANON_KEY environment variable is required"
    exit 1
fi

echo "✅ Environment variables validated"
echo "📡 Starting server on port $PORT with ${WORKERS:-4} workers"
echo "🌍 Environment: $ENVIRONMENT"
echo "📋 Log level: $LOG_LEVEL"
echo "🚀 Max requests per worker: ${MAX_REQUESTS:-1000}"

# Start the application
exec python -m uvicorn app.cmd.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers ${WORKERS:-4} \
    --worker-class uvicorn.workers.UvicornWorker \
    --max-requests ${MAX_REQUESTS:-1000} \
    --max-requests-jitter ${MAX_REQUESTS_JITTER:-100} \
    --access-log \
    --log-level info