#!/usr/bin/env python3

import asyncio
import asyncpg
from decouple import config

async def check_enum_values():
    """Check the actual enum values in the database"""
    try:
        # Get database connection details
        db_url = config('DATABASE_URL', default='postgresql://postgres:postgres@localhost:5432/postgres')
        
        # Connect to database
        conn = await asyncpg.connect(db_url)
        
        # Check enum values
        result = await conn.fetch("""
            SELECT unnest(enum_range(NULL::trip_status)) as enum_value;
        """)
        
        print("Database enum values:")
        for row in result:
            print(f"  - {row['enum_value']}")
        
        # Check if there are any trips with invalid status
        result2 = await conn.fetch("""
            SELECT DISTINCT trip_status FROM trips WHERE deleted_at IS NULL;
        """)
        
        print("\nTrip status values in database:")
        for row in result2:
            print(f"  - {row['trip_status']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_enum_values()) 