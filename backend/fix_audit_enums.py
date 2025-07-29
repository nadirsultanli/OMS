#!/usr/bin/env python3
"""
Script to fix audit enum values in Supabase database
"""
import os
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def fix_audit_enums():
    """Fix audit enum values to match domain entities"""
    
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
        
        # Add missing enum values to audit_event_type
        event_type_values = [
            'read', 'logout', 'price_change', 'stock_adjustment', 
            'delivery_complete', 'delivery_failed', 'trip_start', 
            'trip_complete', 'credit_approval', 'credit_rejection', 'error'
        ]
        
        print("🔄 Adding missing audit_event_type enum values...")
        for value in event_type_values:
            try:
                await conn.execute(f"ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS '{value}'")
                print(f"✅ Added '{value}' to audit_event_type")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e):
                    print(f"⏭️ '{value}' already exists in audit_event_type")
                else:
                    print(f"❌ Error adding '{value}' to audit_event_type: {e}")
        
        # Add missing enum values to audit_object_type
        object_type_values = [
            'variant', 'warehouse', 'vehicle', 'address', 'delivery', 'other'
        ]
        
        print("🔄 Adding missing audit_object_type enum values...")
        for value in object_type_values:
            try:
                await conn.execute(f"ALTER TYPE audit_object_type ADD VALUE IF NOT EXISTS '{value}'")
                print(f"✅ Added '{value}' to audit_object_type")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e):
                    print(f"⏭️ '{value}' already exists in audit_object_type")
                else:
                    print(f"❌ Error adding '{value}' to audit_object_type: {e}")
        
        print("✅ Audit enum fix completed successfully!")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    import asyncio
    asyncio.run(fix_audit_enums())