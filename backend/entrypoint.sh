#!/bin/sh
set -e

# If $PORT is not set by Railway, fallback to 8000
PORT=${PORT:-8000}

echo "🚀 Starting OMS Backend on port $PORT"
echo "Environment: ${ENVIRONMENT:-development}"

exec uvicorn app.cmd.main:app --host 0.0.0.0 --port "$PORT"