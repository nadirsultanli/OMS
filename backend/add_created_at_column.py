#!/usr/bin/env python3
"""
Script to add created_at column to audit_events table
"""
import os
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def add_created_at_column():
    """Add created_at column to audit_events table"""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return
    
    # Convert asyncpg URL to standard postgres URL for asyncpg
    database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to database")
        
        # Add created_at column to audit_events table
        print("🔄 Adding created_at column to audit_events table...")
        await conn.execute("""
            ALTER TABLE audit_events 
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        """)
        print("✅ created_at column added successfully!")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    import asyncio
    asyncio.run(add_created_at_column())