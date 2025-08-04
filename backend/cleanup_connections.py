#!/usr/bin/env python3
"""
Standalone script to clean up idle database connections.
This can be run as a cron job every 2-5 minutes.

Usage:
    python cleanup_connections.py

Or as a cron job (every 2 minutes):
    */2 * * * * cd /path/to/OMS/backend && python cleanup_connections.py
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    """Main function to run connection cleanup"""
    try:
        from app.infrastucture.database.connection import cleanup_idle_connections
        from app.infrastucture.logs.logger import default_logger
        
        print(f"[{datetime.now()}] Starting connection cleanup...")
        
        # Run the cleanup
        await cleanup_idle_connections()
        
        print(f"[{datetime.now()}] Connection cleanup completed successfully")
        
    except Exception as e:
        print(f"[{datetime.now()}] Connection cleanup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 