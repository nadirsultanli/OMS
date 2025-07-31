#!/usr/bin/env python3
"""
Script to apply payments table migration to Supabase database
"""

import asyncio
from app.infrastucture.database.connection import get_supabase_client_sync
from app.infrastucture.logs.logger import default_logger

def apply_payment_migration():
    """Apply the payments table migration"""
    try:
        # Get Supabase client
        client = get_supabase_client_sync()
        print("✅ Connected to Supabase")
        
        # Read the migration SQL
        with open('migrations/024_create_payments_table.sql', 'r') as f:
            migration_sql = f.read()
        
        print("📄 Migration SQL loaded")
        
        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        print(f"🔧 Applying {len(statements)} SQL statements...")
        
        # Apply each statement
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    print(f"  {i}/{len(statements)}: {statement[:50]}...")
                    # Execute the SQL statement using Supabase's rpc function
                    result = client.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"    ✅ Statement {i} executed successfully")
                except Exception as e:
                    print(f"    ⚠️ Statement {i} failed: {str(e)}")
                    # Continue with other statements
                    continue
        
        print("✅ Migration completed!")
        
        # Test if tables were created
        try:
            # Test payments table
            result = client.table('payments').select('id').limit(1).execute()
            print("✅ Payments table exists and is accessible")
        except Exception as e:
            print(f"❌ Payments table test failed: {str(e)}")
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        default_logger.error(f"Migration failed: {str(e)}")

if __name__ == "__main__":
    apply_payment_migration() 