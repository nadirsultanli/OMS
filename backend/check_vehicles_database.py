#!/usr/bin/env python3
"""
Script to check the vehicles table structure and data in the database
"""

import asyncio
import os
import sys
from decouple import config
from supabase import create_client, Client

async def main():
    print("🔍 Checking Vehicles Database Structure and Data")
    print("=" * 60)
    
    try:
        # Try to get database connection details from environment
        supabase_url = config("SUPABASE_URL", default=None)
        supabase_key = config("SUPABASE_KEY", default=None) or config("SUPABASE_ANON_KEY", default=None)
        
        if not supabase_url or not supabase_key:
            print("❌ No database connection details found in environment variables")
            print("   Looking for SUPABASE_URL and SUPABASE_KEY/SUPABASE_ANON_KEY")
            print("\n📋 Available environment variables:")
            for key in sorted(os.environ.keys()):
                if 'DATABASE' in key or 'SUPABASE' in key:
                    value = os.environ[key]
                    # Mask sensitive data
                    if len(value) > 20:
                        value = value[:10] + "..." + value[-10:]
                    print(f"   {key}={value}")
            return
        
        print(f"🌐 Connecting to Supabase: {supabase_url[:30]}...")
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # 1. Check vehicles table structure
        print("\n📊 Vehicles Table Structure:")
        print("-" * 40)
        
        # Query a few sample vehicles to understand the structure
        vehicles_response = supabase.table("vehicles").select("*").limit(5).execute()
        
        if vehicles_response.data:
            sample_vehicle = vehicles_response.data[0]
            print("✅ Sample Vehicle Fields:")
            for key, value in sample_vehicle.items():
                print(f"   {key}: {value} ({type(value).__name__})")
        else:
            print("⚠️  No vehicles found in the table")
            return
            
        # 2. Check all vehicles with their capacity and current load data
        print(f"\n📋 All Vehicles Data (Total: {len(vehicles_response.data)}):")
        print("-" * 60)
        
        all_vehicles_response = supabase.table("vehicles").select("*").execute()
        
        for i, vehicle in enumerate(all_vehicles_response.data, 1):
            print(f"\n{i}. Vehicle ID: {vehicle.get('id')}")
            print(f"   Plate: {vehicle.get('plate')}")
            print(f"   Type: {vehicle.get('vehicle_type')}")
            print(f"   Capacity KG: {vehicle.get('capacity_kg')}")
            print(f"   Capacity M³: {vehicle.get('capacity_m3')}")
            print(f"   Volume Unit: {vehicle.get('volume_unit')}")
            print(f"   Active: {vehicle.get('active')}")
            print(f"   Tenant ID: {vehicle.get('tenant_id')}")
            print(f"   Depot ID: {vehicle.get('depot_id')}")
        
        # 3. Check stock levels with TRUCK_STOCK status (this is where current load comes from)
        print(f"\n📦 Current Vehicle Loads (TRUCK_STOCK):")
        print("-" * 50)
        
        truck_stock_response = supabase.table("stock_levels").select("*").eq("stock_status", "TRUCK_STOCK").execute()
        
        if truck_stock_response.data:
            print(f"✅ Found {len(truck_stock_response.data)} TRUCK_STOCK entries:")
            for stock in truck_stock_response.data:
                print(f"   Warehouse: {stock.get('warehouse_id')}")
                print(f"   Variant: {stock.get('variant_id')}")
                print(f"   Quantity: {stock.get('quantity')}")
                print(f"   Status: {stock.get('stock_status')}")
                print(f"   Last Updated: {stock.get('last_transaction_date')}")
                print("   ---")
        else:
            print("⚠️  No TRUCK_STOCK entries found")
            
        # 4. Check variants table for weight/volume data
        print(f"\n⚖️  Variants Weight/Volume Data:")
        print("-" * 40)
        
        variants_response = supabase.table("variants").select("*").limit(10).execute()
        
        if variants_response.data:
            print(f"✅ Found {len(variants_response.data)} variants (showing first 10):")
            for variant in variants_response.data:
                weight = variant.get('unit_weight_kg', 'N/A')
                volume = variant.get('unit_volume_m3', 'N/A') 
                print(f"   ID: {variant.get('id')}")
                print(f"   Product: {variant.get('product_id')}")
                print(f"   Weight: {weight} kg")
                print(f"   Volume: {volume} m³")
                print("   ---")
        else:
            print("⚠️  No variants found")
            
        # 5. Calculate theoretical load for any TRUCK_STOCK
        if truck_stock_response.data:
            print(f"\n🧮 Calculated Current Load:")
            print("-" * 30)
            
            total_weight = 0.0
            total_volume = 0.0
            items_calculated = 0
            
            for stock in truck_stock_response.data:
                quantity = float(stock.get('quantity', 0))
                
                # Try to get variant details
                variant_response = supabase.table("variants").select("*").eq("id", stock.get('variant_id')).execute()
                
                if variant_response.data:
                    variant = variant_response.data[0]
                    unit_weight = float(variant.get('unit_weight_kg', 27.0))  # Default fallback
                    unit_volume = float(variant.get('unit_volume_m3', 0.036))  # Default fallback
                else:
                    # Use hardcoded defaults (this is likely the source of identical values!)
                    unit_weight = 27.0
                    unit_volume = 0.036
                    
                item_weight = quantity * unit_weight
                item_volume = quantity * unit_volume
                
                total_weight += item_weight
                total_volume += item_volume
                items_calculated += 1
                
                print(f"   Item {items_calculated}:")
                print(f"     Quantity: {quantity}")
                print(f"     Unit Weight: {unit_weight} kg")
                print(f"     Unit Volume: {unit_volume} m³")
                print(f"     Total Weight: {item_weight} kg")
                print(f"     Total Volume: {item_volume} m³")
            
            print(f"\n📊 TOTAL CALCULATED LOAD:")
            print(f"   Total Weight: {total_weight} kg")
            print(f"   Total Volume: {total_volume} m³")
            
            # Check if this matches the reported values
            if abs(total_weight - 1323.0) < 0.1:
                print(f"   ✅ This matches the reported load of 1323.0 kg!")
            if abs(total_volume - 1.76) < 0.01:
                print(f"   ✅ This matches the reported volume of 1.76 m³!")
                
        print("\n" + "=" * 60)
        print("✅ Database analysis completed!")
            
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())