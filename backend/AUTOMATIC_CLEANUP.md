# Automatic Connection Cleanup

## Overview

The OMS Backend automatically cleans up idle database connections to prevent connection pool exhaustion and performance issues.

## How It Works

✅ **Automatic**: Runs every 30 seconds when the app starts
✅ **Safe**: Only terminates problematic "idle in transaction" connections
✅ **No Setup**: Works out of the box, no additional configuration needed
✅ **No Broker**: Uses built-in asyncio background tasks (no Redis/Celery needed)

## What It Does

- **Terminates idle transactions** after 30 seconds
- **Frees up connection pool resources**
- **Prevents connection pool exhaustion**
- **Logs all cleanup activities**

## What It Does NOT Do

- ❌ Does NOT log out users
- ❌ Does NOT terminate active sessions
- ❌ Does NOT affect JWT tokens
- ❌ Does NOT interrupt ongoing requests

## Activation

Simply restart the backend:
```bash
docker-compose restart oms-backend
```

You'll see in the logs:
```
✅ Automatic connection cleanup started (every 30 seconds)
```

## Manual Commands (Admin Only)

```bash
# Force cleanup
curl -X POST "http://localhost:8000/api/v1/system/cleanup-connections"

# Check connection status
curl -X GET "http://localhost:8000/api/v1/system/connection-status"
```

## Database Commands

```sql
-- Manual cleanup
SELECT cleanup_idle_connections_aggressive();

-- Check connections
SELECT state, COUNT(*) FROM pg_stat_activity 
WHERE datname = current_database() 
GROUP BY state;
```

## Configuration

The system uses optimized connection pool settings:
- Pool size: 3 connections
- Statement timeout: 15 seconds
- Idle transaction timeout: 30 seconds
- Pool recycle: 1 minute

## Monitoring

Check the application logs for cleanup messages:
```
✅ Aggressive connection cleanup completed: 2 connections terminated
✅ No connections needed cleanup
```

The system is now clean and simple - just automatic cleanup without any external dependencies! 