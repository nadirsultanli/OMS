#!/bin/sh
set -e

# Set default port if not provided
PORT=${PORT:-8000}

echo "🚀 Starting OMS Backend on port $PORT"
echo "Environment: ${ENVIRONMENT:-development}"

# Start the application with the resolved port
exec python -m uvicorn app.cmd.main:app --host 0.0.0.0 --port "$PORT"